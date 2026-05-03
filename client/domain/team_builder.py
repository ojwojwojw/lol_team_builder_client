import itertools
import json
import random
from pathlib import Path

from domain.constants import (
    ANY_POSITION,
    DEFAULT_BUILD_WEIGHTS,
    DEFAULT_TIER_SCORE,
    POSITIONS,
    normalize_position_name,
    normalize_tier_name,
)

CLIENT_ROOT = Path(__file__).resolve().parents[1]

# 한 팀에서 포지션 배치를 전부 탐색하면 경우의 수가 빠르게 커지므로,
# 우선순위가 좋은 배치만 상위 N개로 잘라서 조합 탐색량을 줄인다.
MAX_POSITION_MAPS_PER_TEAM = 24
RELAXED_POSITION_PENALTY = len(POSITIONS) + 2
ADC_POSITION = POSITIONS[3]
SUPPORT_POSITION = POSITIONS[4]

DETAIL_MULTIPLIER_MAP = {
    1: 1.15,
    2: 1.05,
    3: 0.95,
    4: 0.85,
}

DETAIL_BONUS_MAP = {
    1: 0.3,
    2: 0.1,
    3: -0.1,
    4: -0.3,
}

LINE_LIMIT_MAP = {
    ADC_POSITION: 0.8,
    POSITIONS[0]: 1.0,
    POSITIONS[2]: 1.0,
}

LINE_MISMATCH_WEIGHT_MAP = {
    ADC_POSITION: 4,
}

POSITION_INDEX_MAP = {position: index for index, position in enumerate(POSITIONS)}


def load_config():
    """클라이언트 설정 파일에서 티어 가중치 맵을 읽는다."""
    path = CLIENT_ROOT / "data" / "config.json"

    if not path.exists():
        return DEFAULT_TIER_SCORE

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("tier_score", DEFAULT_TIER_SCORE)


def get_adc_position():
    """원딜 포지션 라벨을 반환한다."""
    return ADC_POSITION


def get_support_position():
    """서포터 포지션 라벨을 반환한다."""
    return SUPPORT_POSITION


def clamp(value, minimum, maximum):
    """숫자를 지정된 최소/최대 범위 안으로 고정한다."""
    return max(minimum, min(maximum, value))


def calc_recent_form_bonus(user):
    """최근 전적의 승률/KDA를 바탕으로 작은 추가 배율을 계산한다."""
    cached = user.get("_recent_form_bonus")
    if cached is not None:
        return cached

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
    """최근 포지션 통계 목록에서 특정 포지션 통계를 찾는다."""
    stat_map = user.get("_position_stat_map")
    if stat_map is not None:
        return stat_map.get(position)

    for stat in user.get("recent_position_stats", []) or []:
        if stat.get("position") == position:
            return stat
    return None


def calc_position_fit_bonus(user, position):
    """배정 포지션 숙련도와 최근 성과를 반영한 라인 적합 보너스를 계산한다."""
    position_bonus_map = user.get("_position_fit_bonus_map")
    if position_bonus_map is not None and position in position_bonus_map:
        return position_bonus_map[position]

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
    """팀 총점 계산에 쓰이는 유저의 종합 전투력을 계산한다."""
    cached = user.get("_power")
    if cached is not None:
        return cached

    tier = normalize_tier_name(user["tier"])
    base = DEFAULT_TIER_SCORE.get(tier, 1)
    weight = tier_score.get(tier, 1)
    detail = int(user.get("tier_detail", 2))
    detail_multiplier = DETAIL_MULTIPLIER_MAP.get(detail, 1.0)
    form_bonus = calc_recent_form_bonus(user)
    form_multiplier = 1.0 + form_bonus
    return base * detail_multiplier * weight * form_multiplier


def calc_line_power(user, tier_score, assigned_position=None):
    """라인 대결 비교용 점수를 계산한다."""
    line_power_map = user.get("_line_power_by_position")
    if assigned_position and line_power_map is not None:
        cached = line_power_map.get(assigned_position)
        if cached is not None:
            return cached

    tier = normalize_tier_name(user["tier"])
    base = DEFAULT_TIER_SCORE.get(tier, 0)
    detail = int(user.get("tier_detail", 2))
    detail_bonus = DETAIL_BONUS_MAP.get(detail, 0.0)

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
    """한 팀의 총 전투력 합계를 계산한다."""
    return sum(calc_power(user, tier_score) for user in team)


