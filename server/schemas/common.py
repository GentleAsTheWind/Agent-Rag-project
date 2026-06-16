from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: UUID
    chunk_id: UUID
    source: str
    category: str


class AuthContext(BaseModel):
    user_id: UUID
    username: str
    account_code: str | None = None
    location: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class IntentResult(BaseModel):
    intent: str
    confidence: float
    required_entities: list[str] = Field(default_factory=list)
    needs_auth: bool = False
    risk_level: str = "low"
    resolved_month: str | None = None
    target_account_code: str | None = None


class ApiMessage(BaseModel):
    message: str
    detail: dict[str, Any] | None = None


class ConversationMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    intent: str | None = None
    citations: list[dict[str, Any]] | None = None
    created_at: datetime
