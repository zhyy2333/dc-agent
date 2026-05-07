"""Searcher Agent — discovers jobs on BOSS直聘."""

from pathlib import Path
from hirehive.agents.base import BaseAgent
from hirehive.tools.registry import ToolRegistry

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "searcher.system.md"


class SearcherAgent(BaseAgent):
    name = "searcher"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    def search(self, keyword: str, city: str, salary_min: int = 0, salary_max: int = 0, max_pages: int = 3) -> str:
        return self.run(
            f"搜索岗位：关键词={keyword}，城市={city}，薪资范围={salary_min}-{salary_max}。"
            f"请搜索最多 {max_pages} 页结果，对前 20 个岗位逐一抓取详情。",
            stream_callback=None,
        )