def normalize_positions(user):
    """유저의 선호 포지션 리스트를 정규화한다."""
    cached = user.get("_normalized_positions")
    if cached is not None:
        return cached

    return [
        normalize_position_name(position) if position else ANY_POSITION
        for position in user.get("positions", [])
    ]


def get_position_priority_penalty(user, position):
    """엄격 모드에서 포지션 배정 우선순위 페널티를 계산한다."""
    positions = normalize_positions(user)

    if position not in positions:
        if ANY_POSITION not in positions:
            return None
        return positions.index(ANY_POSITION)

    return positions.index(position)


def get_relaxed_position_priority_penalty(user, position):
    """완화 모드에서 포지션이 없더라도 강제로 배정할 수 있게 페널티를 준다."""
    penalty = get_position_priority_penalty(user, position)

    if penalty is not None:
        return penalty

    positions = normalize_positions(user)
    return max(len(positions), 1) + RELAXED_POSITION_PENALTY


def _position_map_sort_key(position_map):
    """포지션 맵 정렬 기준을 정의한다."""
    return (
        position_map["position_penalty"],
        position_map["bottom_penalty"],
    )


def _build_line_diff_vector(team1_case, team2_case):
    """두 포지션 맵의 라인별 점수 차이를 벡터 형태로 계산한다."""
    return tuple(
        abs(left - right)
        for left, right in zip(
            team1_case["line_power_vector"],
            team2_case["line_power_vector"],
        )
    )


def _build_line_metrics(team1_case, team2_case):
    """라인 차이 벡터에서 경고 수, 최대 차이, 불일치 심각도를 계산한다."""
    line_diffs = _build_line_diff_vector(team1_case, team2_case)
    warning_count = 0
    mismatch_severity = 0.0

    for index, diff in enumerate(line_diffs):
        position = POSITIONS[index]
        limit = get_line_limit(position)
        if diff >= limit:
            warning_count += 1
            weight = LINE_MISMATCH_WEIGHT_MAP.get(position, 1)
            mismatch_severity += (diff - limit) * weight

    return {
        "line_diffs": line_diffs,
        "line_diff_total": sum(line_diffs),
        "warning_count": warning_count,
        "max_line_diff": max(line_diffs),
        "adc_line_diff": line_diffs[POSITION_INDEX_MAP[ADC_POSITION]],
        "mismatch_severity": mismatch_severity,
    }


def _prepare_user(user, index, tier_score):
    """반복 계산을 줄이기 위해 한 유저의 캐시 데이터를 미리 만들어 둔다."""
    prepared = dict(user)
    prepared["_build_id"] = index
    prepared["_normalized_positions"] = [
        normalize_position_name(position) if position else ANY_POSITION
        for position in user.get("positions", [])
    ]
    prepared["_position_stat_map"] = {
        stat.get("position"): stat
        for stat in (user.get("recent_position_stats", []) or [])
        if stat.get("position")
    }
    prepared["_recent_form_bonus"] = calc_recent_form_bonus(prepared)
    prepared["_position_fit_bonus_map"] = {
        position: calc_position_fit_bonus(prepared, position)
        for position in POSITIONS
    }
    prepared["_line_power_by_position"] = {
        position: calc_line_power(prepared, tier_score, position)
        for position in POSITIONS
    }

    tier = normalize_tier_name(prepared["tier"])
    base = DEFAULT_TIER_SCORE.get(tier, 1)
    weight = tier_score.get(tier, 1)
    detail = int(prepared.get("tier_detail", 2))
    detail_multiplier = DETAIL_MULTIPLIER_MAP.get(detail, 1.0)
    form_multiplier = 1.0 + prepared["_recent_form_bonus"]
    power = base * detail_multiplier * weight * form_multiplier

    prepared["_power"] = power
    prepared["_power_components"] = {
        "base": base,
        "weight": weight,
        "detail": detail,
        "detail_multiplier": detail_multiplier,
        "form_bonus": prepared["_recent_form_bonus"],
        "form_multiplier": form_multiplier,
        "power": power,
    }
    return prepared


