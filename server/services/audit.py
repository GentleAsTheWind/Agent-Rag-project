from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from server.db.models import ToolAuditLog


class AuditService:
    def log(
        self,
        db: Session,
        action: str,
        status: str = "success",
        detail: dict[str, Any] | None = None,
        user_id: UUID | None = None,
        thread_id: UUID | None = None,
    ) -> None:
        record = ToolAuditLog(
            action=action,
            status=status,
            detail=detail or {},
            user_id=user_id,
            thread_id=thread_id,
        )
        db.add(record)
        db.commit()


audit_service = AuditService()
