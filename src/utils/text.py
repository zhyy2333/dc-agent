"""Text processing helpers."""

import re
import random
import time


def extract_email(text: str) -> str | None:
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str) -> str | None:
    m = re.search(r"1[3-9]\d-?\d{4}-?\d{4}", text)
    return m.group(0) if m else None


def truncate(text: str, max_len: int = 200) -> str:
    return text if len(text) <= max_len else text[:max_len] + "..."


def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    time.sleep(random.uniform(min_s, max_s))