def _generate_position_maps(team, relaxed=False):
    """한 팀에 대해 가능한 포지션 배치 후보를 생성한다."""
    maps = []

    for permutation in itertools.permutations(team, len(POSITIONS)):
        mapping = {}
        line_power_vector = []
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
            line_power_vector.append(user["_line_power_by_position"][position])
            position_penalty += penalty

        if not valid:
            continue

        bottom_penalty = abs(
            mapping[ADC_POSITION]["_line_power_by_position"][ADC_POSITION]
            - mapping[SUPPORT_POSITION]["_line_power_by_position"][SUPPORT_POSITION]
        )

        maps.append({
            "map": mapping,
            "position_penalty": position_penalty,
            "line_power_vector": tuple(line_power_vector),
            "bottom_penalty": bottom_penalty,
        })

    maps.sort(key=_position_map_sort_key)
    return maps[:MAX_POSITION_MAPS_PER_TEAM]


def generate_position_maps(team):
    """엄격 모드 포지션 배치 후보를 생성한다."""
    return _generate_position_maps(team, relaxed=False)


def generate_relaxed_position_maps(team):
    """완화 모드 포지션 배치 후보를 생성한다."""
    return _generate_position_maps(team, relaxed=True)


def get_line_limit(position):
    """포지션별 허용 라인 격차 한계를 반환한다."""
    return LINE_LIMIT_MAP.get(position, 1.2)


def calc_line_diff_total(team1_map, team2_map, tier_score):
    """두 팀의 라인 차이 총합을 계산한다."""
    total = 0.0
    for position in POSITIONS:
        total += abs(
            calc_line_power(team1_map[position], tier_score, position)
            - calc_line_power(team2_map[position], tier_score, position)
        )
    return total


def check_line_warnings(team1_map, team2_map, tier_score):
    """라인별 격차가 허용 범위를 넘는지 검사한다."""
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
    """라인 경고 개수만 빠르게 계산한다."""
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
    """한 포지션에서 양 팀 유저 간 점수 차이를 계산한다."""
    return abs(
        calc_line_power(team1_map[position], tier_score, position)
        - calc_line_power(team2_map[position], tier_score, position)
    )


def get_max_line_diff(team1_map, team2_map, tier_score):
    """모든 라인 중 가장 큰 점수 차이를 반환한다."""
    return max(
        get_line_diff(position, team1_map, team2_map, tier_score)
        for position in POSITIONS
    )


def get_position_mismatch_severity(position, team1_map, team2_map, tier_score):
    """한 라인의 불균형 심각도를 계산한다."""
    diff = get_line_diff(position, team1_map, team2_map, tier_score)
    limit = get_line_limit(position)

    if diff <= limit:
        return 0

    weight = LINE_MISMATCH_WEIGHT_MAP.get(position, 1)
    return (diff - limit) * weight


def get_line_mismatch_severity(team1_map, team2_map, tier_score):
    """모든 라인의 불균형 심각도 합을 계산한다."""
    return sum(
        get_position_mismatch_severity(position, team1_map, team2_map, tier_score)
        for position in POSITIONS
    )


def get_adc_line_diff(team1_map, team2_map, tier_score):
    """원딜 라인의 점수 차이만 따로 반환한다."""
    return get_line_diff(ADC_POSITION, team1_map, team2_map, tier_score)


def calc_bottom_pair_penalty(team_map, tier_score):
    """한 팀 내부의 원딜-서포터 밸런스 차이를 계산한다."""
    adc = team_map.get(get_adc_position())
    support = team_map.get(get_support_position())

    if not adc or not support:
        return 0

    return abs(
        calc_line_power(adc, tier_score, ADC_POSITION)
        - calc_line_power(support, tier_score, SUPPORT_POSITION)
    )


