from agent.tools.agent_tools import rag_summarize, ger_weather, ger_user_location, ger_user_id, get_current_month, \
    fetch_external_data, fill_context_for_report
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from codes.prompt_loader import load_system_prompts
from model.factory import chat_model
from langchain.agents import create_agent


class ReactAgent:
    def __init__(self):
        system_prompt = load_system_prompts()

        self.agent = create_agent(
            model=chat_model,
            tools=[
                rag_summarize,
                ger_weather,
                ger_user_location,
                ger_user_id,
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

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

    # 第三个参数context就是上下文runtime中的信息，就是我们做提示词切换的标记
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("生成使用报告"):
        print(chunk)
