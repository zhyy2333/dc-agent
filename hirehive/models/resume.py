"""Parsed resume model."""

from typing import Optional
from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str
    title: str
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class Education(BaseModel):
    school: str
    degree: str
    major: str = ""
    graduation_year: int = 0


class Resume(BaseModel):
    id: Optional[int] = None
    name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    file_path: str = ""
    raw_text: str = ""