def calc_team_form_diff(team1, team2):
    """양 팀의 최근 폼 차이를 계산한다."""
    team1_form = sum(calc_recent_form_bonus(user) for user in team1)
    team2_form = sum(calc_recent_form_bonus(user) for user in team2)
    return abs(team1_form - team2_form)


def normalize_couple_group(value):
    """커플 그룹명을 비교하기 쉬운 형태로 정리한다."""
    text = str(value or "").strip()
    return text or None


def calc_couple_group_penalty(team1, team2):
    """같은 커플 그룹이 서로 다른 팀에 나뉘면 페널티와 상세 목록을 계산한다."""
    group_map = {}

    for user in team1:
        group_name = normalize_couple_group(user.get("couple_group"))
        if not group_name:
            continue
        group_map.setdefault(group_name, {"team1": [], "team2": []})
        group_map[group_name]["team1"].append(user["name"])

    for user in team2:
        group_name = normalize_couple_group(user.get("couple_group"))
        if not group_name:
            continue
        group_map.setdefault(group_name, {"team1": [], "team2": []})
        group_map[group_name]["team2"].append(user["name"])

    penalty = 0
    split_groups = []

    for group_name, members in sorted(group_map.items()):
        total_count = len(members["team1"]) + len(members["team2"])
        if total_count < 2:
            continue

        if members["team1"] and members["team2"]:
            penalty += min(len(members["team1"]), len(members["team2"]))
            split_groups.append({
                "group_name": group_name,
                "team1_members": members["team1"],
                "team2_members": members["team2"],
            })

    return penalty, split_groups


def build_balance_alerts(selected, used_relaxed_rules, tier_score):
    """최종 결과에 함께 보여줄 밸런스 경고 메시지를 만든다."""
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

    split_couple_groups = selected.get("split_couple_groups", [])
    if split_couple_groups:
        group_names = ", ".join(group["group_name"] for group in split_couple_groups)
        alerts.append({
            "type": "couple_group_warning",
            "message": f"커플 그룹 분리 주의: {group_names} 그룹이 서로 다른 팀으로 나뉘었습니다.",
            "details": split_couple_groups,
        })

    return alerts


def _get_team_cache_key(team):
    """팀 구성 캐시를 위한 안정적인 키를 만든다."""
    return tuple(sorted(user["_build_id"] for user in team))


def _get_position_maps_for_team(team, relaxed, position_map_cache):
    """같은 팀 구성에 대한 포지션 배치 후보를 캐시에서 재사용한다."""
    cache_key = (relaxed, _get_team_cache_key(team))
    if cache_key not in position_map_cache:
        position_map_cache[cache_key] = _generate_position_maps(team, relaxed=relaxed)
    return position_map_cache[cache_key]


def _build_candidate(
    team1,
    team2,
    team1_case,
    team2_case,
    team1_score,
    team2_score,
    build_weights,
):
    """한 쌍의 포지션 배치 후보를 최종 평가용 candidate로 만든다."""
    line_metrics = _build_line_metrics(team1_case, team2_case)
    team_diff = abs(team1_score - team2_score)
    team_form_diff = calc_team_form_diff(team1, team2)
    position_penalty = team1_case["position_penalty"] + team2_case["position_penalty"]
    bottom_penalty = team1_case["bottom_penalty"] + team2_case["bottom_penalty"]
    couple_group_penalty, split_couple_groups = calc_couple_group_penalty(team1, team2)

    final_score = (
        team_diff * build_weights.get("team_diff", DEFAULT_BUILD_WEIGHTS["team_diff"])
        + line_metrics["line_diff_total"] * build_weights.get("line_diff_total", DEFAULT_BUILD_WEIGHTS["line_diff_total"])
        + position_penalty * build_weights.get("position_penalty", DEFAULT_BUILD_WEIGHTS["position_penalty"])
        + bottom_penalty * build_weights.get("bottom_penalty", DEFAULT_BUILD_WEIGHTS["bottom_penalty"])
        + team_form_diff * build_weights.get("team_form_diff", DEFAULT_BUILD_WEIGHTS["team_form_diff"])
        + couple_group_penalty * build_weights.get("couple_group_penalty", DEFAULT_BUILD_WEIGHTS["couple_group_penalty"])
    )

    candidate = {
        "final_score": final_score,
        "warning_count": line_metrics["warning_count"],
        "diff": team_diff,
        "max_line_diff": line_metrics["max_line_diff"],
        "adc_line_diff": line_metrics["adc_line_diff"],
        "mismatch_severity": line_metrics["mismatch_severity"],
        "line_diff_total": line_metrics["line_diff_total"],
        "position_penalty": position_penalty,
        "bottom_penalty": bottom_penalty,
        "team_form_diff": team_form_diff,
        "couple_group_penalty": couple_group_penalty,
        "split_couple_groups": split_couple_groups,
        "t1_map": team1_case["map"],
        "t2_map": team2_case["map"],
        "t1_score": team1_score,
        "t2_score": team2_score,
    }

    candidate_key = (
        candidate["warning_count"],
        candidate["adc_line_diff"],
        candidate["max_line_diff"],
        candidate["mismatch_severity"],
        candidate["final_score"],
    )

    return candidate, candidate_key


