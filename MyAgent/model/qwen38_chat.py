"""qwen3.8-max 的 LangChain 适配器。"""

import json
import os
from typing import Any, Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI


class Qwen38ChatModel(BaseChatModel):
    """通过阿里云 OpenAI 兼容接口调用 qwen3.8-max。"""

    model_name: str = "qwen3.8-max"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    @property
    def _llm_type(self) -> str:
        return "qwen3_8_openai_compatible"

    @property
    def _identifying_params(self) -> dict[str, str]:
        return {"model_name": self.model_name, "base_url": self.base_url}

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any):
        return self.bind(tools=[convert_to_openai_tool(tool) for tool in tools], **kwargs)

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None,
                  run_manager: Any = None, **kwargs: Any) -> ChatResult:
        request: dict[str, Any] = {
            "model": self.model_name,
            "messages": [self._to_openai_message(message) for message in messages],
            "extra_body": {"enable_thinking": False},
        }
        if stop:
            request["stop"] = stop
        if tools := kwargs.get("tools"):
            request["tools"] = tools
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未找到 DASHSCOPE_API_KEY，无法调用 qwen3.8-max。")
        response = OpenAI(api_key=api_key, base_url=self.base_url).chat.completions.create(**request)
        output = response.choices[0].message
        tool_calls = []
        for call in output.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append({"name": call.function.name, "args": arguments, "id": call.id})
        message = AIMessage(content=output.content or "", tool_calls=tool_calls,
                            response_metadata={"model_name": response.model})
        return ChatResult(generations=[ChatGeneration(message=message)])

    @staticmethod
    def _to_openai_message(message: BaseMessage) -> dict[str, Any]:
        content = message.content
        if isinstance(message, SystemMessage):
            return {"role": "system", "content": content}
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": content}
        if isinstance(message, ToolMessage):
            return {"role": "tool", "content": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
                    "tool_call_id": message.tool_call_id}
        if isinstance(message, AIMessage):
            result: dict[str, Any] = {"role": "assistant", "content": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)}
            if message.tool_calls:
                result["tool_calls"] = [{"id": call["id"], "type": "function", "function": {"name": call["name"], "arguments": json.dumps(call["args"], ensure_ascii=False)}} for call in message.tool_calls]
            return result
        raise TypeError(f"不支持的消息类型：{type(message).__name__}")
