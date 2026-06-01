from typing import Callable

from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from langchain_community.utilities.pebblo import Runtime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from codes.logger_handler import logger


# Deleted:from codes.prompt_loader import load_report_prompts, load_system_prompts


@wrap_tool_call
def monitor_tool(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    logger.info(f"[tool monitor]执行工具: {request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数: {request.tool_call['args']}")

    try:
        result = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")

        if request.tool_call["name"] == "fill_context_for_report":
            if request.runtime is not None:
                print("sdkfjdkf")
                if request.runtime.context is None:
                    print("fkdsjk")
                    request.runtime.context = {}
                request.runtime.context["report"] = True
        return result
    except Exception as e:
        logger.error(f"工具{request.tool_call['name']}调用失败，原因: {str(e)}")
        raise e


@before_model
def log_before_model(
        state: AgentState,
        # Deleted:        # 整个Agent智能体中的状态记录
        runtime: Runtime,
        # Deleted:        # 记录了整个执行过程中的上下文信息
):
    # Deleted:    # 在模型执行前输出日志
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息。")

    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content}")

    return None


@dynamic_prompt
def report_prompt_switch(request: ModelRequest):
    from codes.prompt_loader import load_report_prompts, load_system_prompts

    if request.runtime is None or request.runtime.context is None:
        return load_system_prompts()

    is_report = request.runtime.context.get("report", False)
    if is_report:
        print("******" * 20)
        return load_report_prompts()

    return load_system_prompts()