def _build_score_breakdown_rows(candidate, build_weights):
    """최종 점수 계산에 사용된 항목별 합산표 데이터를 만든다."""
    metrics = [
        ("팀 총점 차이", "team_diff", candidate["diff"]),
        ("라인 점수 차이 합", "line_diff_total", candidate["line_diff_total"]),
        ("선호 포지션 페널티", "position_penalty", candidate["position_penalty"]),
        ("봇 듀오 밸런스 페널티", "bottom_penalty", candidate["bottom_penalty"]),
        ("팀 최근 폼 차이", "team_form_diff", candidate["team_form_diff"]),
        ("커플매칭 중요도", "couple_group_penalty", candidate["couple_group_penalty"]),
    ]

    rows = []
    for label, key, raw_value in metrics:
        weight = build_weights.get(key, DEFAULT_BUILD_WEIGHTS[key])
        weighted_value = raw_value * weight
        rows.append({
            "항목": label,
            "원본값": round(raw_value, 2),
            "가중치": weight,
            "반영값": round(weighted_value, 2),
        })

    rows.append({
        "항목": "라인 경고 수",
        "원본값": candidate["warning_count"],
        "가중치": "-",
        "반영값": "-",
    })
    rows.append({
        "항목": "가장 큰 라인 차이",
        "원본값": round(candidate["max_line_diff"], 2),
        "가중치": "-",
        "반영값": "-",
    })
    rows.append({
        "항목": "원딜 라인 차이",
        "원본값": round(candidate["adc_line_diff"], 2),
        "가중치": "-",
        "반영값": "-",
    })
    if candidate.get("split_couple_groups"):
        split_group_text = ", ".join(
            f"{group['group_name']} (1팀: {', '.join(group['team1_members'])} / 2팀: {', '.join(group['team2_members'])})"
            for group in candidate["split_couple_groups"]
        )
        rows.append({
            "항목": "분리된 커플 그룹",
            "원본값": split_group_text,
            "가중치": "-",
            "반영값": "-",
        })

    rows.append({
        "항목": "최종 점수",
        "원본값": "",
        "가중치": "",
        "반영값": round(candidate["final_score"], 2),
    })
    return rows


def _build_team_candidates(users, tier_score, build_weights, relaxed=False):
    """10명 중 가능한 5:5 팀 후보를 탐색해 최상위 결과만 남긴다."""
    best_candidates = []
    best_key = None
    position_map_cache = {}
    user_count = len(users)

    for team1_indexes in itertools.combinations(range(user_count), 5):
        team1_index_set = set(team1_indexes)
        team2_indexes = tuple(
            index for index in range(user_count) if index not in team1_index_set
        )

        team1 = [users[index] for index in team1_indexes]
        team2 = [users[index] for index in team2_indexes]

        team1_maps = _get_position_maps_for_team(team1, relaxed, position_map_cache)
        team2_maps = _get_position_maps_for_team(team2, relaxed, position_map_cache)

        if not team1_maps or not team2_maps:
            continue

        team1_score = sum(user["_power"] for user in team1)
        team2_score = sum(user["_power"] for user in team2)

        for team1_case in team1_maps:
            for team2_case in team2_maps:
                candidate, candidate_key = _build_candidate(
                    team1,
                    team2,
                    team1_case,
                    team2_case,
                    team1_score,
                    team2_score,
                    build_weights,
                )

                if best_key is None or candidate_key < best_key:
                    best_key = candidate_key
                    best_candidates = [candidate]
                elif candidate_key == best_key:
                    best_candidates.append(candidate)

    return best_candidates


