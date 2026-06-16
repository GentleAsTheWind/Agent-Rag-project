import os

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def resolve_api_base_url() -> str:
    env_value = os.getenv("STREAMLIT_API_BASE_URL")
    if env_value:
        return env_value

    try:
        return st.secrets.get("api_base_url", "http://127.0.0.1:8000")
    except StreamlitSecretNotFoundError:
        return "http://127.0.0.1:8000"


API_BASE_URL = resolve_api_base_url()


st.set_page_config(
    page_title="智能扫地机器人客服",
    page_icon="🤖",
    layout="centered",
)

st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #0f766e 0%, #164e63 100%);
        border-radius: 18px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
    }
    .main-header p {
        color: rgba(255,255,255,0.88);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="main-header">
    <h1>智能扫地机器人客服</h1>
    <p>生产化 API 的 Streamlit 演示入口</p>
</div>
""",
    unsafe_allow_html=True,
)


def api_request(method: str, path: str, token: str | None = None, json: dict | None = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{API_BASE_URL}{path}", headers=headers, json=json, timeout=60)


if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


with st.sidebar:
    st.header("登录")
    username = st.text_input("用户名", value="user1001")
    password = st.text_input("密码", value="user1001", type="password")
    if st.button("获取令牌", use_container_width=True):
        response = api_request("POST", "/auth/login", json={"username": username, "password": password})
        if response.ok:
            payload = response.json()
            st.session_state.access_token = payload["access_token"]
            st.session_state.refresh_token = payload["refresh_token"]
            st.success("登录成功")
        else:
            st.error(response.text)

    st.caption("示例账号：`user1001/user1001`、`admin/admin123`")
    st.markdown("---")
    st.header("常见问题")
    for question in [
        "小户型适合哪种扫地机器人？",
        "扫地机器人如何维护保养？",
        "扫拖一体机器人值得买吗？",
        "查询我2025-01的使用报告",
        "扫地机器人回充失败怎么办？",
    ]:
        if st.button(question, use_container_width=True):
            st.session_state.pending_question = question
    if st.button("清空会话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.rerun()


for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
        st.markdown(message["content"])


def send_message(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        if not st.session_state.access_token:
            answer = "请先在左侧登录，再发起对话。"
            placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            return

        response = api_request(
            "POST",
            "/chat",
            token=st.session_state.access_token,
            json={
                "thread_id": st.session_state.thread_id,
                "message": prompt,
                "stream": False,
                "client_context": {},
            },
        )
        if not response.ok:
            answer = f"请求失败：{response.text}"
            placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            return

        payload = response.json()
        st.session_state.thread_id = payload["thread_id"]
        citations = payload.get("citations", [])
        answer = payload["answer"]
        if citations:
            answer = answer + "\n\n**引用来源**\n" + "\n".join(
                f"- {item['source']} / {item['chunk_id']}" for item in citations
            )
        placeholder.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


pending_question = st.session_state.pop("pending_question", None)
if pending_question:
    send_message(pending_question)

if prompt := st.chat_input("请输入问题，例如：查询我2025-01的使用报告"):
    send_message(prompt)
