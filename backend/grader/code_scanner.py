import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Set

from backend.grader.groq_client import groq_chat_completion
EXCLUDED_DIRS = {"node_modules", ".git", "__pycache__", "dist", "build", "venv", ".venv"}
SOURCE_EXTS = {".js", ".jsx", ".ts", ".tsx", ".py", ".java"}
CONFIG_FILES = {"package.json", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "build.gradle.kts"}


def _is_excluded_file(path: Path) -> bool:
    name = path.name
    if name.endswith(".min.js") or name.endswith(".lock"):
        return True
    if path.stat().st_size > 50 * 1024:
        return True
    return False


def build_folder_tree(repo_path: str, max_depth: int = 3) -> str:
    root = Path(repo_path)
    lines: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = 0 if str(rel) == "." else len(rel.parts)
        if depth > max_depth:
            continue
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        indent = "  " * depth
        lines.append(f"{indent}{rel if str(rel) != '.' else root.name}/")
        for f in sorted(filenames)[:20]:
            lines.append(f"{indent}  {f}")
    return "\n".join(lines)


def collect_source_blob(repo_path: str) -> Dict[str, Any]:
    files_content: List[str] = []
    files_seen = 0
    test_files: List[str] = []

    for dirpath, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        for filename in filenames:
            path = Path(dirpath) / filename
            if _is_excluded_file(path):
                continue

            rel = str(path.relative_to(repo_path))
            lower_rel = rel.lower()
            if any(t in lower_rel for t in ["/test", "/tests"]) or re.search(r"test_.*\.py$|.*_test\.py$|.*\.(test|spec)\.(js|ts)$|.*test(s)?\.java$|.*tests?\.java$", lower_rel):
                test_files.append(rel)

            if files_seen >= 50:
                continue

            if path.suffix in SOURCE_EXTS or path.name in CONFIG_FILES:
                try:
                    content = path.read_text(errors="ignore")
                except Exception:
                    continue
                first_200 = "\n".join(content.splitlines()[:200])
                files_content.append(f"\n# FILE: {rel}\n{first_200}")
                files_seen += 1

    blob = "\n".join(files_content)
    return {"source_blob": blob, "test_files_found": test_files, "has_tests": len(test_files) > 0}


def detect_dependencies(repo_path: str) -> List[str]:
    deps: Set[str] = set()
    package_json = Path(repo_path) / "package.json"
    req_file = Path(repo_path) / "requirements.txt"

    if package_json.exists():
        try:
            data = json.loads(package_json.read_text())
            deps.update(data.get("dependencies", {}).keys())
            deps.update(data.get("devDependencies", {}).keys())
        except Exception:
            pass

    if req_file.exists():
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[<>=~!]", line)[0].strip()
            if pkg:
                deps.add(pkg)

    pom_file = Path(repo_path) / "pom.xml"
    if pom_file.exists():
        try:
            tree = ET.parse(pom_file)
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            for dep in tree.findall(".//m:dependency", ns) or tree.findall(".//dependency"):
                artifact = dep.find("m:artifactId", ns) or dep.find("artifactId")
                if artifact is not None and artifact.text:
                    deps.add(artifact.text.strip())
        except Exception:
            pass

    return sorted(deps)


def detect_routes(repo_path: str) -> List[str]:
    patterns = [r"app\.get", r"app\.post", r"app\.put", r"app\.delete", r"router\.get", r"@app\.route", r"@router\.get", r"@app\.get", r"<Route", r"useNavigate", r"Link to=", r"@GetMapping", r"@PostMapping", r"@PutMapping", r"@DeleteMapping", r"@RequestMapping"]
    matches: List[str] = []
    for dirpath, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix not in SOURCE_EXTS:
                continue
            try:
                text = path.read_text(errors="ignore")
            except Exception:
                continue
            for p in patterns:
                if re.search(p, text):
                    matches.append(f"{path.name}:{p}")
            if len(matches) >= 20:
                return matches[:20]
    return matches[:20]


