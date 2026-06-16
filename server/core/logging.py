import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from server.core.config import PROJECT_ROOT


def configure_logging() -> None:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if root.handlers:
        return

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        log_dir / "production-api.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


class RequestIdFilter(logging.Filter):
    def __init__(self, request_id: str = "-"):
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = self.request_id
        return True
