
"""RAG 问答服务：检索领域资料，将问题和资料上下文交给模型生成受约束的回答。"""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts
from langchain_core.prompts import PromptTemplate
from model.factory import chat_model


def print_prompt(prompt):
    # 调试辅助函数：输出最终 Prompt，便于检查资料是否被正确拼入上下文。
    print("="*20)
    print(prompt.to_string())
    print("="*20)
    return prompt


class RagSummarizeService(object):
    # 初始化向量库检索器、RAG Prompt、聊天模型和 LCEL 执行链。
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        # Prompt → 调试输出 → 大模型 → 字符串解析，避免调用方处理 AIMessage 对象。
        chain = self.prompt_template | print_prompt | self.model | StrOutputParser()
        return chain

    def retriever_docs(self, query: str) -> list[Document]:
        # 根据用户问题执行向量相似度检索，返回 Top-K 文档分块。
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        # 首先只召回相关片段，不把整个知识库塞进模型上下文。
        context_docs = self.retriever_docs(query)

        # 按序号组织资料正文与元数据，便于 Prompt 要求模型基于资料作答。
        context = ""
        counter = 0
        for doc in context_docs:
            counter += 1
            context += f"【参考资料{counter}】: 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}\n"

        # 将原始问题和已召回上下文传入链，得到最终文本回答。
        return self.chain.invoke(
            {
                "input": query,
                "context": context,
            }
        )


if __name__ == '__main__':
    rag = RagSummarizeService()

    print(rag.rag_summarize("小户型适合哪些扫地机器人"))
