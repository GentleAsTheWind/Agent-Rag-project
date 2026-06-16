from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.api.deps import get_current_auth_context
from server.db.models import ConversationMessage, ConversationThread
from server.db.session import get_db
from server.schemas.common import AuthContext, ConversationMessageOut


router = APIRouter(tags=["conversations"])


@router.get("/conversations/{thread_id}", response_model=list[ConversationMessageOut])
def get_conversation(
    thread_id: UUID,
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db),
) -> list[ConversationMessageOut]:
    thread = db.scalar(
        select(ConversationThread).where(
            ConversationThread.id == thread_id,
            ConversationThread.user_id == auth_context.user_id,
        )
    )
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = db.scalars(
        select(ConversationMessage).where(ConversationMessage.thread_id == thread_id).order_by(ConversationMessage.created_at.asc())
    ).all()
    return [ConversationMessageOut.model_validate(message, from_attributes=True) for message in messages]
