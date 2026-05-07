import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def run_command(cmd: List[str], cwd: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(cmd, timeout=60, capture_output=True, text=True, cwd=cwd)
        return {
            "command": " ".join(cmd),
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output": f"{result.stdout}\n{result.stderr}",
        }
    except subprocess.TimeoutExpired:
        return {
            "command": " ".join(cmd),
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": "Command timed out",
            "output": "Command timed out",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "command": " ".join(cmd),
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
            "output": str(exc),
        }


def detect_project_type(repo_path: str) -> str:
    root = Path(repo_path)
    if (root / "package.json").exists():
        return "node"
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
        return "python"
    if (root / "pom.xml").exists():
        return "java"
    if (root / "go.mod").exists():
        return "go"
    if (root / "Gemfile").exists():
        return "ruby"
    return "unknown"


def clone_repo(github_url: str, target_path: str) -> Dict[str, Any]:
    if os.path.exists(target_path):
        shutil.rmtree(target_path, ignore_errors=True)
    return run_command(["git", "clone", github_url, "--depth=50", target_path], cwd="/tmp")


def run_project_checks(repo_path: str) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "project_type": detect_project_type(repo_path),
        "commands": [],
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_total": 0,
        "build_success": False,
        "lint_errors": 999,
        "lint_warnings": 0,
        "pylint_score": 0.0,
        "note": "",
    }

    project_type = results["project_type"]
    if project_type == "unknown":
        results["note"] = "Unknown project type, manual review required"
        return results

    if project_type == "node":
        install = run_command(["npm", "install"], cwd=repo_path)
        results["commands"].append({"name": "install", **install})

        test = run_command(["npm", "test", "--", "--watchAll=false", "--passWithNoTests"], cwd=repo_path)
        results["commands"].append({"name": "test", **test})
        output = test["output"]
        if "Tests:" in output:
            try:
                failed_match = output.split("failed,")[0].split()[-1] if "failed," in output else "0"
                passed_match = output.split("passed,")[0].split()[-1] if "passed," in output else "0"
                total_match = output.split("total")[0].split()[-1] if "total" in output else "0"
                results["tests_failed"] = int(failed_match) if failed_match.isdigit() else 0
                results["tests_passed"] = int(passed_match) if passed_match.isdigit() else 0
                results["tests_total"] = int(total_match) if total_match.isdigit() else results["tests_passed"] + results["tests_failed"]
            except Exception:
                pass

        build_success = False
        pkg_json = Path(repo_path) / "package.json"
        try:
            pkg_data = json.loads(pkg_json.read_text())
            if "build" in pkg_data.get("scripts", {}):
                build = run_command(["npm", "run", "build"], cwd=repo_path)
                results["commands"].append({"name": "build", **build})
                build_success = build["success"]
        except Exception:
            pass
        results["build_success"] = build_success

        lint = run_command(["npx", "eslint", ".", "--ext", ".js,.jsx,.ts,.tsx"], cwd=repo_path)
        results["commands"].append({"name": "lint", **lint})
        text = lint["output"].lower()
        results["lint_errors"] = text.count("error")
        results["lint_warnings"] = text.count("warning")

    if project_type == "python":
        req = Path(repo_path) / "requirements.txt"
        if req.exists():
            install = run_command(["pip", "install", "-r", "requirements.txt"], cwd=repo_path)
            results["commands"].append({"name": "install", **install})

        test = run_command(["pytest", "--tb=short", "-q"], cwd=repo_path)
        results["commands"].append({"name": "test", **test})
        for line in test["output"].splitlines():
            if " passed" in line or " failed" in line:
                parts = line.split(",")
                for p in parts:
                    t = p.strip()
                    if t.endswith(" passed"):
                        results["tests_passed"] = int(t.split()[0])
                    if t.endswith(" failed"):
                        results["tests_failed"] = int(t.split()[0])
        results["tests_total"] = results["tests_passed"] + results["tests_failed"]

        python_files = [
            str(path.relative_to(repo_path))
            for path in Path(repo_path).rglob("*.py")
            if all(not part.startswith(".") for part in path.parts)
        ][:20]
        pylint_cmd = ["pylint", "--score=yes", "--disable=C0114,C0115,C0116", *python_files] if python_files else [
            "pylint",
            "--score=yes",
            "--disable=C0114,C0115,C0116",
            ".",
        ]
        pylint = run_command(pylint_cmd, cwd=repo_path)
        results["commands"].append({"name": "pylint", **pylint})
        for line in pylint["output"].splitlines():
            if "Your code has been rated at" in line:
                score = line.split("rated at")[-1].split("/")[0].strip()
                try:
                    results["pylint_score"] = float(score)
                except ValueError:
                    pass

        flake8 = run_command(["flake8", ".", "--count", "--max-line-length=120"], cwd=repo_path)
        results["commands"].append({"name": "flake8", **flake8})
        try:
            results["lint_errors"] = int((flake8["stdout"].strip() or "0").splitlines()[-1])
        except Exception:
            results["lint_errors"] = flake8["output"].lower().count(".py:")

        results["build_success"] = True

    return results
