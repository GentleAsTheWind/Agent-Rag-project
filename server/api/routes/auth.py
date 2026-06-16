"""认证相关 API。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.api.deps import get_current_auth_context
from server.db.session import get_db
from server.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from server.schemas.common import AuthContext
from server.services.auth import auth_service


router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    """用户名密码登录。"""
    return TokenPair(**auth_service.login(db, payload.username, payload.password))


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    """刷新 access token。"""
    return TokenPair(**auth_service.refresh(db, payload.refresh_token))


@router.get("/me", response_model=AuthContext)
def me(auth_context: AuthContext = Depends(get_current_auth_context)) -> AuthContext:
    """返回当前登录用户的身份与权限信息。"""
    return auth_context
