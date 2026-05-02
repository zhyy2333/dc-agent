"""Application tracker model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    DISCOVERED = "discovered"
    MATCHED = "matched"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Application(BaseModel):
    id: Optional[int] = None
    job_id: int
    resume_id: Optional[int] = None
    pipeline_stage: PipelineStage = PipelineStage.DISCOVERED
    match_score: Optional[float] = None
    match_details: dict = Field(default_factory=dict)
    applied_at: Optional[str] = None
    application_response: Optional[str] = None
    interview_scheduled_at: Optional[str] = None
    interview_notes: str = ""
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
