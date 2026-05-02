"""Application repository."""

import json
from src.storage.engine import get_connection
from src.models.application import Application


def save_application(app: Application) -> int:
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM application WHERE job_id = ? AND resume_id = ?",
        (app.job_id, app.resume_id),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE application SET pipeline_stage=?, match_score=?, match_details=?,
               applied_at=?, application_response=?, interview_scheduled_at=?,
               interview_notes=?, updated_at=datetime('now')
               WHERE id=?""",
            (app.pipeline_stage.value, app.match_score,
             json.dumps(app.match_details, ensure_ascii=False),
             app.applied_at, app.application_response,
             app.interview_scheduled_at, app.interview_notes,
             existing["id"]),
        )
        app_id = existing["id"]
    else:
        row = conn.execute(
            """INSERT INTO application (job_id, resume_id, pipeline_stage, match_score,
               match_details, applied_at)
               VALUES (?, ?, ?, ?, ?, ?) RETURNING id""",
            (app.job_id, app.resume_id, app.pipeline_stage.value, app.match_score,
             json.dumps(app.match_details, ensure_ascii=False), app.applied_at),
        ).fetchone()
        app_id = row["id"]
    conn.commit()
    conn.close()
    return app_id


def list_applications(stage: str | None = None, limit: int = 100) -> list[dict]:
    conn = get_connection()
    query = """SELECT a.*, j.title, j.company, j.city
               FROM application a JOIN job j ON a.job_id = j.id WHERE 1=1"""
    params: list = []
    if stage:
        query += " AND a.pipeline_stage = ?"
        params.append(stage)
    query += " ORDER BY a.match_score DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_application(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM application WHERE job_id = ?", (job_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_pipeline_stats() -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT pipeline_stage, COUNT(*) as cnt FROM application GROUP BY pipeline_stage"
    ).fetchall()
    conn.close()
    return {r["pipeline_stage"]: r["cnt"] for r in rows}
