import hashlib
import math
import re
from typing import Any

from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings

from server.core.config import get_settings


class ModelManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._routing_model = None
        self._chat_model = None
        self._fallback_chat_model = None
        self._embedding_model = None

    @property
    def available(self) -> bool:
        return bool(self.settings.dashscope_api_key)

    def get_routing_model(self):
        if not self.available:
            return None
        if self._routing_model is None:
            self._routing_model = ChatTongyi(
                model=self.settings.routing_model_name,
                api_key=self.settings.dashscope_api_key,
                timeout=20,
            )
        return self._routing_model

    def get_chat_model(self):
        if not self.available:
            return None
        if self._chat_model is None:
            self._chat_model = ChatTongyi(
                model=self.settings.chat_model_name,
                api_key=self.settings.dashscope_api_key,
                timeout=30,
            )
        return self._chat_model

    def get_fallback_chat_model(self):
        if not self.available:
            return None
        if self._fallback_chat_model is None:
            self._fallback_chat_model = ChatTongyi(
                model=self.settings.fallback_chat_model_name,
                api_key=self.settings.dashscope_api_key,
                timeout=30,
            )
        return self._fallback_chat_model

    def get_embedding_model(self):
        if not self.available:
            return None
        if self._embedding_model is None:
            self._embedding_model = DashScopeEmbeddings(
                model=self.settings.embedding_model_name,
                dashscope_api_key=self.settings.dashscope_api_key,
            )
        return self._embedding_model

    def embed_text(self, text: str) -> list[float]:
        model = self.get_embedding_model()
        if model is not None:
            return model.embed_query(text)
        return self._local_embedding(text)

    def _local_embedding(self, text: str) -> list[float]:
        dims = self.settings.embedding_dimensions
        tokens = re.findall(r"[\u4e00-\u9fff]|\w+", text.lower())
        vector = [0.0] * dims
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dims
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def invoke_chat(self, prompt: str) -> str | None:
        model = self.get_chat_model()
        if model is None:
            return None
        try:
            response = model.invoke(prompt)
            return getattr(response, "content", None) or str(response)
        except Exception:
            fallback = self.get_fallback_chat_model()
            if fallback is None:
                return None
            response = fallback.invoke(prompt)
            return getattr(response, "content", None) or str(response)


model_manager = ModelManager()
