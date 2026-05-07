"""Matcher Agent — scores resume against job listings."""

from pathlib import Path
from hirehive.agents.base import BaseAgent
from hirehive.tools.registry import ToolRegistry

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "matcher.system.md"


class MatcherAgent(BaseAgent):
    name = "matcher"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    def match(self, job_ids: list[int] | None = None, min_score: float = 0.0) -> str:
        job_filter = f"对指定岗位 ID {job_ids} 进行匹配" if job_ids else "对所有未匹配的岗位进行匹配"
        return self.run(
            f"{job_filter}。先读取简历，然后逐一分析岗位要求并打分。只保留评分 >= {min_score} 的结果。",
            stream_callback=None,
        )
