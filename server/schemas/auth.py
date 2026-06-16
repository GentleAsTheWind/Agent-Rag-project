from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from server.schemas.common import AuthContext


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthContext


class SessionOut(BaseModel):
    id: UUID
    expires_at: datetime
