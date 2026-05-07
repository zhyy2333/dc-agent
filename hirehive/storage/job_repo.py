"""Job repository — CRUD for discovered job listings."""

import json
from hirehive.storage.engine import get_connection
from hirehive.models.job import Job, SalaryRange


def save_job(job: Job) -> int:
    conn = get_connection()
    row = conn.execute(
        """INSERT INTO job (external_id, title, company, city, district,
           salary_min, salary_max, description, requirements, tags, url, source, posted_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(external_id) DO UPDATE SET
           title=excluded.title, company=excluded.company, city=excluded.city,
           salary_min=excluded.salary_min, salary_max=excluded.salary_max,
           description=excluded.description, requirements=excluded.requirements,
           tags=excluded.tags, url=excluded.url
           RETURNING id""",
        (job.external_id, job.title, job.company, job.city, job.district,
         job.salary_range.min, job.salary_range.max,
         job.description, job.requirements, json.dumps(job.tags, ensure_ascii=False),
         job.url, job.source, job.posted_date),
    ).fetchone()
    conn.commit()
    conn.close()
    return row["id"]


def list_jobs(stage: str | None = None, min_score: float | None = None, limit: int = 100) -> list[dict]:
    conn = get_connection()
    query = """SELECT j.*, a.pipeline_stage, a.match_score
               FROM job j LEFT JOIN application a ON j.id = a.job_id WHERE 1=1"""
    params: list = []
    if stage:
        query += " AND a.pipeline_stage = ?"
        params.append(stage)
    if min_score is not None:
        query += " AND a.match_score >= ?"
        params.append(min_score)
    query += " ORDER BY j.discovered_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM job WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_job_by_external_id(external_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM job WHERE external_id = ?", (external_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def job_count() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM job").fetchone()
    conn.close()
    return row["cnt"]
