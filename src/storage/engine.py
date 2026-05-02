"""SQLite connection management."""

import sqlite3
from pathlib import Path
from src.config import config


def get_db_path() -> Path:
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    return config.db_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    conn = get_connection()
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
