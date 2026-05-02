import itertools
import json
import random
from pathlib import Path

from util.constants import (
    ANY_POSITION,
    DEFAULT_TIER_SCORE,
    POSITIONS,
    normalize_position_name,
    normalize_tier_name,
)

MAX_POSITION_MAPS_PER_TEAM = 40
RELAXED_POSITION_PENALTY = len(POSITIONS) + 2
ADC_POSITION = "원딜"
SUPPORT_POSITION = "서포터"


def load_config():
    path = Path("data/config.json")

    if not path.exists():
        return DEFAULT_TIER_SCORE

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("tier_score", DEFAULT_TIER_SCORE)


def get_adc_position():
    return ADC_POSITION


def get_support_position():
    return SUPPORT_POSITION


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def calc_recent_form_bonus(user):
    """Convert recent match metrics into a small bonus multiplier."""
    match_count = int(user.get("recent_match_count", 0) or 0)
    if match_count <= 0:
        return 0.0

    reliability = clamp(match_count / 10, 0.0, 1.0)
    recent_win_rate = float(user.get("recent_win_rate", 50.0) or 50.0)
    recent_kda = float(user.get("recent_kda", 2.0) or 2.0)

    win_rate_bonus = clamp((recent_win_rate - 50.0) / 100.0, -0.20, 0.20)
    kda_bonus = clamp((recent_kda - 2.5) * 0.06, -0.18, 0.18)
    return (win_rate_bonus + kda_bonus) * reliability


def _find_position_stat(user, position):
    for stat in user.get("recent_position_stats", []) or []:
        if stat.get("position") == position:
            return stat
    return None


def calc_position_fit_bonus(user, position):
    """Reward users who recently played the assigned lane often and well."""
    match_count = int(user.get("recent_match_count", 0) or 0)
    if match_count <= 0:
        return 0.0

    stat = _find_position_stat(user, position)
    if not stat:
        return 0.0

    reliability = clamp(match_count / 10, 0.0, 1.0)
    share = float(stat.get("share", 0.0) or 0.0) / 100.0
    win_rate = float(stat.get("win_rate", 50.0) or 50.0)
    share_bonus = clamp((share - 0.20) * 0.6, -0.10, 0.18)
    win_bonus = clamp((win_rate - 50.0) / 100.0, -0.08, 0.08)
    return (share_bonus + win_bonus) * reliability


def calc_power(user, tier_score):
    tier = normalize_tier_name(user["tier"])
    base = DEFAULT_TIER_SCORE.get(tier, 1)
    weight = tier_score.get(tier, 1)
    detail = int(user.get("tier_detail", 2))

    multiplier = {
        1: 1.15,
        2: 1.05,
        3: 0.95,
        4: 0.85,
    }.get(detail, 1.0)

    form_multiplier = 1.0 + calc_recent_form_bonus(user)
    return base * multiplier * weight * form_multiplier


def calc_line_power(user, tier_score, assigned_position=None):
    tier = normalize_tier_name(user["tier"])
    base = DEFAULT_TIER_SCORE.get(tier, 0)
    detail = int(user.get("tier_detail", 2))

    detail_bonus = {
        1: 0.3,
        2: 0.1,
        3: -0.1,
        4: -0.3,
    }.get(detail, 0)

    recent_kda = float(user.get("recent_kda", 2.0) or 2.0)
    recent_win_rate = float(user.get("recent_win_rate", 50.0) or 50.0)
    match_count = int(user.get("recent_match_count", 0) or 0)
    reliability = clamp(match_count / 10, 0.0, 1.0)
    form_bonus = ((recent_kda - 2.5) * 0.08) + ((recent_win_rate - 50.0) * 0.01)
    form_bonus = clamp(form_bonus * reliability, -0.4, 0.4)

    position_fit_bonus = 0.0
    if assigned_position:
        position_fit_bonus = calc_position_fit_bonus(user, assigned_position)

    return base + detail_bonus + form_bonus + position_fit_bonus


def evaluate_team(team, tier_score):
    return sum(calc_power(user, tier_score) for user in team)


def normalize_positions(user):
    return [
        normalize_position_name(position) if position else ANY_POSITION
        for position in user.get("positions", [])
    ]


def get_position_priority_penalty(user, position):
    positions = normalize_positions(user)

    if position not in positions:
        if ANY_POSITION not in positions:
            return None
        return positions.index(ANY_POSITION)

    return positions.index(position)


def get_relaxed_position_priority_penalty(user, position):
    penalty = get_position_priority_penalty(user, position)

    if penalty is not None:
        return penalty

    positions = normalize_positions(user)
    return max(len(positions), 1) + RELAXED_POSITION_PENALTY


