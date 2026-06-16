from typing import Any, TypedDict
from uuid import UUID

from sqlalchemy.orm import Session

from server.schemas.common import AuthContext, Citation, IntentResult


class WorkflowState(TypedDict, total=False):
    db: Session
    auth_context: AuthContext
    user_message: str
    thread_id: UUID | None
    client_context: dict[str, Any]
    intent_result: IntentResult
    route_after_policy: str
    report_payload: dict[str, Any]
    retrieved_docs: list[dict[str, Any]]
    final_answer: str
    citations: list[Citation]
    decision_log: list[str]
