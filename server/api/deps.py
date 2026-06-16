"""FastAPI 依赖注入层。

类似 Java/Spring 里的拦截器 + 参数解析：
1. 取当前登录用户
2. 做接口级权限校验
3. 做简单限流
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from server.core.config import get_settings
from server.core.rate_limit import InMemoryRateLimiter
from server.db.session import get_db
from server.schemas.common import AuthContext
from server.services.auth import auth_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
settings = get_settings()
rate_limiter = InMemoryRateLimiter(
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


def get_request_id(request: Request) -> str:
    """从请求上下文里拿 request_id。"""
    return getattr(request.state, "request_id", "-")


def enforce_rate_limit(request: Request) -> None:
    """按 IP + 路径做进程内限流。"""
    client_host = request.client.host if request.client else "unknown"
    rate_limiter.check(f"{client_host}:{request.url.path}")


def get_current_auth_context(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    """把 Bearer Token 解析成当前请求的认证上下文。"""
    _user, auth_context = auth_service.get_user_from_access_token(db, token)
    return auth_context


def require_permission(permission: str):
    """声明式权限校验工厂。

    用法上类似：
    - require_permission("admin:knowledge:write")
    """
    def checker(auth_context: AuthContext = Depends(get_current_auth_context)) -> AuthContext:
        if permission not in auth_context.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return auth_context

    return checker
