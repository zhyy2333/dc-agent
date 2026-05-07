"""BaseAgent — SDK call + manual tool loop shared by all specialized agents."""

import json
from typing import Any
from anthropic import Anthropic
from anthropic.types import MessageParam, ToolParam
from hirehive.llm import get_client
from hirehive.config import config
from hirehive.tools.registry import ToolRegistry
from hirehive.utils.logger import log


class BaseAgent:
    name: str = "base"
    system_prompt: str = ""
    tools: list[ToolParam] = []
    tool_registry: ToolRegistry | None = None

    def __init__(self, registry: ToolRegistry | None = None):
        self.client = get_client()
        if registry:
            self.tool_registry = registry

    def run(self, user_message: str, context: dict | None = None, stream_callback: Any = None) -> str:
        messages: list[MessageParam] = []
        if context:
            ctx_block = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append({"role": "user", "content": f"Context:\n{ctx_block}\n\nTask:\n{user_message}"})
        else:
            messages.append({"role": "user", "content": user_message})

        tool_schemas = self._get_tool_schemas()

        while True:
            log("agent-turn", self.name, tools=len(tool_schemas) if tool_schemas else 0)
            resp = self.client.messages.create(
                model=config.anthropic_model,
                max_tokens=config.max_tokens,
                system=self.system_prompt,
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
                stream=True,
            )

            accumulated = self._collect_stream(resp, stream_callback)
            messages.append({"role": "assistant", "content": accumulated})

            tool_uses = [b for b in accumulated if b.get("type") == "tool_use"]
            if not tool_uses:
                # Extract text response
                text_blocks = [b for b in accumulated if b.get("type") == "text"]
                return "\n".join(b.get("text", "") for b in text_blocks)

            # Execute tools
            tool_results: list[dict] = []
            for block in tool_uses:
                result = self._execute_tool(block["name"], block["input"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })

            messages.append({"role": "user", "content": tool_results})

    def _collect_stream(self, stream, callback=None) -> list[dict]:
        blocks: list[dict] = []
        current: dict | None = None
        for event in stream:
            if event.type == "content_block_start":
                block = event.content_block
                block_type = str(block.type)
                current = {"type": block_type, "text": ""}
                if block_type == "tool_use":
                    current["id"] = getattr(block, "id", "")
                    current["name"] = getattr(block, "name", "")
                    current["input"] = ""
                elif block_type in ("thinking", "redacted_thinking"):
                    current["thinking"] = ""
                blocks.append(current)
            elif event.type == "content_block_delta":
                if current is None:
                    continue
                delta = event.delta
                delta_type = str(delta.type)
                if delta_type == "text_delta":
                    current["text"] += getattr(delta, "text", "")
                    if callback:
                        callback("text", getattr(delta, "text", ""))
                elif delta_type == "input_json_delta":
                    current["input"] += getattr(delta, "partial_json", "")
                elif delta_type == "thinking_delta":
                    current["thinking"] = current.get("thinking", "") + getattr(delta, "thinking", "")
                elif delta_type == "signature_delta":
                    current["signature"] = current.get("signature", "") + getattr(delta, "signature", "")
            elif event.type == "content_block_stop":
                if current and "input" in current and isinstance(current.get("input"), str):
                    try:
                        current["input"] = json.loads(current["input"])
                    except json.JSONDecodeError:
                        pass
                current = None
        return blocks

    def _execute_tool(self, name: str, inputs: dict) -> Any:
        if self.tool_registry:
            return self.tool_registry.execute(name, inputs)
        return {"error": f"No tool registry for {self.name}. Tool '{name}' not available."}

    def _get_tool_schemas(self) -> list[dict] | None:
        if not self.tool_registry:
            return None
        schemas = self.tool_registry.get_schemas()
        return schemas if schemas else None
