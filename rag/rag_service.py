from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from codes.prompt_loader import load_rag_prompts
from model.factory import chat_model
from rag.vector_store import VectorStoreService
from agent.tools.middleware import log_before_model


def print_prompt(prompt):
    print("----" * 20)
    print(prompt.to_string())
    print("----" * 20)
    return prompt


class RagSummaryService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._intit_chain()

    def _intit_chain(self):
        chain = self.prompt_template |print_prompt | self.model | StrOutputParser()
        return chain

    def retriver_docs(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)



    def generate_summary(self, query: str) -> str:
        docs: list[Document] = self.retriver_docs(query)
        context = ""
        count = 0
        for doc in docs:
            count += 1
            context += f"【参考资料{count}】:{doc.page_content}|参考元数据:{doc.metadata}"

        return self.chain.invoke({
            "input": query,
            "context": context,
        })


if __name__ == '__main__':
    rag_service = RagSummaryService()
    print(rag_service.generate_summary("小户型适合哪种扫地机器人"))
