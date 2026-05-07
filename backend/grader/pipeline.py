import os
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Submission
from backend.grader.ai_evaluator import generate_final_evaluation
from backend.grader.code_scanner import (
    assess_features_with_gemini,
    build_folder_tree,
    collect_source_blob,
    detect_dependencies,
    detect_routes,
    keyword_hits,
)
from backend.grader.github_checker import fetch_github_metadata
from backend.grader.problem_parser import extract_text_from_file, parse_problem_statement_with_gemini
from backend.grader.repo_runner import clone_repo, run_project_checks
from backend.grader.scorer import calculate_scores


STEP_LABELS = {
    "PARSING": "Reading problem statement...",
    "EXTRACTING": "Extracting requirements...",
    "FETCHING": "Fetching GitHub data...",
    "CLONING": "Cloning repository...",
    "RUNNING": "Running build and tests...",
    "SCANNING": "Scanning source code...",
    "SCORING": "Calculating score...",
    "SUMMARIZING": "Generating evaluation...",
    "GRADED": "Done",
}


def update_status(db: Session, submission: Submission, status: str, step: Optional[str] = None) -> None:
    submission.status = status
    submission.current_step_label = step or STEP_LABELS.get(status, status)
    db.add(submission)
    db.commit()
    db.refresh(submission)


def _append_error(submission: Submission, message: str) -> None:
    if submission.error_message:
        submission.error_message = f"{submission.error_message}\n{message}"
    else:
        submission.error_message = message


