"""Job listing model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SalaryRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None


class Job(BaseModel):
    id: Optional[int] = None
    external_id: str = ""
    title: str
    company: str
    city: str = ""
    district: Optional[str] = None
    salary_range: SalaryRange = Field(default_factory=SalaryRange)
    description: str = ""
    requirements: str = ""
    tags: list[str] = Field(default_factory=list)
    url: str = ""
    source: str = "boss_zhipin"
    posted_date: Optional[str] = None
    discovered_at: str = Field(default_factory=lambda: datetime.now().isoformat())