def _format_power_formula_line(user, tier_score):
    """한 유저의 팀 점수 계산식을 사람이 읽기 쉬운 문자열로 만든다."""
    components = user.get("_power_components")
    if not components:
        tier = normalize_tier_name(user["tier"])
        base = DEFAULT_TIER_SCORE.get(tier, 1)
        weight = tier_score.get(tier, 1)
        detail = int(user.get("tier_detail", 2))
        detail_multiplier = DETAIL_MULTIPLIER_MAP.get(detail, 1.0)
        form_bonus = calc_recent_form_bonus(user)
        form_multiplier = 1.0 + form_bonus
        power = calc_power(user, tier_score)
        components = {
            "base": base,
            "weight": weight,
            "detail": detail,
            "detail_multiplier": detail_multiplier,
            "form_bonus": form_bonus,
            "form_multiplier": form_multiplier,
            "power": power,
        }

    return (
        f"{user['name']}: 기본점수 {components['base']} "
        f"x 세부랭크배율 {components['detail_multiplier']:.2f} "
        f"(세부랭크 {components['detail']}) "
        f"x 티어가중치 {components['weight']:.2f} "
        f"x 최근폼배율 {components['form_multiplier']:.2f} "
        f"(폼보너스 {components['form_bonus'] * 100:+.1f}%) "
        f"= {components['power']:.2f}"
    )


def build_team_score_tooltip(team_map, tier_score):
    """팀 점수 라벨 툴팁에 표시할 계산식 문자열을 만든다."""
    lines = [
        "팀 점수 계산식",
        "총점 = 각 유저의 (기본점수 x 세부랭크배율 x 티어가중치 x 최근폼배율) 합",
        "",
    ]

    total = 0.0
    for position in POSITIONS:
        user = team_map[position]
        lines.append(f"[{position}] {_format_power_formula_line(user, tier_score)}")
        total += calc_power(user, tier_score)

    lines.extend(["", f"총합 = {total:.2f}"])
    return "\n".join(lines)


def build_best_teams(users, tier_score=None, build_weights=None):
    """10명의 유저를 받아 가장 밸런스가 좋은 5:5 조합을 반환한다."""
    if tier_score is None:
        tier_score = load_config()
    if build_weights is None:
        build_weights = dict(DEFAULT_BUILD_WEIGHTS)

    if len(users) != 10:
        raise Exception("5:5 팀 생성을 위해 선택된 유저는 반드시 10명이어야 합니다.")

    prepared_users = [
        _prepare_user(user, index, tier_score)
        for index, user in enumerate(users)
    ]

    best_candidates = _build_team_candidates(
        prepared_users,
        tier_score,
        build_weights,
        relaxed=False,
    )
    used_relaxed_rules = False

    if not best_candidates:
        best_candidates = _build_team_candidates(
            prepared_users,
            tier_score,
            build_weights,
            relaxed=True,
        )
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
        "t1_score_tooltip": build_team_score_tooltip(selected["t1_map"], tier_score),
        "t2_score_tooltip": build_team_score_tooltip(selected["t2_map"], tier_score),
        "score_breakdown_rows": _build_score_breakdown_rows(selected, build_weights),
    }


def format_team(team_map):
    """디버깅이나 복사용으로 팀 배치를 문자열로 만든다."""
    return "\n".join(
        f"{position} - {user['name']} ({user['tier']}/{user.get('tier_detail', 2)})"
        for position, user in team_map.items()
    )
