"""Central tool registry — maps tool name to callable executor."""

from typing import Any, Callable
import json
from hirehive.utils.logger import log


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, schema: dict, func: Callable) -> None:
        self._tools[name] = {"schema": schema, "func": func}

    def get_schemas(self, names: list[str] | None = None) -> list[dict]:
        if names is None:
            return [t["schema"] for t in self._tools.values()]
        return [self._tools[n]["schema"] for n in names if n in self._tools]

    def execute(self, name: str, inputs: dict) -> Any:
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}
        log("tool", name, **{k: str(v)[:80] for k, v in inputs.items()})
        try:
            result = self._tools[name]["func"](**inputs)
            return result
        except Exception as e:
            log("tool-error", name, error=str(e))
            return {"error": str(e)}
