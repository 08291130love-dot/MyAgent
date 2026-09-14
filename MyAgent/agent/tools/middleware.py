from typing import Callable
from utils.prompt_loader import load_system_prompts, load_report_prompts
from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handler import logger


@wrap_tool_call
# 工具调用装饰器：在真正执行任意工具前后统一执行此函数。
def monitor_tool(
        # ToolCallRequest 包含工具名、入参和当前运行时上下文。
        request: ToolCallRequest,
        # handler 是被装饰器包装的原始工具执行函数。
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:             # 返回工具消息或状态更新命令。
    # 先记录工具名，方便定位 Agent 选择了哪条执行路径。
    logger.info(f"[tool monitor]执行工具：{request.tool_call['name']}")
    # 再记录实际参数，便于排查模型是否构造了错误输入。
    logger.info(f"[tool monitor]传入参数：{request.tool_call['args']}")

    try:
        # 调用真实工具，例如 RAG、天气或 CSV 数据查询。
        result = handler(request)
        # 成功日志用于统计工具成功率与排查链路。
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")

        # 报告工具本身不产出报告，只把本次运行切换为“报告模式”。
        if request.tool_call['name'] == "fill_context_for_report":
            # 该标记会被下方 dynamic_prompt 中间件读取。
            request.runtime.context["report"] = True

        # 将原工具的输出原样交还给 Agent 继续推理。
        return result
    except Exception as e:
        # 统一记录失败信息，避免工具异常静默丢失。
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        # 向上抛出，使 Agent 框架能按自身策略处理失败。
        raise e


@before_model
# 模型调用前钩子：每次 LLM 推理之前自动执行。
def log_before_model(
        state: AgentState,          # Agent 执行状态，包含完整 messages。
        runtime: Runtime,           # 运行时上下文，可承载本轮执行标记。
):         # 此处只记录日志，不修改模型输入。
    # 输出上下文消息数量，帮助观察多轮对话的增长情况。
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息。")

    # Debug 日志记录最后一条消息类型与内容，排查工具结果或用户输入。
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}")

    # 返回 None 表示不额外改变 AgentState。
    return None


@dynamic_prompt                 # 每一次模型生成提示词之前，都会调用此函数。
def report_prompt_switch(request: ModelRequest):     # 根据运行态动态选择系统提示词。
    # 默认值为 false，保证普通问答仍使用客服系统提示词。
    is_report = request.runtime.context.get("report", False)
    if is_report:               # 报告场景返回报告结构、语气等专用约束。
        return load_report_prompts()

    # 非报告场景回退到通用客服/工具编排提示词。
    return load_system_prompts()
