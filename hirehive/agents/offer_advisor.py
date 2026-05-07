"""Offer Advisor Agent — compares multiple job offers."""

from pathlib import Path
from hirehive.agents.base import BaseAgent
from hirehive.tools.registry import ToolRegistry

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "offer_advisor.system.md"


class OfferAdvisorAgent(BaseAgent):
    name = "offer_advisor"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    def compare(self) -> str:
        return self.run(
            "使用 get_offers 获取所有 pending 状态的 Offer，然后从薪资、发展、生活、公司、文化五个维度逐一对比，"
            "给出排名和最终推荐。",
            stream_callback=None,
        )

    def analyze(self, offer_id: int) -> str:
        return self.run(
            f"对 Offer ID={offer_id} 进行深度分析，给出该 Offer 的优劣势、风险点和发展预期。",
            stream_callback=None,
        )