def run_grading_pipeline(submission_id: int, uploaded_file_path: str) -> None:
    db = SessionLocal()
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        db.close()
        return

    clone_path = ""
    raw_text = ""
    parsed_problem = {}
    github_data = {}
    run_data = {}
    assessment = {}

    try:
        update_status(db, submission, "PARSING")
        try:
            raw_text = extract_text_from_file(uploaded_file_path)
            submission.problem_raw_text = raw_text
        except Exception as exc:  # noqa: BLE001
            _append_error(submission, f"Problem file read error: {exc}")
        db.commit()

        update_status(db, submission, "PARSING", STEP_LABELS["EXTRACTING"])
        try:
            parsed_problem = parse_problem_statement_with_gemini(raw_text)
            submission.problem_parsed = parsed_problem
        except Exception as exc:  # noqa: BLE001
            parsed_problem = {
                "assignment_title": "Parse failed",
                "assignment_type": "fullstack",
                "required_features": [],
                "bonus_features": [],
                "deliverables": [],
                "keywords": [],
            }
            submission.problem_parsed = parsed_problem
            _append_error(submission, f"Gemini parse error: {exc}")
        submission.repo_owner = submission.github_url.rstrip("/").split("/")[-2] if "/" in submission.github_url else None
        submission.repo_name = submission.github_url.rstrip("/").split("/")[-1].replace(".git", "") if "/" in submission.github_url else None
        db.commit()

        update_status(db, submission, "FETCHING")
        try:
            github_data = fetch_github_metadata(os.getenv("GITHUB_TOKEN", ""), submission.github_url)
            submission.github_data = github_data
        except Exception as exc:  # noqa: BLE001
            github_data = {"error": f"GitHub check error: {exc}"}
            submission.github_data = github_data
            _append_error(submission, str(github_data["error"]))
        db.commit()

        if github_data.get("error"):
            _append_error(submission, github_data["error"])
            submission.status = "FAILED"
            submission.current_step_label = "GitHub validation failed"
            db.commit()
            return

        update_status(db, submission, "CLONING")
        clone_path = f"/tmp/{submission.repo_owner}_{submission.repo_name}_{submission.id}"
        try:
            clone_result = clone_repo(submission.github_url, clone_path)
            if not clone_result.get("success"):
                _append_error(submission, clone_result.get("output", "Clone failed"))
        except Exception as exc:  # noqa: BLE001
            _append_error(submission, f"Clone error: {exc}")
            clone_result = {"success": False}
        db.commit()

        update_status(db, submission, "RUNNING")
        try:
            run_data = run_project_checks(clone_path)
        except Exception as exc:  # noqa: BLE001
            run_data = {"project_type": "unknown", "note": "Run checks failed", "commands": []}
            _append_error(submission, f"Run checks error: {exc}")
        submission.grading_data = run_data
        db.commit()

        update_status(db, submission, "SCANNING")
        try:
            source_scan = collect_source_blob(clone_path)
            dependencies = detect_dependencies(clone_path)
            folder_tree = build_folder_tree(clone_path)
            routes = detect_routes(clone_path)
            keyword_map = keyword_hits(parsed_problem.get("keywords", []), source_scan.get("source_blob", ""))

            assessment = assess_features_with_gemini(
                parsed_problem,
                folder_tree,
                dependencies,
                source_scan.get("source_blob", ""),
                routes,
                keyword_map,
                github_data.get("language_percentages", {}),
            )

            run_data["has_tests"] = source_scan.get("has_tests", False)
            run_data["test_files_found"] = source_scan.get("test_files_found", [])
            run_data["detected_dependencies"] = dependencies
            run_data["detected_routes"] = routes
            run_data["keyword_hits"] = keyword_map
            run_data["folder_tree"] = folder_tree
            run_data["overall_completeness"] = assessment.get("overall_completeness", "incomplete")
            run_data["tech_stack_summary"] = assessment.get("tech_stack_summary", "Unknown")
            run_data["bonus_features_found"] = assessment.get("bonus_features_found", [])
        except Exception as exc:  # noqa: BLE001
            assessment = {
                "features_assessment": [],
                "bonus_features_found": [],
                "overall_completeness": "incomplete",
                "tech_stack_summary": "Scan unavailable",
            }
            run_data["has_tests"] = run_data.get("has_tests", False)
            _append_error(submission, f"Scanning error: {exc}")

        submission.features_assessment = assessment
        submission.grading_data = run_data
        db.commit()

        update_status(db, submission, "SCORING")
        try:
            score_data = calculate_scores(
                parsed_problem.get("required_features", []),
                assessment.get("features_assessment", []),
                run_data,
            )
        except Exception as exc:  # noqa: BLE001
            score_data = {"problem_solving_score": 0, "quality_score": 0, "total_score": 0}
            _append_error(submission, f"Scoring error: {exc}")
        submission.problem_solving_score = score_data["problem_solving_score"]
        submission.quality_score = score_data["quality_score"]
        submission.total_score = score_data["total_score"]
        try:
            if isinstance(run_data, dict) and isinstance(score_data, dict) and score_data.get("breakdown"):
                run_data["score_breakdown"] = score_data["breakdown"]
                submission.grading_data = run_data
        except Exception:
            pass
        db.commit()

        update_status(db, submission, "SUMMARIZING")
        try:
            ai_result = generate_final_evaluation(
                {
                    "assignment_type": parsed_problem.get("assignment_type", "unknown"),
                    "problem_raw_text": raw_text,
                    "features_assessment": assessment,
                    "tech_stack_summary": assessment.get("tech_stack_summary", "Unknown"),
                    "languages": github_data.get("language_percentages", {}),
                    "build_success": run_data.get("build_success", False),
                    "tests_passed": run_data.get("tests_passed", 0),
                    "tests_total": run_data.get("tests_total", 0),
                    "lint_errors": run_data.get("lint_errors", 0),
                    "multiple_contributors": github_data.get("multiple_contributors", False),
                    "is_fork": github_data.get("is_fork", False),
                    "overall_completeness": assessment.get("overall_completeness", "incomplete"),
                    "total_score": submission.total_score or 0,
                }
            )
        except Exception as exc:  # noqa: BLE001
            ai_result = {
                "ai_summary": f"AI evaluation failed: {exc}",
                "hire_recommendation": "Maybe",
            }
            _append_error(submission, f"Summarization error: {exc}")

        submission.ai_summary = ai_result["ai_summary"]
        submission.hire_recommendation = ai_result["hire_recommendation"]
        update_status(db, submission, "GRADED")

    except Exception as exc:  # noqa: BLE001
        submission.status = "FAILED"
        submission.current_step_label = "Pipeline error"
        submission.error_message = str(exc)
        db.commit()
    finally:
        if clone_path:
            shutil.rmtree(clone_path, ignore_errors=True)
        try:
            if uploaded_file_path and Path(uploaded_file_path).exists():
                Path(uploaded_file_path).unlink(missing_ok=True)
        except Exception:
            pass
        db.close()
