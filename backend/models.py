from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from backend.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    github_url = Column(String, nullable=False)
    repo_name = Column(String, nullable=True)
    repo_owner = Column(String, nullable=True)
    problem_filename = Column(String, nullable=True)
    problem_raw_text = Column(Text, nullable=True)
    problem_parsed = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING", nullable=False)
    current_step_label = Column(String, default="Waiting to start", nullable=True)
    github_data = Column(JSON, nullable=True)
    grading_data = Column(JSON, nullable=True)
    features_assessment = Column(JSON, nullable=True)
    total_score = Column(Integer, nullable=True)
    problem_solving_score = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)
    ai_summary = Column(Text, nullable=True)
    hire_recommendation = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