def _position_map_sort_key(position_map):
    team_map = position_map["map"]
    return (
        position_map["position_penalty"],
        calc_bottom_pair_penalty(team_map, DEFAULT_TIER_SCORE),
    )


def _generate_position_maps(team, relaxed=False):
    maps = []

    for permutation in itertools.permutations(team, len(POSITIONS)):
        mapping = {}
        position_penalty = 0
        valid = True

        for position, user in zip(POSITIONS, permutation):
            penalty = (
                get_relaxed_position_priority_penalty(user, position)
                if relaxed
                else get_position_priority_penalty(user, position)
            )

            if penalty is None:
                valid = False
                break

            mapping[position] = user
            position_penalty += penalty

        if valid:
            maps.append({
                "map": mapping,
                "position_penalty": position_penalty,
            })

    maps.sort(key=_position_map_sort_key)
    return maps[:MAX_POSITION_MAPS_PER_TEAM]


def generate_position_maps(team):
    return _generate_position_maps(team, relaxed=False)


def generate_relaxed_position_maps(team):
    return _generate_position_maps(team, relaxed=True)


def get_line_limit(position):
    if position == ADC_POSITION:
        return 0.8

    if position in ("탑", "미드"):
        return 1.0

    return 1.2


def calc_line_diff_total(team1_map, team2_map, tier_score):
    total = 0
    for position in POSITIONS:
        total += abs(
            calc_line_power(team1_map[position], tier_score, position)
            - calc_line_power(team2_map[position], tier_score, position)
        )
    return total


def check_line_warnings(team1_map, team2_map, tier_score):
    warnings = []

    for position in POSITIONS:
        user1 = team1_map[position]
        user2 = team2_map[position]
        diff = abs(
            calc_line_power(user1, tier_score, position)
            - calc_line_power(user2, tier_score, position)
        )
        limit = get_line_limit(position)

        if diff >= limit:
            warnings.append({
                "position": position,
                "team1": {
                    "name": user1["name"],
                    "tier": user1["tier"],
                    "detail": user1.get("tier_detail", 2),
                },
                "team2": {
                    "name": user2["name"],
                    "tier": user2["tier"],
                    "detail": user2.get("tier_detail", 2),
                },
                "diff": round(diff, 2),
                "limit": limit,
            })

    return warnings


def count_line_warnings(team1_map, team2_map, tier_score):
    count = 0

    for position in POSITIONS:
        diff = abs(
            calc_line_power(team1_map[position], tier_score, position)
            - calc_line_power(team2_map[position], tier_score, position)
        )
        if diff >= get_line_limit(position):
            count += 1

    return count


def get_line_diff(position, team1_map, team2_map, tier_score):
    return abs(
        calc_line_power(team1_map[position], tier_score, position)
        - calc_line_power(team2_map[position], tier_score, position)
    )


def get_max_line_diff(team1_map, team2_map, tier_score):
    return max(
        get_line_diff(position, team1_map, team2_map, tier_score)
        for position in POSITIONS
    )


def get_position_mismatch_severity(position, team1_map, team2_map, tier_score):
    diff = get_line_diff(position, team1_map, team2_map, tier_score)
    limit = get_line_limit(position)

    if diff <= limit:
        return 0

    weight = 4 if position == ADC_POSITION else 1
    return (diff - limit) * weight


def get_line_mismatch_severity(team1_map, team2_map, tier_score):
    return sum(
        get_position_mismatch_severity(position, team1_map, team2_map, tier_score)
        for position in POSITIONS
    )


def get_adc_line_diff(team1_map, team2_map, tier_score):
    return get_line_diff(ADC_POSITION, team1_map, team2_map, tier_score)


def calc_bottom_pair_penalty(team_map, tier_score):
    adc = team_map.get(get_adc_position())
    support = team_map.get(get_support_position())

    if not adc or not support:
        return 0

    return abs(
        calc_line_power(adc, tier_score, ADC_POSITION)
        - calc_line_power(support, tier_score, SUPPORT_POSITION)
    )


def calc_team_form_diff(team1, team2):
    team1_form = sum(calc_recent_form_bonus(user) for user in team1)
    team2_form = sum(calc_recent_form_bonus(user) for user in team2)
    return abs(team1_form - team2_form)


