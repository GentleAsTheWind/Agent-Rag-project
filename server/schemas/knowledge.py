from pydantic import BaseModel, Field


class KnowledgeIngestRequest(BaseModel):
    path: str | None = None
    category: str = "general"
    tags: list[str] = Field(default_factory=list)


class KnowledgeIngestResponse(BaseModel):
    status: str
    documents_ingested: int
    chunks_ingested: int
    skipped_documents: int
