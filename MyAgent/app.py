import sys
import time
from pathlib import Path

# Streamlit、IDE 或直接运行时都确保项目根目录可被绝对导入找到。
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from agent.react_agent import ReactAgent
from utils.logger_handler import logger

st.title("智能客服")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"] = []

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 用户输入提示词
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages = []
    try:
        with st.chat_message("assistant"):
            with st.spinner("正在为你查询..."):
                res_stream = st.session_state["agent"].execute_stream(prompt)

                def capture(generator, cache_list):
                    for chunk in generator:
                        cache_list.append(chunk)
                        for char in chunk:
                            time.sleep(0.008)
                            yield char

                st.write_stream(capture(res_stream, response_messages))
    except Exception as error:
        logger.exception("[app] Agent 调用失败: %s", error)
        friendly_message = "服务暂时不可用，请稍后重试。"
        response_messages.append(friendly_message)
        st.error(friendly_message)
    if response_messages:
        st.session_state["message"].append({"role": "assistant", "content": "".join(response_messages).strip()})
    # 让整个 Streamlit 页面立刻从头重新执行一次。
    st.rerun()
