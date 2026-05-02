from application.match_analysis import (
    format_kda,
    format_match_datetime,
    get_match_cs,
    get_match_position,
    get_match_result_text,
)


MATCH_TABLE_COLUMNS = [
    "일시",
    "챔피언",
    "포지션",
    "결과",
    "K/D/A",
    "CS",
    "시야",
    "피해량",
    "골드",
]

POSITION_SUMMARY_COLUMNS = [
    "포지션",
    "경기 수",
    "승",
    "패",
    "승률",
]

CHAMPION_SUMMARY_COLUMNS = [
    "챔피언",
    "경기 수",
    "승",
    "패",
    "승률",
]

MATCH_DETAIL_COLUMNS = [
    "소환사",
    "챔피언",
    "포지션",
    "결과",
    "K/D/A",
    "CS",
    "피해량",
    "시야",
]


def build_recent_summary_text(summary):
    if not summary.get("match_count"):
        return build_empty_recent_summary_text()

    return (
        "최근 요약: "
        f"{summary['match_count']}경기 {summary['wins']}승 {summary['losses']}패"
        f" / 승률 {summary['recent_win_rate']}%"
        f" / 평균 KDA {summary['recent_kda']}"
        f" / 평균 CS {summary['avg_cs']}"
        f" / 주 챔피언 {summary['main_champion']}"
    )


def build_empty_recent_summary_text():
    return (
        "최근 요약: 아직 불러온 경기가 없습니다. "
        "계정을 선택하면 승률, KDA, 포지션 통계를 확인할 수 있습니다."
    )


def build_loading_recent_summary_text():
    return "최근 요약: 최근 전적을 불러오는 중입니다..."


def build_recent_match_error_text():
    return (
        "최근 요약: 최근 전적을 불러오지 못했습니다. "
        "계정 정보만으로 추가는 가능하지만 최근 폼은 비어 있습니다."
    )


def build_recent_match_rows(matches):
    rows = []
    for match in matches:
        rows.append({
            "일시": format_match_datetime(match.get("game_start_timestamp")),
            "챔피언": match.get("champion_name", "-"),
            "포지션": get_match_position(match),
            "결과": get_match_result_text(match),
            "K/D/A": format_kda(match),
            "CS": get_match_cs(match),
            "시야": match.get("vision_score", 0) or 0,
            "피해량": match.get("total_damage_dealt_to_champions", 0) or 0,
            "골드": match.get("gold_earned", 0) or 0,
        })
    return rows


def build_position_summary_rows(stats):
    rows = []
    for item in stats:
        rows.append({
            "포지션": item["position"],
            "경기 수": item["count"],
            "승": item["wins"],
            "패": item["losses"],
            "승률": f"{item['win_rate']}%",
        })
    return rows


def build_champion_summary_rows(stats):
    rows = []
    for item in stats:
        rows.append({
            "챔피언": item["champion_name"],
            "경기 수": item["count"],
            "승": item["wins"],
            "패": item["losses"],
            "승률": f"{item['win_rate']}%",
        })
    return rows
