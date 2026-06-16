"""认证与授权服务。

这层对应 Java 项目里常见的 AuthService / TokenService：
1. 校验用户名密码
2. 生成 JWT
3. 管理 refresh token 会话
4. 构建当前请求的权限上下文
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from server.core.config import get_settings
from server.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from server.db.models import Role, Session as UserSession, User
from server.schemas.common import AuthContext


class AuthService:
    """认证服务。"""

    def __init__(self) -> None:
        self.settings = get_settings()

    def build_auth_context(self, user: User) -> AuthContext:
        """把数据库用户对象转换成运行时权限上下文。

        后续 LangGraph 和业务服务都不直接依赖 ORM User，
        而是依赖这个更轻量的 AuthContext。
        """
        roles = [role.name for role in user.roles]
        permissions = sorted(
            {
                permission.name
                for role in user.roles
                for permission in role.permissions
            }
        )
        return AuthContext(
            user_id=user.id,
            username=user.username,
            account_code=user.account_code,
            location=user.location,
            roles=roles,
            permissions=permissions,
        )

    def authenticate(self, db: Session, username: str, password: str) -> tuple[User, AuthContext]:
        """登录时校验用户名密码。"""
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.username == username)
        )
        user = db.scalar(stmt)
        if user is None or not verify_password(password, user.password_hash) or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user, self.build_auth_context(user)

    def login(self, db: Session, username: str, password: str) -> dict:
        """登录并签发 access token / refresh token。"""
        user, auth_context = self.authenticate(db, username, password)
        session = UserSession(
            user_id=user.id,
            refresh_token_hash="pending",
            expires_at=datetime.now(UTC) + timedelta(minutes=self.settings.refresh_token_expire_minutes),
        )
        db.add(session)
        db.flush()

        refresh_token = create_refresh_token(str(user.id), str(session.id))
        session.refresh_token_hash = hash_refresh_token(refresh_token)
        db.commit()

        access_token = create_access_token(str(user.id), {"username": user.username})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.settings.access_token_expire_minutes * 60,
            "user": auth_context,
        }

    def refresh(self, db: Session, refresh_token: str) -> dict:
        """根据 refresh token 刷新 access token。"""
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        session_id = payload.get("sid")
        if not session_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session")

        stmt = (
            select(UserSession)
            .options(
                selectinload(UserSession.user)
                .selectinload(User.roles)
                .selectinload(Role.permissions)
            )
            .where(UserSession.id == UUID(session_id))
        )
        session = db.scalar(stmt)
        if (
            session is None
            or session.refresh_token_hash != hash_refresh_token(refresh_token)
            or session.revoked_at is not None
            or session.expires_at < datetime.now(UTC)
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        user = session.user
        auth_context = self.build_auth_context(user)
        access_token = create_access_token(str(user.id), {"username": user.username})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.settings.access_token_expire_minutes * 60,
            "user": auth_context,
        }

    def get_user_from_access_token(self, db: Session, access_token: str) -> tuple[User, AuthContext]:
        """解析 access token，并回库补齐角色和权限。"""
        payload = decode_token(access_token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing subject")
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == UUID(subject))
        )
        user = db.scalar(stmt)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user, self.build_auth_context(user)

    def ensure_password(self, db: Session, username: str, password: str) -> None:
        """兼容旧账号时，必要时重写密码哈希。"""
        user = db.scalar(select(User).where(User.username == username))
        if user and not user.password_hash.startswith("$2"):
            user.password_hash = hash_password(password)
            db.commit()


auth_service = AuthService()
