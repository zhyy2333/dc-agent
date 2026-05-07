"""Structured logging with timestamps."""

import sys
from datetime import datetime


def log(level: str, message: str, **kwargs) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
    line = f"[{ts}] [{level}] {message}"
    if extras:
        line += f"  {extras}"
    print(line, file=sys.stderr)
