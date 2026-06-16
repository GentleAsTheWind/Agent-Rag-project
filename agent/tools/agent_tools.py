import os
import threading
from datetime import datetime

from langchain_core.tools import tool

from codes.config_handler import agent_conf
from codes.logger_handler import logger
from codes.path_tool import get_abs_path
from codes.file_handler import load_csv_as_dict

# 延迟初始化 RAG 服务，避免模块导入时就创建实例
_rag_service = None
_rag_lock = threading.Lock()


def _get_rag_service():
    global _rag_service
    if _rag_service is None:
        with _rag_lock:
            if _rag_service is None:
                from rag.rag_service import RagSummaryService
                _rag_service = RagSummaryService()
    return _rag_service


# 外部数据缓存，线程安全
_external_data = None
_external_data_lock = threading.Lock()


def _get_external_data() -> dict:
    """延迟加载外部数据，线程安全"""
    global _external_data
    if _external_data is None:
        with _external_data_lock:
            if _external_data is None:
                external_data_path = get_abs_path(agent_conf["external_data_path"])
                if not os.path.exists(external_data_path):
                    logger.error(f"[外部数据]文件不存在: {external_data_path}")
                    _external_data = {}
                    return _external_data
                _external_data = load_csv_as_dict(external_data_path)
                logger.info(f"[外部数据]成功加载 {len(_external_data)} 个用户的使用记录")
    return _external_data


@tool(description="从向量库存储中检索资料")
def rag_summarize(query: str) -> str:
    return _get_rag_service().generate_summary(query)


@tool(description="获取天气信息")
def get_weather(city: str) -> str:
    return f"城市{city}的天气是晴天,温度23度,降水概率0.1"


@tool(description="获取用户位置")
def get_user_location() -> str:
    return "上海"


@tool(description="获取用户id")
def get_user_id() -> str:
    return "用户id为1001,用户名字为王吱呲"


@tool(description="获取当前月份")
def get_current_month() -> str:
    return datetime.now().strftime("%Y年%m月")


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回，如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    data = _get_external_data()
    try:
        return str(data[user_id][month])
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""


@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"


if __name__ == '__main__':
    print(fetch_external_data.invoke({"user_id": "1001", "month": "2025-01"}))
