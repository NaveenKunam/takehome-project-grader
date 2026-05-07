import json
import os
import re
from typing import Any, Dict

import docx
from pypdf import PdfReader

from backend.grader.groq_client import groq_chat_completion

def extract_text_from_file(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if file_path.lower().endswith(".docx"):
        document = docx.Document(file_path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    raise ValueError("Unsupported file type. Please upload PDF or DOCX.")


def _strip_json_fences(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def _extract_json_object(raw: str) -> str:
    text = _strip_json_fences(raw)
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    if start == -1:
        return text

    depth = 0
    in_string = False
    escaped = False
    for idx, ch in enumerate(text[start:], start=start):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return text


def _normalize_problem_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "assignment_title": str(data.get("assignment_title", "Untitled assignment")),
        "assignment_type": data.get("assignment_type", "fullstack") if data.get("assignment_type") in {"frontend", "backend", "fullstack"} else "fullstack",
        "required_features": list(data.get("required_features", [])) if isinstance(data.get("required_features", []), list) else [],
        "bonus_features": list(data.get("bonus_features", [])) if isinstance(data.get("bonus_features", []), list) else [],
        "deliverables": list(data.get("deliverables", [])) if isinstance(data.get("deliverables", []), list) else [],
        "keywords": list(data.get("keywords", [])) if isinstance(data.get("keywords", []), list) else [],
    }


def _heuristic_parse_problem(extracted_text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    title = lines[0][:120] if lines else "Assignment"

    lower_text = extracted_text.lower()
    assignment_type = "fullstack"
    if any(token in lower_text for token in ["react", "frontend", "ui", "tailwind", "vite"]):
        assignment_type = "frontend"
    if any(token in lower_text for token in ["fastapi", "flask", "django", "backend", "api", "database"]):
        assignment_type = "backend" if assignment_type != "frontend" else "fullstack"

    candidate_keywords = [
        "auth",
        "jwt",
        "login",
        "crud",
        "pagination",
        "database",
        "api",
        "react",
        "fastapi",
        "docker",
        "testing",
        "pytest",
    ]
    keywords = [kw for kw in candidate_keywords if kw in lower_text]

    required_features = []
    for line in lines:
        if line.startswith(("-", "*")) or re.match(r"^\d+[\.\)]", line):
            cleaned = re.sub(r"^[-*\d\.\)\s]+", "", line).strip()
            if len(cleaned) > 4:
                required_features.append(cleaned[:200])
        if len(required_features) >= 8:
            break

    return {
        "assignment_title": title,
        "assignment_type": assignment_type,
        "required_features": required_features,
        "bonus_features": [],
        "deliverables": [],
        "keywords": keywords,
    }


def parse_problem_statement_with_gemini(extracted_text: str) -> Dict[str, Any]:
    if not extracted_text.strip():
        return {
            "assignment_title": "Empty or unreadable document",
            "assignment_type": "fullstack",
            "required_features": [],
            "bonus_features": [],
            "deliverables": [],
            "keywords": [],
            "raw_response": "No text could be extracted from uploaded file",
        }

    # Use Groq if available; otherwise fall back to heuristics.
    system_prompt = "You are a technical assessor. Return ONLY valid JSON. No markdown, no backticks, no extra text."
    user_prompt = f"""Extract the following from this take-home assignment problem statement:
{{
  "assignment_title": "string",
  "assignment_type": "frontend | backend | fullstack",
  "required_features": ["string"],
  "bonus_features": ["string"],
  "deliverables": ["string"],
  "keywords": ["string"]
}}

Problem statement:
{extracted_text}
"""

    model_name = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    try:
        text = groq_chat_completion(system_prompt, user_prompt, model=model_name, temperature=0.1, max_tokens=1200)
        cleaned = _extract_json_object(text)
        parsed = json.loads(cleaned)
        normalized = _normalize_problem_schema(parsed if isinstance(parsed, dict) else {})
        normalized["raw_response"] = text
        normalized["model_used"] = model_name
        return normalized
    except Exception:
        parsed = _heuristic_parse_problem(extracted_text)
        normalized = _normalize_problem_schema(parsed if isinstance(parsed, dict) else {})
        normalized["raw_response"] = "Heuristic parser (Groq unavailable)"
        normalized["model_used"] = "heuristic-v1"
        return normalized
