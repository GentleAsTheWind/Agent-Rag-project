"""FastAPI 服务入口。

这个文件相当于 Java Web 项目里的 Application + WebConfig：
1. 创建 FastAPI 应用
2. 注册中间件
3. 注册路由
4. 在启动阶段完成数据库自举和知识库导入
"""

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
    """应用生命周期钩子。

    这里的职责类似 Java 项目启动时执行的 CommandLineRunner：
    - 自动建表/灌初始化数据
    - 首次启动时把 data/ 下的知识文件切片并写入 pgvector
    """
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
    """统一兜底异常处理。

    生产环境里不把 Python 堆栈直接暴露给前端，只返回 request_id，
    方便后续查日志定位问题。
    """
    request_id = getattr(request.state, "request_id", "-")
    logger.exception("unhandled exception", extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "request_id": request_id,
        },
    )
