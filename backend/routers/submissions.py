import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.grader.pipeline import run_grading_pipeline
from backend.grader.problem_parser import extract_text_from_file, parse_problem_statement_with_gemini
from backend.models import Submission
from backend.schemas import DeleteResponse, GradeResponse, SubmissionResponse, SubmissionStatus, SubmissionSummary

router = APIRouter(prefix="/api", tags=["submissions"])


@router.post("/parse-problem")
def parse_problem(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    suffix = Path(file.filename or "problem.txt").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        file_path = tmp.name
    try:
        extracted = extract_text_from_file(file_path)
        parsed = parse_problem_statement_with_gemini(extracted)
        return {"problem_raw_text": extracted, "problem_parsed": parsed}
    finally:
        Path(file_path).unlink(missing_ok=True)


@router.post("/grade", response_model=GradeResponse)
def grade_submission(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    github_url: str = Form(...),
    db: Session = Depends(get_db),
):
    if not (file.filename or "").lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

    submission = Submission(
        github_url=github_url,
        problem_filename=file.filename,
        status="PENDING",
        current_step_label="Waiting to start",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    suffix = Path(file.filename or "problem.txt").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        uploaded_file_path = tmp.name

    background_tasks.add_task(run_grading_pipeline, submission.id, uploaded_file_path)
    return GradeResponse(submission_id=submission.id)


@router.get("/submissions", response_model=list[SubmissionSummary])
def list_submissions(db: Session = Depends(get_db)):
    items = db.query(Submission).order_by(Submission.submitted_at.desc()).all()
    out = []
    for s in items:
        parsed = s.problem_parsed or {}
        out.append(
            SubmissionSummary(
                id=s.id,
                repo_name=s.repo_name,
                repo_owner=s.repo_owner,
                assignment_title=parsed.get("assignment_title"),
                assignment_type=parsed.get("assignment_type"),
                total_score=s.total_score,
                hire_recommendation=s.hire_recommendation,
                status=s.status,
                submitted_at=s.submitted_at,
            )
        )
    return out


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    item = db.query(Submission).filter(Submission.id == submission_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    return item


@router.get("/submissions/{submission_id}/status", response_model=SubmissionStatus)
def get_submission_status(submission_id: int, db: Session = Depends(get_db)):
    item = db.query(Submission).filter(Submission.id == submission_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionStatus(status=item.status, step_label=item.current_step_label)


@router.delete("/submissions/{submission_id}", response_model=DeleteResponse)
def delete_submission(submission_id: int, db: Session = Depends(get_db)):
    item = db.query(Submission).filter(Submission.id == submission_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    db.delete(item)
    db.commit()
    return DeleteResponse(deleted=True)
