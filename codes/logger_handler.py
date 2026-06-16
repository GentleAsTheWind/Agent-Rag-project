import logging
import os
from logging.handlers import RotatingFileHandler

from codes.path_tool import get_abs_path

# 日志保存的根目录
LOG_ROOT = get_abs_path("logs")

# 确保日志的目录存在
os.makedirs(LOG_ROOT, exist_ok=True)

# 日志的格式配置
DEFAULT_LOG_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


def get_logger(
        name: str = "agent",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file: str = None,
        max_bytes: int = 10 * 1024 * 1024,  # 单个日志文件最大 10MB
        backup_count: int = 5,  # 保留 5 个历史日志文件
) -> logging.Logger:
    """
    获取配置好的Logger实例
    :param name: logger名称
    :param console_level: 控制台日志级别
    :param file_level: 文件日志级别
    :param log_file: 日志文件路径（默认按名称生成）
    :param max_bytes: 单个日志文件最大字节数
    :param backup_count: 保留的历史日志文件数量
    :return: 配置好的Logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加Handler
    if logger.handlers:
        return logger

    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handler)

    # 文件handler（带轮转）
    if not log_file:
        log_file = os.path.join(LOG_ROOT, f"{name}.log")

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)

    return logger


logger = get_logger()

if __name__ == '__main__':
    logger.info("hello world")
