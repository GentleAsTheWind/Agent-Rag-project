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


chat_model = ChatModelFactory().generate()
embeddings_model = EmbeddingsFactory().generate()

