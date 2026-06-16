import hashlib
import csv
import os

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from codes.logger_handler import logger


def get_file_md5_hex(file_path: str):
    if not os.path.exists(file_path):
        logger.error(f"「md5计算」文件不存在: {file_path}")
        return

    if not os.path.isfile(file_path):
        logger.error(f"「md5计算」不是文件: {file_path}")
        return

    md5_obj = hashlib.md5()

    chunk_size = 4096  # 4KB
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件MD5失败: {file_path}，原因: {e}")
        return None

def listdir_with_allowed_type(path: str, allowed_type: tuple[str, ...]) -> list[str]:
    """获取指定文件夹下指定后缀的文件路径列表"""
    files = []
    if not os.path.isdir(path):
        logger.error(f"不是文件夹: {path}")
        return files
    for f in os.listdir(path):
        if f.endswith(allowed_type):
            files.append(os.path.join(path, f))
    return files


def pdf_loader(filepath: str, passwd: str = None) -> list:
    return PyPDFLoader(filepath).load()


def txt_loader(filepath: str) -> list:
    return TextLoader(filepath, encoding="utf-8").load()


def load_csv_as_dict(filepath: str) -> dict:
    """
    将CSV文件加载为嵌套字典结构: {user_id: {time: {feature, efficiency, consumables, comparison}}}
    使用csv模块解析，避免手动split导致的脆弱性问题
    """
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_id = row.get("用户ID", "").strip().strip('"')
            time_val = row.get("时间", "").strip().strip('"')
            if not user_id or not time_val:
                continue
            if user_id not in data:
                data[user_id] = {}
            data[user_id][time_val] = {
                "feature": row.get("特征", "").strip().strip('"'),
                "efficiency": row.get("清洁效率", "").strip().strip('"'),
                "consumables": row.get("耗材", "").strip().strip('"'),
                "comparison": row.get("对比", "").strip().strip('"'),
            }
    return data

