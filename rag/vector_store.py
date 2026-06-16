import os.path

from codes.config_handler import chroma_conf
from langchain_community.vectorstores import Chroma

from langchain_core.documents import Document
from codes.logger_handler import logger
from codes.path_tool import get_abs_path
from model.factory import embeddings_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from codes.file_handler import txt_loader, pdf_loader, listdir_with_allowed_type, get_file_md5_hex


class VectorStoreService:
    def __init__(self):
        persist_dir = get_abs_path(chroma_conf["persist_directory"])
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embeddings_model,
            persist_directory=persist_dir,
        )

        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chroma_conf["chunk_size"],
                                                       chunk_overlap=chroma_conf["chunk_overlap"],
                                                       separators=chroma_conf["separator"],
                                                       length_function=len)

    # 获取向量检索器，as_retriever加入到chain中
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    def load_document(self):
        """
        从数据文件夹内读取数据文件，转为向量存入向量库
        要计算文件的MD5做去重
        :return: None
        """

        def check_md5_hex(md5_for_check: str):
            md5_store_path = get_abs_path(chroma_conf["md5_hex_store"])
            if not os.path.exists(md5_store_path):
                # 创建文件
                with open(md5_store_path, "w", encoding="utf-8") as f:
                    pass
                return False  # md5 没处理过

            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True  # md5 处理过

                return False  # md5 没处理过

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str):
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            if read_path.endswith("pdf"):
                return pdf_loader(read_path)

            return []

        allowed_files_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )

        for path in allowed_files_path:
            # 获取文件的MD5
            md5_hex = get_file_md5_hex(path)

            if not md5_hex:
                logger.warning(f"[加载知识库]{path}无法计算MD5，跳过")
                continue

            if check_md5_hex(md5_hex):
                logger.info(f"[加载知识库]{path}内容已经存在知识库内，跳过")
                continue

            try:
                documents: list[Document] = get_file_documents(path)

                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本内容，跳过")
                    continue

                split_document: list[Document] = self.splitter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue

                # 将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理好的文件的md5，避免下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path} 内容加载成功")
            except Exception as e:
                # exc_info为True会记录详细的报错堆栈，如果为False仅记录报错信息本身
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}", exc_info=True)
                continue


if __name__ == '__main__':
    service = VectorStoreService()
    service.load_document()
    retriever = service.get_retriever()
    res = retriever.invoke("迷路")
    print(f"检索到 {len(res)} 条结果")
    for i, r in enumerate(res):
        print("----" * 20)
        print(f"结果{i+1}: {r.page_content}")
