import json
import os
from typing import Any, Dict

from backend.grader.groq_client import groq_chat_completion

def generate_final_evaluation(payload: Dict[str, Any]) -> Dict[str, str]:
    # Prefer Groq if configured; fall back to deterministic summary if unavailable.
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    try:
        system_prompt = (
            "You are a senior software engineer evaluating a candidate's take-home assignment. "
            "Be direct, specific, and honest. Do not use filler phrases or be overly positive."
        )
        user_prompt = f"""Assignment Type: {payload.get('assignment_type', 'unknown')}

Problem Statement (truncated):
{(payload.get('problem_raw_text') or '')[:1200]}

Feature Assessment:
{json.dumps(payload.get('features_assessment', {}))}

Candidate's Tech Stack:
{payload.get('tech_stack_summary', 'Unknown')}
Languages detected: {json.dumps(payload.get('languages', {}))}

Automated Results:
- Build: {payload.get('build_success')}
- Tests: {payload.get('tests_passed', 0)}/{payload.get('tests_total', 0)} passed
- Lint errors: {payload.get('lint_errors', 0)}
- Multiple contributors: {payload.get('multiple_contributors', False)}
- Is fork: {payload.get('is_fork', False)}
- Overall completeness: {payload.get('overall_completeness', 'unknown')}

Total Score: {payload.get('total_score', 0)}/100

Write evaluation with exactly these 5 sections.
Each section 2-4 sentences, specific, no fluff.

1. Problem Solving
2. Tech Stack Choice
3. Code Quality
4. Red Flags
5. Hire Recommendation
Start with exactly one of: Strong Yes / Yes / Maybe / No
Then 2-3 sentences of reasoning tied to the problem.
"""
        text = groq_chat_completion(system_prompt, user_prompt, model=model_name, temperature=0.2, max_tokens=900).strip()
        rec = "Maybe"
        if text.startswith("Strong Yes") or "\nStrong Yes" in text:
            rec = "Strong Yes"
        elif text.startswith("Yes") or "\nYes" in text:
            rec = "Yes"
        elif text.startswith("No") or "\nNo" in text:
            rec = "No"
        elif "Maybe" in text:
            rec = "Maybe"
        return {"ai_summary": text, "hire_recommendation": rec}
    except Exception:
        pass

    # Deterministic summary from pipeline signals.
    total_score = int(payload.get("total_score", 0) or 0)
    build_success = bool(payload.get("build_success", False))
    tests_passed = int(payload.get("tests_passed", 0) or 0)
    tests_total = int(payload.get("tests_total", 0) or 0)
    lint_errors = int(payload.get("lint_errors", 0) or 0)
    overall = str(payload.get("overall_completeness", "unknown") or "unknown")
    tech_stack = str(payload.get("tech_stack_summary", "Unknown") or "Unknown")

    if total_score >= 85 and build_success and (tests_total == 0 or tests_passed == tests_total) and lint_errors < 10:
        rec = "Strong Yes"
    elif total_score >= 70 and build_success:
        rec = "Yes"
    elif total_score >= 45:
        rec = "Maybe"
    else:
        rec = "No"

    problem_solving_line = f"Feature completeness is reported as '{overall}'. The score was {total_score}/100, based on detected feature evidence and automated checks."
    tech_stack_line = f"Detected tech stack signals: {tech_stack}."
    quality_line = f"Build: {'pass' if build_success else 'fail'}. Tests: {tests_passed}/{tests_total} passed. Lint errors reported: {lint_errors}."

    red_flags = []
    if not build_success:
        red_flags.append("Build failed or was not detected")
    if tests_total > 0 and tests_passed < tests_total:
        red_flags.append("Some tests failed")
    if lint_errors >= 25:
        red_flags.append("High lint error count")
    if str(payload.get("is_fork", False)).lower() in {"true", "1"} or payload.get("is_fork") is True:
        red_flags.append("Repository is a fork (check originality)")
    if str(payload.get("multiple_contributors", False)).lower() in {"true", "1"} or payload.get("multiple_contributors") is True:
        red_flags.append("Multiple contributors (confirm ownership of work)")

    red_flags_text = "No major automated red flags were detected." if not red_flags else "Red flags: " + "; ".join(red_flags) + "."
    hire_line = f"{rec}\nBased on the automated signals, this is a {rec.lower()} recommendation. Use this as a starting point and spot-check the highest-impact features and architecture decisions."

    text = "\n\n".join(
        [
            "1. Problem Solving\n" + problem_solving_line,
            "2. Tech Stack Choice\n" + tech_stack_line,
            "3. Code Quality\n" + quality_line,
            "4. Red Flags\n" + red_flags_text,
            "5. Hire Recommendation\n" + hire_line,
        ]
    )

    return {"ai_summary": text, "hire_recommendation": rec}
