import os
import yaml

from codes.path_tool import get_abs_path


def load_yaml_config(config_path: str, encoding: str = "utf-8") -> dict:
    """
    通用的YAML配置文件加载函数
    :param config_path: 配置文件的绝对路径
    :param encoding: 文件编码
    :return: 解析后的配置字典
    """
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_rag_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = get_abs_path("config/rag.yml")
    return load_yaml_config(config_path)


def load_chroma_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = get_abs_path("config/chroma.yml")
    return load_yaml_config(config_path)


def load_prompts_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = get_abs_path("config/prompts.yml")
    return load_yaml_config(config_path)


def load_agent_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = get_abs_path("config/agent.yml")
    config = load_yaml_config(config_path)

    # 强制从环境变量读取 API Key，生产环境不应将密钥写在配置文件中
    api_key = os.getenv("AI_DASHSCOPE_API_KEY")
    if api_key:
        config["api_key"] = api_key
    else:
        import warnings
        warnings.warn(
            "环境变量 AI_DASHSCOPE_API_KEY 未设置，将使用配置文件中的 api_key。"
            "生产环境请务必通过环境变量注入 API Key。",
            UserWarning,
            stacklevel=2,
        )

    return config


rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()

if __name__ == '__main__':
    print(agent_conf.get("api_key", "未配置"))
