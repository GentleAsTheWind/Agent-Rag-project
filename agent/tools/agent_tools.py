import os

from langchain_core.tools import tool

from codes.config_handler import agent_conf
from codes.logger_handler import logger
from codes.path_tool import get_abs_path
from rag.rag_service import RagSummaryService

rag = RagSummaryService()

external_data = {}


@tool(description="从向量库村存储中检索资料")
def rag_summarize(query: str) -> str:
    return rag.generate_summary(query)


@tool(description="获取天气信息")
def ger_weather(city: str) -> str:
    return f"城市{city}的天气是晴天,温度23度,降水概率0.1"


@tool(description="获取用户位置")
def ger_user_location() -> str:
    return "上海"


@tool(description="获取用户id")
def ger_user_id() -> str:
    return "用户id为1001,用户名字为王吱呲"


@tool(description="获取当前月份")
def get_current_month() -> str:
    return "2025年1月"


def generate_external_data():
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            print(f"外部数据文件不存在: {external_data_path}")

        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr: list[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                        "feature": feature,
                        "efficiency": efficiency,
                        "consumables": consumables,
                        "comparison": comparison,
                    }


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回，如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""

@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"


if __name__ == '__main__':
    print(fetch_external_data.invoke({"user_id": "1001", "month": "2026-05"}))
