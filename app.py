import streamlit as st
from agent.react_agent import ReactAgent

st.set_page_config(
    page_title="智能扫地机器人客服",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stChatInputContainer {
        padding: 1rem 0;
        border-top: 2px solid #f0f0f0;
        margin-top: 1rem;
    }
    div[data-testid="stChatMessageContent"] {
        font-size: 1rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🤖 智能扫地机器人客服</h1>
    <p>为您提供专业的扫地机器人咨询服务</p>
</div>
""", unsafe_allow_html=True)

if 'agent' not in st.session_state:
    st.session_state.agent = ReactAgent()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'auto_question' not in st.session_state:
    st.session_state.auto_question = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
        st.markdown(message["content"])

st.markdown("---")

def handle_user_input(prompt):
    """处理用户输入并获取助手回复"""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("正在思考..."):
            for chunk in st.session_state.agent.execute_stream(prompt):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
        
        cleaned_response = full_response.strip()
        if cleaned_response.lower().startswith(prompt.lower()):
            cleaned_response = cleaned_response[len(prompt):].strip()
        
        message_placeholder.markdown(cleaned_response)
    
    st.session_state.messages.append({"role": "assistant", "content": cleaned_response})

if st.session_state.auto_question:
    handle_user_input(st.session_state.auto_question)
    st.session_state.auto_question = ""
elif prompt := st.chat_input("请输入您的问题，例如：小户型适合哪种扫地机器人？"):
    handle_user_input(prompt)

with st.sidebar:
    st.header("💡 常见问题")
    faq_questions = [
        "小户型适合哪种扫地机器人？",
        "扫地机器人如何维护保养？",
        "扫拖一体机器人值得买吗？",
        "扫地机器人常见故障有哪些？",
        "如何选择适合的扫地机器人？"
    ]
    
    st.markdown("**点击快速提问：**")
    for question in faq_questions:
        if st.button(question, use_container_width=True, type="secondary"):
            st.session_state.auto_question = question
            st.rerun()
    
    st.markdown("---")
    if st.button("🗑️ 清空对话历史", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
