import csv
from pathlib import Path
from typing import Iterable

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.core.config import get_settings
from server.db.models import IngestionJob, KnowledgeChunk, KnowledgeDocument
from server.llm.factory import model_manager
from server.services.rag import rag_service


class IngestionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ","],
        )

    def ingest(self, db: Session, path: str | None = None, category: str = "general", tags: list[str] | None = None) -> dict:
        target = Path(path or self.settings.data_path)
        tags = tags or []

        job = IngestionJob(source_path=str(target), status="running", stats={})
        db.add(job)
        db.commit()
        db.refresh(job)

        documents_ingested = 0
        chunks_ingested = 0
        skipped_documents = 0

        try:
            for file_path in self._iter_source_files(target):
                raw_text = self._read_text(file_path)
                if not raw_text.strip():
                    skipped_documents += 1
                    continue

                document_hash = rag_service.compute_hash(raw_text)
                existing = db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.document_hash == document_hash))
                if existing:
                    skipped_documents += 1
                    continue

                document = KnowledgeDocument(
                    source_path=str(file_path),
                    source=file_path.name,
                    doc_type=file_path.suffix.lstrip(".").lower(),
                    category=category,
                    tags=tags,
                    document_hash=document_hash,
                )
                db.add(document)
                db.flush()

                documents_ingested += 1
                texts = self.splitter.split_text(raw_text)
                for index, chunk_text in enumerate(texts):
                    sanitized = rag_service.sanitize_content(chunk_text)
                    chunk_hash = rag_service.compute_hash(f"{document_hash}:{index}:{sanitized}")
                    metadata = {
                        "suspicious_patterns": rag_service.detect_prompt_injection(chunk_text),
                        "source_path": str(file_path),
                    }
                    chunk = KnowledgeChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=chunk_text,
                        sanitized_content=sanitized,
                        chunk_hash=chunk_hash,
                        source=file_path.name,
                        doc_type=file_path.suffix.lstrip(".").lower(),
                        category=category,
                        tags=tags,
                        chunk_metadata=metadata,
                        embedding=model_manager.embed_text(sanitized),
                    )
                    db.add(chunk)
                    chunks_ingested += 1

                db.commit()

            job.status = "completed"
            job.stats = {
                "documents_ingested": documents_ingested,
                "chunks_ingested": chunks_ingested,
                "skipped_documents": skipped_documents,
            }
            db.commit()
            return job.stats
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error = str(exc)
            db.add(job)
            db.commit()
            raise

    def has_knowledge(self, db: Session) -> bool:
        return db.scalar(select(KnowledgeChunk.id).limit(1)) is not None

    def _iter_source_files(self, target: Path) -> Iterable[Path]:
        if target.is_file():
            yield target
            return
        for pattern in self.settings.knowledge_glob:
            yield from target.rglob(pattern)

    def _read_text(self, file_path: Path) -> str:
        if file_path.suffix.lower() == ".txt":
            return file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() == ".pdf":
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return ""


ingestion_service = IngestionService()
