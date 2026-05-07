"""Database read/write tools exposed to agents."""

from typing import Any
from hirehive.storage import job_repo, application_repo, offer_repo, resume_repo
from hirehive.models.job import Job, SalaryRange
from hirehive.models.application import Application
from hirehive.models.offer import Offer


def list_jobs(stage: str | None = None, min_score: float | None = None, limit: int = 100) -> list[dict]:
    return job_repo.list_jobs(stage=stage, min_score=min_score, limit=limit)


def save_job(job_data: dict[str, Any]) -> dict:
    salary = SalaryRange(min=job_data.get("salary_min"), max=job_data.get("salary_max"))
    job = Job(
        external_id=job_data.get("external_id", ""),
        title=job_data["title"],
        company=job_data["company"],
        city=job_data.get("city", ""),
        district=job_data.get("district"),
        salary_range=salary,
        description=job_data.get("description", ""),
        requirements=job_data.get("requirements", ""),
        tags=job_data.get("tags", []),
        url=job_data.get("url", ""),
        posted_date=job_data.get("posted_date"),
    )
    job_id = job_repo.save_job(job)
    return {"id": job_id, "status": "saved"}


def list_applications(stage: str | None = None, limit: int = 100) -> list[dict]:
    return application_repo.list_applications(stage=stage, limit=limit)


def update_application(job_id: int, stage: str, **kwargs: Any) -> dict:
    from hirehive.models.application import PipelineStage
    app_data = application_repo.get_application(job_id)
    if app_data:
        for key, value in kwargs.items():
            app_data[key] = value
        app_data["pipeline_stage"] = stage
        # Reconstruct Application from dict — use the save_application directly
        import json
        conn_ = None
        from hirehive.storage.engine import get_connection
        conn_ = get_connection()
        conn_.execute(
            """UPDATE application SET pipeline_stage=?, match_score=?, match_details=?,
               updated_at=datetime('now') WHERE job_id=?""",
            (stage, kwargs.get("match_score"), json.dumps(kwargs.get("match_details", {}), ensure_ascii=False), job_id),
        )
        conn_.commit()
        conn_.close()
        return {"status": "updated", "job_id": job_id}
    return {"error": "application not found", "job_id": job_id}


def save_offer_state(offer_data: dict[str, Any]) -> dict:
    offer = Offer(**offer_data)
    offer_id = offer_repo.save_offer(offer)
    return {"id": offer_id, "status": "saved"}


def get_offers(status: str | None = None) -> list[dict]:
    return offer_repo.get_offers(status=status)


def get_active_resume() -> dict | None:
    return resume_repo.get_active_resume()
