from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.api.deps import get_current_auth_context, require_permission
from server.db.session import get_db
from server.schemas.common import AuthContext
from server.schemas.knowledge import KnowledgeIngestRequest, KnowledgeIngestResponse
from server.services.ingestion import ingestion_service


router = APIRouter(tags=["knowledge"])


@router.post("/knowledge/ingest", response_model=KnowledgeIngestResponse)
def ingest_knowledge(
    payload: KnowledgeIngestRequest,
    auth_context: AuthContext = Depends(require_permission("admin:knowledge:write")),
    db: Session = Depends(get_db),
) -> KnowledgeIngestResponse:
    stats = ingestion_service.ingest(db, payload.path, payload.category, payload.tags)
    return KnowledgeIngestResponse(status="completed", **stats)
