import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from server.api.routes import auth, chat, conversations, health, knowledge, reports
from server.core.config import get_settings
from server.core.logging import RequestIdFilter, configure_logging
from server.core.middleware import RequestContextMiddleware
from server.db.bootstrap import bootstrapper
from server.db.session import SessionLocal
from server.services.ingestion import ingestion_service


configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)
logger.addFilter(RequestIdFilter())


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.auto_bootstrap:
        bootstrapper.bootstrap()
    with SessionLocal() as db:
        if settings.auto_ingest_sample_knowledge and not ingestion_service.has_knowledge(db):
            logger.info("ingesting sample knowledge", extra={"request_id": "startup"})
            ingestion_service.ingest(db)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(health.router)
app.include_router(knowledge.router)
app.include_router(reports.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    logger.exception("unhandled exception", extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "request_id": request_id,
        },
    )
