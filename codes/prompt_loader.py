from codes.config_handler import prompts_conf
from codes.path_tool import get_abs_path
from codes.logger_handler import logger


def _load_prompt(config_key: str, caller_name: str) -> str:
    """
    通用的提示词加载函数，从yaml配置中读取路径并加载文件内容
    :param config_key: yaml配置中的键名
    :param caller_name: 调用方名称，用于日志
    :return: 提示词文本内容
    """
    try:
        prompt_path = get_abs_path(prompts_conf[config_key])
    except KeyError:
        logger.error(f"[{caller_name}]在yaml配置项中没有{config_key}配置项")
        raise

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[{caller_name}]加载提示词文件失败: {prompt_path}，原因: {e}")
        raise


def load_system_prompts() -> str:
    return _load_prompt("main_prompt_path", "load_system_prompts")


def load_rag_prompts() -> str:
    return _load_prompt("rag_summarize_prompt_path", "load_rag_prompts")


def load_report_prompts() -> str:
    return _load_prompt("report_prompt_path", "load_report_prompts")


if __name__ == '__main__':
    print(load_system_prompts())
