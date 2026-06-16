from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from server.db.session import get_db


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
    return {"status": "ready"}
