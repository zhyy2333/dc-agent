"""Offer model for comparison."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Offer(BaseModel):
    id: Optional[int] = None
    application_id: Optional[int] = None
    company: str
    position: str
    base_salary: int
    bonus_months: int = 12
    equity: str = ""
    benefits: list[str] = Field(default_factory=list)
    work_mode: str = "onsite"
    location: str = ""
    commute_minutes: int = 0
    growth_potential: str = ""
    received_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    status: str = "pending"
