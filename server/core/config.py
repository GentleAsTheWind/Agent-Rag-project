"""全局配置中心。

对于 Java 背景，可以把它理解成：
- Spring Boot 的 @ConfigurationProperties
- 所有环境变量/默认值的统一入口
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """项目运行配置。

    这里把“数据库、JWT、模型、RAG 参数、数据目录”集中定义，
    避免这些参数散落在各个模块里。
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Agent-RAG Production API"
    environment: str = "local"
    api_prefix: str = ""
    debug: bool = False

    database_url: str = "postgresql+psycopg://agent_app:AgentApp!2026@127.0.0.1:5432/agent_rag"

    jwt_secret_key: str = "replace-this-local-dev-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7

    chat_model_name: str = "qwen3-max"
    fallback_chat_model_name: str = "qwen-plus"
    routing_model_name: str = "qwen-turbo"
    embedding_model_name: str = "text-embedding-v4"
    embedding_dimensions: int = 1024
    dashscope_api_key: str | None = Field(default=None, alias="AI_DASHSCOPE_API_KEY")

    auto_bootstrap: bool = True
    auto_ingest_sample_knowledge: bool = True
    data_path: str = str(PROJECT_ROOT / "data")
    knowledge_glob: tuple[str, ...] = ("*.txt", "*.pdf")
    report_csv_path: str = str(PROJECT_ROOT / "data" / "external" / "records.csv")

    rag_top_k: int = 6
    rag_score_threshold: float = 0.42
    rerank_top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 80

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    streamlit_api_base_url: str = "http://127.0.0.1:8000"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回全局单例配置。

    配置通常在一个进程内只需要解析一次，因此这里做缓存。
    """
    return Settings()
