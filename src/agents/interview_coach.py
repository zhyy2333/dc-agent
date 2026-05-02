"""Interview Coach Agent — generates questions and runs mock interviews."""

from pathlib import Path
from src.agents.base import BaseAgent
from src.tools.registry import ToolRegistry

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "interview_coach.system.md"


class InterviewCoachAgent(BaseAgent):
    name = "interview_coach"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    def prepare(self, job_description: str, job_title: str = "", company: str = "") -> str:
        return self.run(
            f"为以下岗位生成面试准备材料：\n公司：{company}\n岗位：{job_title}\n"
            f"岗位描述：{job_description}\n\n"
            "请生成 10-15 道个性化面试题，覆盖技术、项目、行为三个类别，并给出每题的考察点和参考答案要点。",
            stream_callback=None,
        )

    def mock_interview(self, user_response: str, history: list[dict] | None = None) -> str:
        ctx = {"conversation_history": history or []}
        message = user_response if user_response else "开始模拟面试。先介绍你自己，然后提出第一个面试问题。"
        return self.run(message, context=ctx, stream_callback=None)
