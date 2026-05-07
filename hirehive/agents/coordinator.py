"""Coordinator Agent — the Planner/Orchestrator for the pipeline."""

from pathlib import Path
from hirehive.agents.base import BaseAgent
from hirehive.tools.registry import ToolRegistry
from hirehive.tools import state_tools


PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "coordinator.system.md"


class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    def plan(self, user_intent: str) -> str:
        """Given a user intent, return a stage-by-stage execution plan."""
        return self.run(
            f"根据以下用户意图制定执行计划，列出需要执行的阶段和每个阶段的目标：\n\n{user_intent}",
            stream_callback=None,
        )

    def execute_stage(self, stage: str, context: dict) -> str:
        """Execute a pipeline stage and return results."""
        return self.run(
            f"执行流水线阶段 [{stage}]，使用上下文中的数据完成任务，并汇总结果。",
            context=context,
            stream_callback=None,
        )

    def present_results(self, results: list[dict]) -> str:
        """Format and present final results to the user."""
        ctx = {
            "stages_completed": len(results),
            "results": results,
        }
        return self.run("汇总以下流水线执行结果，用清晰的中文呈现给用户。", context=ctx)