def keyword_hits(keywords: List[str], source_blob: str) -> Dict[str, bool]:
    blob = source_blob.lower()
    return {kw: kw.lower() in blob for kw in keywords}


def assess_features_with_gemini(
    parsed_problem: Dict[str, Any],
    folder_tree: str,
    detected_dependencies: List[str],
    source_blob: str,
    detected_routes: List[str],
    keyword_map: Dict[str, bool],
    languages: Dict[str, Any],
) -> Dict[str, Any]:
    # Prefer Groq if configured; fall back to heuristics if unavailable.
    blob = (source_blob or "").lower()
    deps = {d.lower() for d in (detected_dependencies or [])}

    def _feature_tokens(feature: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9_]{4,}", (feature or "").lower())
        stop = {"with", "that", "this", "have", "from", "into", "your", "must", "should", "able", "user", "users"}
        return [t for t in tokens if t not in stop][:8]

    def _evidence_for(tokens: List[str]) -> str:
        hits = [t for t in tokens if t in blob or t in deps]
        if hits:
            return f"Matched keywords: {', '.join(hits[:6])}"
        return "No keyword evidence found in scanned files"

    features = parsed_problem.get("required_features", []) or []

    model_name = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    try:
        system_prompt = "You are a senior engineer reviewing a take-home submission. Return ONLY valid JSON, no markdown."
        user_prompt = f"""Problem statement requirements:
{json.dumps(parsed_problem)}

Candidate's folder structure:
{folder_tree}

Detected dependencies:
{detected_dependencies}

Source code (combined, truncated):
{(source_blob or '')[:8000]}

Detected routes/endpoints:
{detected_routes}

Keyword hits:
{json.dumps(keyword_map)}

Candidate's detected tech stack:
{json.dumps(languages)}

For each required feature assess implementation status.
Return JSON:
{{
  "features_assessment": [
    {{
      "feature": "string",
      "status": "implemented | partial | missing | unclear",
      "evidence": "string"
    }}
  ],
  "bonus_features_found": ["string"],
  "overall_completeness": "complete | mostly_complete | incomplete | barely_started",
  "tech_stack_summary": "string"
}}"""
        text = groq_chat_completion(system_prompt, user_prompt, model=model_name, temperature=0.2, max_tokens=1400)
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        if isinstance(data, dict) and "features_assessment" in data:
            data["analysis_mode"] = f"groq:{model_name}"
            return data
    except Exception:
        pass

    assessed = []
    implemented = 0
    partial = 0

    for f in features:
        tokens = _feature_tokens(str(f))
        hit_count = sum(1 for t in tokens if t in blob or t in deps)
        status = "missing"
        if hit_count >= 3 or (tokens and str(f).lower() in blob):
            status = "implemented"
            implemented += 1
        elif hit_count >= 1:
            status = "partial"
            partial += 1
        assessed.append({"feature": str(f), "status": status, "evidence": _evidence_for(tokens)})

    total = len(features) or 1
    ratio = implemented / total
    overall = "incomplete"
    if ratio >= 0.85:
        overall = "complete"
    elif ratio >= 0.55:
        overall = "mostly_complete"
    elif implemented == 0 and partial <= 1:
        overall = "barely_started"

    lang_keys = list((languages or {}).keys())
    summary_bits = []
    if lang_keys:
        summary_bits.append(f"Languages: {', '.join(lang_keys[:5])}")
    if detected_dependencies:
        summary_bits.append(f"Dependencies: {', '.join(detected_dependencies[:10])}")
    if detected_routes:
        summary_bits.append(f"Route signals: {', '.join(detected_routes[:6])}")
    tech_stack_summary = " | ".join(summary_bits) if summary_bits else "Unable to infer tech stack from scan"

    return {
        "features_assessment": assessed,
        "bonus_features_found": [],
        "overall_completeness": overall,
        "tech_stack_summary": tech_stack_summary,
        "analysis_mode": "heuristic-v1",
    }
