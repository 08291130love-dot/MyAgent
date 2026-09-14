"""设计版前端入口。

运行方式：streamlit run app_design.py
本文件通过 Streamlit 组件包装和 CSS 重塑界面；app.py 的 Agent、RAG 和聊天逻辑不做改动。
"""

import runpy
from html import escape
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="智能管家",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #1f2937;
        --muted: #8793a6;
        --line: #e7edf5;
        --blue: #2674ff;
        --soft-blue: #eaf2ff;
        --panel: rgba(255, 255, 255, .90);
    }
    .stApp {
        background:
            radial-gradient(circle at 80% 4%, rgba(137, 194, 255, .20), transparent 24rem),
            radial-gradient(circle at 0% 95%, rgba(198, 224, 255, .24), transparent 23rem),
            #f4f7fb;
    }
    [data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }

    /* 左侧“客服工作台”导航区。 */
    [data-testid="stSidebar"] {
        min-width: 246px; max-width: 246px;
        background: rgba(255, 255, 255, .86);
        border-right: 1px solid var(--line);
        box-shadow: 7px 0 26px rgba(23, 46, 81, .035);
    }
    [data-testid="stSidebar"] > div:first-child { padding: 1.35rem .9rem; }
    .side-brand { display:flex; align-items:center; gap:.7rem; margin:.2rem .35rem 1.65rem; }
    .side-logo {
        display:grid; place-items:center; width:2.35rem; height:2.35rem; border-radius:.78rem;
        color:#fff; background:linear-gradient(135deg,#3585ff,#5967ec); box-shadow:0 8px 16px rgba(44,112,236,.25);
        font-size:1.12rem;
    }
    .side-brand-title { color:var(--ink); font-size:1rem; font-weight:800; letter-spacing:-.02em; }
    .side-brand-sub { margin-top:.06rem; color:var(--muted); font-size:.68rem; }
    .side-label { margin:.4rem .4rem .55rem; color:#9aa5b5; font-size:.72rem; font-weight:700; }
    .side-current {
        display:flex; align-items:center; gap:.62rem; margin:.25rem 0 1rem; padding:.72rem .72rem;
        color:#2563eb; border-radius:.72rem; background:#edf4ff; font-size:.86rem; font-weight:760;
    }
    .side-current-icon { display:grid; place-items:center; width:1.55rem; height:1.55rem; border-radius:.5rem; color:#fff; background:#2e79f5; }
    .contact-row { display:flex; align-items:center; gap:.62rem; padding:.49rem .52rem; color:#66758b; font-size:.79rem; }
    .contact-avatar { display:grid; place-items:center; flex:0 0 auto; width:1.8rem; height:1.8rem; border-radius:50%; background:#f0f4fb; font-size:.88rem; }
    .contact-status { display:block; margin-top:.06rem; color:#a1adbb; font-size:.65rem; }
    .side-tip { margin-top:1.25rem; padding:.78rem; border:1px solid #e3edff; border-radius:.75rem; color:#5b6f8d; background:#f7faff; font-size:.72rem; line-height:1.65; }

    /* 中间对话工作区。 */
    .block-container { max-width: 940px; padding: 2rem 2rem 7.2rem; }
    h1 {
        display:flex !important; align-items:center; gap:.68rem; margin:0 !important;
        padding:1.08rem 1.28rem !important; border:1px solid var(--line); border-radius:18px;
        color:var(--ink) !important; background:var(--panel); box-shadow:0 10px 28px rgba(27, 51, 86, .055);
        font-size:1.24rem !important; letter-spacing:-.025em;
    }
    h1::before {
        content:"💬"; display:grid; place-items:center; width:2.18rem; height:2.18rem; border-radius:.72rem;
        background:var(--soft-blue); font-size:1rem;
    }
    h1::after {
        content:"● 在线"; margin-left:auto; color:#14a36f; font-size:.76rem; font-weight:650; letter-spacing:0;
    }
    hr { margin:1.15rem 0 .8rem !important; border-color:transparent !important; }
    .workspace-note {
        display:flex; align-items:center; gap:.48rem; margin:.12rem .12rem 1.1rem; color:#91a0b3; font-size:.77rem;
    }
    .workspace-note span { color:#5a6d83; font-weight:700; }
    .ability-chip {
        display:inline-block; margin:0 .35rem .25rem 0; padding:.28rem .54rem; border:1px solid #e1eaf6;
        border-radius:999px; color:#74849b; background:rgba(255,255,255,.74); font-size:.69rem;
    }

    /* 自定义聊天气泡：不依赖 Streamlit 内部节点，杜绝空列、横线和错位。 */
    .bubble-row { display:flex; width:100%; margin:1.08rem 0; }
    .bubble-row.assistant { justify-content:flex-start; }
    .bubble-row.user { justify-content:flex-end; }
    .message-bubble {
        width:fit-content; max-width:72%; padding:.86rem 1rem .92rem; border:1px solid #e6edf6;
        border-radius:18px 18px 18px 5px; background:#fff; box-shadow:0 7px 18px rgba(32,55,85,.045);
    }
    .bubble-row.user .message-bubble {
        border-color:#cfe1ff; border-radius:18px 18px 5px 18px;
        background:linear-gradient(135deg,#eef6ff,#dcecff);
    }
    .identity-row { display:flex; align-items:center; gap:.42rem; margin:0 0 .6rem; color:#1d8f82; font-size:.79rem; font-weight:780; }
    .bubble-row.user .identity-row { justify-content:flex-end; color:#3b72c8; }
    .identity-avatar { display:grid; place-items:center; width:1.5rem; height:1.5rem; border-radius:50%; background:#e3f7f3; font-size:.83rem; }
    .bubble-row.user .identity-avatar { background:#dbeafe; }
    .identity-dot { width:.44rem; height:.44rem; border-radius:50%; background:currentColor; opacity:.9; }
    .identity-note { color:#99a6b6; font-size:.69rem; font-weight:500; }
    .message-body { color:#344256; font-size:.96rem; line-height:1.88; word-break:break-word; }
    .bubble-row.user .message-body { color:#294968; text-align:left; }

    /* 底部输入区。 */
    [data-testid="stChatInput"] {
        border:1px solid #dce6f4; border-radius:16px; background:rgba(255,255,255,.96);
        box-shadow:0 13px 30px rgba(30,55,93,.13);
    }
    [data-testid="stChatInput"] textarea { min-height:48px !important; padding:.76rem .95rem !important; color:#334155; font-size:.91rem; }
    [data-testid="stChatInput"] textarea::placeholder { color:#a1adbd; }
    [data-testid="stChatInputSubmitButton"] { color:var(--blue); }
    @media (max-width: 900px) {
        .block-container { max-width:760px; padding:1.25rem 1rem 6.7rem; }
        [data-testid="stSidebar"] { min-width:220px; max-width:220px; }
    }
    @media (max-width: 700px) {
        .block-container { padding:1rem .75rem 6.5rem; }
        [data-testid="stChatMessage"] { max-width:92%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-logo">🤖</div>
            <div><div class="side-brand-title">客服小❀</div><div class="side-brand-sub">SMART ROBOT CARE</div></div>
        </div>
        <div class="side-label">会话工作台</div>
        <div class="side-current"><span class="side-current-icon">▣</span>正在咨询 <span style="margin-left:auto;font-size:.68rem;">在线</span></div>
        <div class="side-label">服务能力</div>
        <div class="contact-row"><span class="contact-avatar">📚</span><div>设备知识库<span class="contact-status">说明书与故障排查</span></div></div>
        <div class="contact-row"><span class="contact-avatar">🌦️</span><div>天气建议<span class="contact-status">湿度与拖地适配</span></div></div>
        <div class="contact-row"><span class="contact-avatar">📊</span><div>使用报告<span class="contact-status">设备习惯与保养建议</span></div></div>
        <div class="side-tip">客服小化会结合知识库和工具结果回答。涉及设备故障时，请尽量描述型号、现象和出现频率。</div>
        """,
        unsafe_allow_html=True,
    )

# Streamlit 会在每次交互时重跑此文件，原始函数只保存一次，避免包装函数层层嵌套。
if not hasattr(st, "_zhisaotong_base_title"):
    st._zhisaotong_base_title = st.title
if not hasattr(st, "_zhisaotong_base_chat_message"):
    st._zhisaotong_base_chat_message = st.chat_message
if not hasattr(st, "_zhisaotong_base_chat_input"):
    st._zhisaotong_base_chat_input = st.chat_input

_original_title = st._zhisaotong_base_title
_original_chat_input = st._zhisaotong_base_chat_input
if not hasattr(st, "_zhisaotong_base_write_stream"):
    st._zhisaotong_base_write_stream = st.write_stream
_original_write_stream = st._zhisaotong_base_write_stream


_active_message = None


class DesignMessage:
    """给未修改的 app.py 提供兼容的 write / 上下文管理接口，并用 HTML 渲染稳定左右气泡。"""

    def __init__(self, role: str):
        self.role = "user" if str(role).lower() == "user" else "assistant"
        self.placeholder = st.empty()

    def _render(self, content: str) -> None:
        is_user = self.role == "user"
        name = "用户" if is_user else "客服小化"
        note = "我正在聆听" if is_user else "智能管家"
        avatar = "🙂" if is_user else "🤖"
        # 文本先转义再插入 HTML，避免用户输入或模型输出被浏览器当作标签执行。
        safe_content = escape(str(content)).replace("\n", "<br>")
        self.placeholder.markdown(
            f"<div class='bubble-row {self.role}'>"
            f"<section class='message-bubble'>"
            f"<div class='identity-row'><span class='identity-avatar'>{avatar}</span>"
            f"<span class='identity-dot'></span>{name}"
            f"<span class='identity-note'>· {note}</span></div>"
            f"<div class='message-body'>{safe_content}</div>"
            f"</section></div>",
            unsafe_allow_html=True,
        )

    def write(self, content: str):
        self._render(content)
        return self

    def write_stream(self, generator):
        full_content = ""
        for chunk in generator:
            full_content += str(chunk)
            self._render(full_content)
        return full_content

    def __enter__(self):
        global _active_message
        _active_message = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        global _active_message
        _active_message = None
        return False


def design_title(_body: str, *args, **kwargs):
    """把 app.py 的普通标题包装成客服工作台顶栏。"""
    result = _original_title("客服小化 · 智能客服", *args, **kwargs)
    st.markdown(
        """
        <div class="workspace-note"><span>当前会话</span> · 有问题尽管问我
            <span style="margin-left:auto;">
                <i class="ability-chip">RAG 知识库</i><i class="ability-chip">实时工具</i><i class="ability-chip">连续对话</i>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return result


def design_chat_message(name: str, *args, **kwargs):
    """拦截 app.py 的原生聊天调用，统一交给稳定的自定义左右气泡。"""
    return DesignMessage(name)


def design_chat_input(placeholder: str = "", *args, **kwargs):
    """给原 app.py 未传提示词的输入框提供更明确的引导文案。"""
    return _original_chat_input(placeholder or "描述你的设备问题，客服小化马上为你解答…", *args, **kwargs)


def design_write_stream(generator, *args, **kwargs):
    """仅在客服气泡上下文中接管流式输出；其他场景仍使用 Streamlit 原实现。"""
    if _active_message is not None:
        return _active_message.write_stream(generator)
    return _original_write_stream(generator, *args, **kwargs)


st.title = design_title
st.chat_message = design_chat_message
st.chat_input = design_chat_input
st.write_stream = design_write_stream

# 设计入口最后执行原 app.py：业务调用、会话保存和 Agent 行为完全复用。
runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
