"""聊天 API。"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from server.api.deps import enforce_rate_limit, get_current_auth_context
from server.db.session import get_db
from server.schemas.chat import ChatRequest, ChatResponse
from server.schemas.common import AuthContext
from server.services.chat import chat_service


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(enforce_rate_limit)])
def chat(
    payload: ChatRequest,
    request: Request,
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """统一聊天入口。

    不管是 FAQ 还是报告，都会先从这个入口进入，
    后续由 LangGraph 决定具体走哪条业务链。
    """
    payload.client_context.setdefault("request_id", getattr(request.state, "request_id", "-"))
    return chat_service.handle_chat(db, auth_context, payload.message, payload.thread_id, payload.client_context)
