import sys
from pathlib import Path

# 允许从 Streamlit、IDE 或直接执行该模块时都能导入项目根目录下的包。
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (rag_summarize, get_weather, get_user_location, get_user_id,
                                     get_current_month, fetch_external_data, fill_context_for_report)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

#Agent 主类：组装模型、工具、中间件、历史消息
class ReactAgent:
    # 封装一个 Streamlit 会话内复用的 ReAct Agent 和它的短期对话历史。
    def __init__(self):
        # Agent 实例被保存在 Streamlit session_state 时，history 会随同一会话保留。
        # 因而后续请求能读取此前的用户问题和模型回答，而不是只看到最新一句话。
        self.history = []
        # 将模型、系统提示词、可调用工具和横切中间件组装为 LangChain Agent。
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fetch_external_data, fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str):
        # 先记录本轮用户输入，使 Agent 的 messages 包含完整会话上下文。
        self.history.append({"role": "user", "content": query})
        # create_agent 期望 messages 字段作为输入状态。
        input_dict = {"messages": self.history}

        # 只保存本轮最终回答，防止工具调用中间状态被重复写入历史。
        final_answer = ""
        # context 是一次执行内的运行态标记；history 则保存跨请求对话上下文。
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            # values 模式会持续返回当前状态，列表最后一条消息代表刚产生的结果。
            latest_message = chunk["messages"][-1]
            # 只将 AIMessage 文本流式输出；用户消息和工具结果不能直接回显给页面。
            if isinstance(latest_message, AIMessage) and isinstance(latest_message.content, str):
                content = latest_message.content.strip()
                if content:
                    # 每次拿到有效模型文本时更新最终答案，并交给 Streamlit 消费器展示。
                    final_answer = content
                    yield content + "\n"

        if final_answer:
            # 流式结束后将最终回答写回历史，供下一轮追问使用。
            self.history.append({"role": "assistant", "content": final_answer})


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)
