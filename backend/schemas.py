from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class GradeResponse(BaseModel):
    submission_id: int


class SubmissionStatus(BaseModel):
    status: str
    step_label: Optional[str] = None


class DeleteResponse(BaseModel):
    deleted: bool


class SubmissionSummary(BaseModel):
    id: int
    repo_name: Optional[str] = None
    repo_owner: Optional[str] = None
    assignment_title: Optional[str] = None
    assignment_type: Optional[str] = None
    total_score: Optional[int] = None
    hire_recommendation: Optional[str] = None
    status: str
    submitted_at: datetime


class SubmissionResponse(BaseModel):
    id: int
    github_url: str
    repo_name: Optional[str] = None
    repo_owner: Optional[str] = None
    problem_filename: Optional[str] = None
    problem_raw_text: Optional[str] = None
    problem_parsed: Optional[Dict[str, Any]] = None
    submitted_at: datetime
    status: str
    current_step_label: Optional[str] = None
    github_data: Optional[Dict[str, Any]] = None
    grading_data: Optional[Dict[str, Any]] = None
    features_assessment: Optional[Dict[str, Any]] = None
    total_score: Optional[int] = None
    problem_solving_score: Optional[int] = None
    quality_score: Optional[int] = None
    ai_summary: Optional[str] = None
    hire_recommendation: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
