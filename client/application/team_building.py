from domain.team_builder import build_best_teams
from repositories.dataset_repository import load_config


def build_teams(selected_users):
    if len(selected_users) < 10:
        return None, "10명을 체크해주세요."

    selected = selected_users[:10]
    tier_score = load_config()

    try:
        result = build_best_teams(selected, tier_score)
    except Exception as exc:
        return None, str(exc)

    return {
        "a1": result["a1"],
        "a2": result["a2"],
        "t1_score": result["t1_score"],
        "t2_score": result["t2_score"],
        "diff": result["diff"],
        "warnings": result.get("warnings", []),
        "alerts": result.get("alerts", []),
        "balance_caution": result.get("balance_caution", False),
        "used_relaxed_rules": result.get("used_relaxed_rules", False),
    }, None
