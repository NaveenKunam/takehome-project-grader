from typing import Any, Dict, List


def calculate_scores(required_features: List[str], feature_assessment: List[Dict[str, Any]], run_data: Dict[str, Any]) -> Dict[str, int]:
    breakdown: Dict[str, Any] = {"problem_solving": [], "quality": []}

    problem_solving_score = 0.0
    if required_features:
        points_per_feature = 50 / len(required_features)
        status_by_feature = {item.get("feature"): item.get("status", "missing") for item in feature_assessment}
        implemented = 0
        partial = 0
        missing = 0
        for feature in required_features:
            status = status_by_feature.get(feature, "missing")
            if status == "implemented":
                problem_solving_score += points_per_feature
                implemented += 1
            elif status == "partial":
                problem_solving_score += points_per_feature / 2
                partial += 1
            else:
                missing += 1

        breakdown["problem_solving"].append(
            {
                "label": "Requirement coverage (from problem document)",
                "awarded": int(round(problem_solving_score)),
                "possible": 50,
                "evidence": f"implemented={implemented}, partial={partial}, missing={missing}, total={len(required_features)}",
            }
        )
    else:
        # Generic rubric when the uploaded document doesn't enumerate requirements.
        # This is intentionally tech-stack agnostic and uses signals we can reliably
        # extract from a repo and automated checks.
        project_type = run_data.get("project_type", "unknown")
        detected_routes = run_data.get("detected_routes", []) or []
        detected_dependencies = run_data.get("detected_dependencies", []) or []
        overall = str(run_data.get("overall_completeness", "unknown") or "unknown")

        # 0–10: recognizable project structure
        structure_awarded = 10 if project_type != "unknown" else 0
        breakdown["problem_solving"].append(
            {
                "label": "Recognizable project structure",
                "awarded": structure_awarded,
                "possible": 10,
                "evidence": f"project_type={project_type}",
            }
        )
        problem_solving_score += structure_awarded

        # 0–15: route / endpoint / UI navigation signals
        route_count = len(detected_routes)
        if route_count == 0:
            routes_awarded = 0
        elif route_count <= 2:
            routes_awarded = 5
        elif route_count <= 5:
            routes_awarded = 10
        else:
            routes_awarded = 15
        breakdown["problem_solving"].append(
            {
                "label": "Route / endpoint signals",
                "awarded": routes_awarded,
                "possible": 15,
                "evidence": f"detected_routes={route_count}",
            }
        )
        problem_solving_score += routes_awarded

        # 0–10: dependency footprint
        deps_awarded = 10 if len(detected_dependencies) >= 3 else (5 if len(detected_dependencies) >= 1 else 0)
        breakdown["problem_solving"].append(
            {
                "label": "Dependency footprint",
                "awarded": deps_awarded,
                "possible": 10,
                "evidence": f"detected_dependencies={len(detected_dependencies)}",
            }
        )
        problem_solving_score += deps_awarded

        # 0–15: implementation evidence / completeness signal
        completeness_map = {
            "complete": 15,
            "mostly_complete": 12,
            "incomplete": 6,
            "barely_started": 2,
        }
        completeness_awarded = completeness_map.get(overall, 4)
        breakdown["problem_solving"].append(
            {
                "label": "Implementation evidence (completeness)",
                "awarded": completeness_awarded,
                "possible": 15,
                "evidence": f"overall_completeness={overall}",
            }
        )
        problem_solving_score += completeness_awarded

    quality_score = 0
    if run_data.get("project_type") != "unknown":
        if run_data.get("build_success"):
            quality_score += 15
            breakdown["quality"].append({"label": "Build succeeds", "awarded": 15, "possible": 15, "evidence": "build_success=true"})
        else:
            breakdown["quality"].append({"label": "Build succeeds", "awarded": 0, "possible": 15, "evidence": "build_success=false"})

        if run_data.get("has_tests"):
            quality_score += 10
            breakdown["quality"].append({"label": "Tests exist", "awarded": 10, "possible": 10, "evidence": "has_tests=true"})
        else:
            breakdown["quality"].append({"label": "Tests exist", "awarded": 0, "possible": 10, "evidence": "has_tests=false"})

        tests_total = run_data.get("tests_total", 0)
        tests_failed = run_data.get("tests_failed", 0)
        if tests_total > 0 and tests_failed == 0:
            quality_score += 15
            breakdown["quality"].append({"label": "Tests pass", "awarded": 15, "possible": 15, "evidence": f"tests_failed={tests_failed}, tests_total={tests_total}"})
        else:
            breakdown["quality"].append({"label": "Tests pass", "awarded": 0, "possible": 15, "evidence": f"tests_failed={tests_failed}, tests_total={tests_total}"})

        lint_ok = run_data.get("lint_errors", 999) < 10 or run_data.get("pylint_score", 0.0) >= 6.0
        if lint_ok:
            quality_score += 10
            breakdown["quality"].append(
                {
                    "label": "Lint quality OK",
                    "awarded": 10,
                    "possible": 10,
                    "evidence": f"lint_errors={run_data.get('lint_errors')}, pylint_score={run_data.get('pylint_score')}",
                }
            )
        else:
            breakdown["quality"].append(
                {
                    "label": "Lint quality OK",
                    "awarded": 0,
                    "possible": 10,
                    "evidence": f"lint_errors={run_data.get('lint_errors')}, pylint_score={run_data.get('pylint_score')}",
                }
            )

    problem_solving_score = int(round(problem_solving_score))
    quality_score = int(round(quality_score))
    total_score = problem_solving_score + quality_score

    return {
        "problem_solving_score": problem_solving_score,
        "quality_score": quality_score,
        "total_score": total_score,
        "breakdown": breakdown,
    }
