from datetime import datetime
from typing import Any, Dict

from github import Github


def _language_percentages(language_bytes: Dict[str, int]) -> Dict[str, float]:
    # PyGithub usually returns ints, but we defensively coerce to int to avoid
    # crashing the whole pipeline on unexpected API/serialization quirks.
    normalized: Dict[str, int] = {}
    for k, v in (language_bytes or {}).items():
        try:
            normalized[str(k)] = int(v)  # handles stringified numbers too
        except Exception:
            continue

    total = sum(normalized.values()) or 1
    return {k: round((v / total) * 100, 2) for k, v in normalized.items()}


def fetch_github_metadata(github_token: str, github_url: str) -> Dict[str, Any]:
    parts = github_url.rstrip("/").split("/")
    if len(parts) < 2:
        return {"error": "Invalid GitHub URL"}

    owner = parts[-2]
    repo_name = parts[-1].replace(".git", "")
    full_name = f"{owner}/{repo_name}"

    gh = Github(github_token)
    try:
        repo = gh.get_repo(full_name)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Repo not found or inaccessible: {exc}", "repo_owner": owner, "repo_name": repo_name}

    if repo.private:
        return {"error": "Repo exists but is private", "repo_owner": owner, "repo_name": repo_name}

    contributors = list(repo.get_contributors())
    languages = repo.get_languages()

    return {
        "repo_owner": owner,
        "repo_name": repo_name,
        "repo_exists": True,
        "is_public": not repo.private,
        "created_at": repo.created_at.isoformat() if isinstance(repo.created_at, datetime) else str(repo.created_at),
        "last_push_at": repo.pushed_at.isoformat() if isinstance(repo.pushed_at, datetime) else str(repo.pushed_at),
        "default_branch": repo.default_branch,
        "contributor_count": len(contributors),
        "multiple_contributors": len(contributors) > 1,
        "is_fork": repo.fork,
        "languages": languages,
        "language_percentages": _language_percentages(languages),
    }
