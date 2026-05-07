from domain.team_builder import build_best_teams
from domain.constants import DEFAULT_TIER_SCORE
from repositories.dataset_repository import (
    load_build_preferences,
    load_build_weights,
    load_config,
)


def build_teams(selected_users):
    if len(selected_users) < 10:
        return None, "10명을 체크해주세요."

    invalid_users = []
    for user in selected_users[:10]:
        tier = str(user.get("tier") or "").strip()
        detail = user.get("tier_detail")
        if tier not in DEFAULT_TIER_SCORE or detail not in {1, 2, 3, 4}:
            invalid_users.append(user.get("name") or "이름 없음")

    if invalid_users:
        joined_names = ", ".join(invalid_users)
        return None, (
            "팀빌딩 전 티어와 랭크를 모두 입력해주세요.\n"
            f"대상 유저: {joined_names}"
        )

    selected = selected_users[:10]
    tier_score = load_config()
    build_weights = load_build_weights()
    build_preferences = load_build_preferences()

    try:
        result = build_best_teams(
            selected,
            tier_score,
            build_weights,
            build_preferences,
        )
    except Exception as exc:
        return None, str(exc)

    return {
        "a1": result["a1"],
        "a2": result["a2"],
        "t1_score": result["t1_score"],
        "t2_score": result["t2_score"],
        "t1_score_tooltip": result.get("t1_score_tooltip", ""),
        "t2_score_tooltip": result.get("t2_score_tooltip", ""),
        "score_breakdown_rows": result.get("score_breakdown_rows", []),
        "diff": result["diff"],
        "warnings": result.get("warnings", []),
        "alerts": result.get("alerts", []),
        "balance_caution": result.get("balance_caution", False),
        "used_relaxed_rules": result.get("used_relaxed_rules", False),
    }, None
