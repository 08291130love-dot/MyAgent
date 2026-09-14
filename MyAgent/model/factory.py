from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_community.chat_models.tongyi import BaseChatModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from utils.config_handler import rag_conf
from model.qwen38_chat import Qwen38ChatModel


class BaseModelFactory(ABC):
    # 抽象工厂接口：统一聊天模型与 Embedding 模型的创建方式。
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    # 从 rag.yml 读取模型名并创建通义千问聊天模型实例。
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        if rag_conf["chat_model_name"] == "qwen3.8-max":
            return Qwen38ChatModel(model_name="qwen3.8-max")
        return ChatTongyi(model=rag_conf["chat_model_name"])


class EmbeddingsFactory(BaseModelFactory):
    # 从 rag.yml 读取模型名并创建文本向量化模型实例。
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])


# 供 Agent/RAG 模块复用的全局聊天模型。
chat_model = ChatModelFactory().generator()
# 供 Chroma 写入和检索使用的全局 Embedding 模型。
embed_model = EmbeddingsFactory().generator()
