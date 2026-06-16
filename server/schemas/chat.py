from uuid import UUID

from pydantic import BaseModel, Field

from server.schemas.common import Citation


class ChatRequest(BaseModel):
    thread_id: UUID | None = None
    message: str
    stream: bool = False
    client_context: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    thread_id: UUID
    answer: str
    intent: str
    confidence: float
    citations: list[Citation] = Field(default_factory=list)
