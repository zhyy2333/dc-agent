"""Central configuration — loads from env vars, .env file, and defaults."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Config:
    # Anthropic / DeepSeek
    anthropic_base_url: str = os.getenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
    anthropic_api_key: str = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "deepseek-v4-pro")
    max_tokens: int = int(os.getenv("JOB_ASSISTANT_MAX_TOKENS", "64000"))

    # Storage
    db_path: Path = field(default_factory=lambda: DATA_DIR / "state.db")
    data_dir: Path = field(default_factory=lambda: DATA_DIR)

    # Browser
    browser_headless: bool = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    browser_user_data_dir: Path = field(default_factory=lambda: DATA_DIR / "browser_profile")

    # Search defaults
    default_city: str = os.getenv("JOB_DEFAULT_CITY", "深圳")
    default_salary_min: int = int(os.getenv("JOB_DEFAULT_SALARY_MIN", "0"))
    default_salary_max: int = int(os.getenv("JOB_DEFAULT_SALARY_MAX", "0"))

    # Delays (anti-bot)
    action_delay_min: float = float(os.getenv("ACTION_DELAY_MIN", "1.0"))
    action_delay_max: float = float(os.getenv("ACTION_DELAY_MAX", "3.0"))


config = Config()
