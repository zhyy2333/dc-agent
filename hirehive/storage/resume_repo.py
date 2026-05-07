"""Resume repository."""

import json
from hirehive.storage.engine import get_connection
from hirehive.models.resume import Resume


def save_resume(resume: Resume) -> int:
    conn = get_connection()
    row = conn.execute(
        """INSERT INTO resume (file_path, raw_text, structured_data)
           VALUES (?, ?, ?) RETURNING id""",
        (resume.file_path, resume.raw_text, resume.model_dump_json()),
    ).fetchone()
    conn.commit()
    conn.close()
    return row["id"]


def get_active_resume() -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM resume ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_resume(resume_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM resume WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
