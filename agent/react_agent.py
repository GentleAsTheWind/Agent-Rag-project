from typing import Optional

from agent.tools.agent_tools import rag_summarize, get_weather, get_user_location, get_user_id, get_current_month, \
    fetch_external_data, fill_context_for_report
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from codes.prompt_loader import load_system_prompts
from model.factory import chat_model
from langchain.agents import create_agent
from codes.logger_handler import logger


class ReactAgent:
    def __init__(self):
        system_prompt = load_system_prompts()

        self.agent = create_agent(
            model=chat_model,
            tools=[
                rag_summarize,
                get_weather,
                get_user_location,
                get_user_id,
                get_current_month,
                fetch_external_data,
                fill_context_for_report,
            ],
            system_prompt=system_prompt,
            middleware=[
                monitor_tool,
                log_before_model,
                report_prompt_switch,
            ],
        )

    def execute_stream(self, query: str, history: Optional[list[dict]] = None):
        """
        执行Agent流式响应
        :param query: 当前用户输入
        :param history: 对话历史列表，格式为 [{"role": "user"/"assistant", "content": "..."}]
        """
        messages = []

        # 加入历史对话，支持多轮对话上下文
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # 加入当前用户输入
        messages.append({"role": "user", "content": query})

        input_dict = {"messages": messages}

        # 第三个参数context就是上下文runtime中的信息，就是我们做提示词切换的标记
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("生成使用报告"):
        print(chunk)
