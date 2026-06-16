"""对话服务。

这是 chat 接口真正的业务入口：
1. 确认/创建 thread
2. 保存用户消息
3. 调用 LangGraph 工作流
4. 保存助手回复
5. 返回结构化响应
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db.models import ConversationMessage, ConversationThread
from server.graph.workflow import workflow_engine
from server.schemas.chat import ChatResponse
from server.schemas.common import AuthContext


class ChatService:
    """聊天主服务。"""

    def _ensure_thread(self, db: Session, auth_context: AuthContext, thread_id: UUID | None, title_hint: str) -> ConversationThread:
        """查找已有会话，或者新建一个对话线程。"""
        if thread_id is not None:
            thread = db.scalar(
                select(ConversationThread).where(
                    ConversationThread.id == thread_id,
                    ConversationThread.user_id == auth_context.user_id,
                )
            )
            if thread is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            return thread

        thread = ConversationThread(user_id=auth_context.user_id, title=title_hint[:48] or "新会话")
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread

    def handle_chat(
        self,
        db: Session,
        auth_context: AuthContext,
        message: str,
        thread_id: UUID | None,
        client_context: dict | None,
    ) -> ChatResponse:
        """处理一次完整聊天请求。"""
        thread = self._ensure_thread(db, auth_context, thread_id, message)
        db.add(ConversationMessage(thread_id=thread.id, role="user", content=message))
        db.commit()

        state = workflow_engine.invoke(
            {
                "db": db,
                "auth_context": auth_context,
                "user_message": message,
                "thread_id": thread.id,
                "client_context": client_context or {},
                "decision_log": [],
            }
        )

        intent_result = state["intent_result"]
        final_answer = state["final_answer"]
        citations = state.get("citations", [])

        db.add(
            ConversationMessage(
                thread_id=thread.id,
                role="assistant",
                content=final_answer,
                intent=intent_result.intent,
                citations=[citation.model_dump(mode="json") for citation in citations],
            )
        )
        db.commit()

        return ChatResponse(
            thread_id=thread.id,
            answer=final_answer,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            citations=citations,
        )


chat_service = ChatService()