def build_balance_alerts(selected, used_relaxed_rules, tier_score):
    alerts = []
    line_warnings = check_line_warnings(
        selected["t1_map"],
        selected["t2_map"],
        tier_score,
    )

    if used_relaxed_rules:
        alerts.append({
            "type": "balance_warning",
            "message": "조건을 완전히 만족하는 조합이 없어 완화 규칙으로 결과를 만들었습니다.",
        })

    if line_warnings:
        alerts.append({
            "type": "line_balance_warning",
            "message": f"라인 밸런스 주의: {len(line_warnings)}개 라인이 권장 범위를 벗어났습니다.",
            "details": line_warnings,
        })

    return alerts


def _build_team_candidates(users, tier_score, relaxed=False):
    best_candidates = []
    best_key = None

    for team1_tuple in itertools.combinations(users, 5):
        team1 = list(team1_tuple)
        team2 = [user for user in users if user not in team1]

        team1_maps = (
            generate_relaxed_position_maps(team1)
            if relaxed
            else generate_position_maps(team1)
        )
        team2_maps = (
            generate_relaxed_position_maps(team2)
            if relaxed
            else generate_position_maps(team2)
        )

        if not team1_maps or not team2_maps:
            continue

        team1_score = evaluate_team(team1, tier_score)
        team2_score = evaluate_team(team2, tier_score)
        team_diff = abs(team1_score - team2_score)
        team_form_diff = calc_team_form_diff(team1, team2)

        for team1_case in team1_maps:
            for team2_case in team2_maps:
                team1_map = team1_case["map"]
                team2_map = team2_case["map"]

                line_diff_total = calc_line_diff_total(team1_map, team2_map, tier_score)
                warning_count = count_line_warnings(team1_map, team2_map, tier_score)
                max_line_diff = get_max_line_diff(team1_map, team2_map, tier_score)
                adc_line_diff = get_adc_line_diff(team1_map, team2_map, tier_score)
                mismatch_severity = get_line_mismatch_severity(
                    team1_map, team2_map, tier_score
                )

                position_penalty = (
                    team1_case["position_penalty"] + team2_case["position_penalty"]
                )
                bottom_penalty = (
                    calc_bottom_pair_penalty(team1_map, tier_score)
                    + calc_bottom_pair_penalty(team2_map, tier_score)
                )

                final_score = (
                    team_diff * 10
                    + line_diff_total * 6
                    + position_penalty * 3
                    + bottom_penalty * 2
                    + team_form_diff * 8
                )

                candidate = {
                    "final_score": final_score,
                    "warning_count": warning_count,
                    "diff": team_diff,
                    "max_line_diff": max_line_diff,
                    "adc_line_diff": adc_line_diff,
                    "mismatch_severity": mismatch_severity,
                    "line_diff_total": line_diff_total,
                    "position_penalty": position_penalty,
                    "bottom_penalty": bottom_penalty,
                    "team_form_diff": team_form_diff,
                    "t1_map": team1_map,
                    "t2_map": team2_map,
                    "t1_score": team1_score,
                    "t2_score": team2_score,
                }

                candidate_key = (
                    warning_count,
                    adc_line_diff,
                    max_line_diff,
                    mismatch_severity,
                    team_form_diff,
                    final_score,
                )

                if best_key is None or candidate_key < best_key:
                    best_key = candidate_key
                    best_candidates = [candidate]
                elif candidate_key == best_key:
                    best_candidates.append(candidate)

    return best_candidates


def build_best_teams(users, tier_score=None):
    if tier_score is None:
        tier_score = load_config()

    if len(users) != 10:
        raise Exception("5:5 팀 생성을 위해 선택된 유저는 반드시 10명이어야 합니다.")

    best_candidates = _build_team_candidates(users, tier_score, relaxed=False)
    used_relaxed_rules = False

    if not best_candidates:
        best_candidates = _build_team_candidates(users, tier_score, relaxed=True)
        used_relaxed_rules = True

    if not best_candidates:
        raise Exception(
            "팀 조합을 생성할 수 없습니다. 유저 정보 또는 포지션 데이터가 올바른지 확인해주세요."
        )

    selected = random.choice(best_candidates)
    warnings = check_line_warnings(
        selected["t1_map"],
        selected["t2_map"],
        tier_score,
    )

    return {
        "a1": selected["t1_map"],
        "a2": selected["t2_map"],
        "t1_score": selected["t1_score"],
        "t2_score": selected["t2_score"],
        "diff": selected["diff"],
        "warnings": warnings,
        "alerts": build_balance_alerts(selected, used_relaxed_rules, tier_score),
        "balance_caution": used_relaxed_rules or bool(warnings),
        "used_relaxed_rules": used_relaxed_rules,
    }


def format_team(team_map):
    return "\n".join(
        f"{position} - {user['name']} ({user['tier']}/{user.get('tier_detail', 2)})"
        for position, user in team_map.items()
    )
