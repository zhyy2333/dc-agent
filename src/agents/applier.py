"""Applier Agent — automates job applications on BOSS直聘."""

from pathlib import Path
from src.agents.base import BaseAgent
from src.tools.registry import ToolRegistry

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "applier.system.md"


class ApplierAgent(BaseAgent):
    name = "applier"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    def apply(self, job_url: str, job_title: str, company: str) -> str:
        return self.run(
            f"对以下岗位发起投递：\n标题：{job_title}\n公司：{company}\n链接：{job_url}\n\n"
            "先打开页面截图，再点击申请按钮，生成并发送个性化打招呼消息。",
            stream_callback=None,
        )
