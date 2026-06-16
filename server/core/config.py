from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
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
    return Settings()
