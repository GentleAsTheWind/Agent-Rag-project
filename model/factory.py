from abc import abstractmethod, ABC
from typing import Optional, Union

from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.language_models import BaseChatModel
from openai.types import EmbeddingModel
from codes.config_handler import agent_conf


class BaseModelFactory(ABC):
    @abstractmethod
    def generate(self) -> Optional[Union[EmbeddingModel, BaseChatModel]]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generate(self) -> BaseChatModel:
        return ChatTongyi(model=agent_conf["chat_model_name"], api_key=agent_conf["api_key"])


class EmbeddingsFactory(BaseModelFactory):
    def generate(self):
        return DashScopeEmbeddings(model=agent_conf["embedding_model_name"], dashscope_api_key=agent_conf["api_key"])


# 延迟初始化：模块导入时不创建模型实例，首次使用时才初始化
_chat_model = None
_embeddings_model = None


def get_chat_model() -> BaseChatModel:
    """获取聊天模型单例（延迟初始化）"""
    global _chat_model
    if _chat_model is None:
        _chat_model = ChatModelFactory().generate()
    return _chat_model


def get_embeddings_model():
    """获取嵌入模型单例（延迟初始化）"""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = EmbeddingsFactory().generate()
    return _embeddings_model


# 保持向后兼容的属性访问
class _LazyModelProxy:
    """代理类，支持向后兼容的模块级属性访问"""

    def __init__(self, getter):
        self._getter = getter
        self._instance = None

    def _ensure_initialized(self):
        if self._instance is None:
            self._instance = self._getter()
        return self._instance

    def __getattr__(self, name):
        return getattr(self._ensure_initialized(), name)

    def __repr__(self):
        return repr(self._ensure_initialized())


chat_model = _LazyModelProxy(get_chat_model)
embeddings_model = _LazyModelProxy(get_embeddings_model)
