from collections import Counter
from datetime import datetime

from domain.constants import ANY_POSITION, normalize_position_name, normalize_tier_name


POSITION_LABEL_MAP = {
    "TOP": "탑",
    "JUNGLE": "정글",
    "MIDDLE": "미드",
    "MID": "미드",
    "BOTTOM": "원딜",
    "ADC": "원딜",
    "UTILITY": "서포터",
    "SUPPORT": "서포터",
    "NONE": ANY_POSITION,
    "": ANY_POSITION,
}

RANK_DETAIL_MAP = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
}


def map_position_label(position):
    value = (position or "").strip().upper()
    return POSITION_LABEL_MAP.get(value, normalize_position_name(position))


def format_match_datetime(timestamp):
    if not timestamp:
        return "-"

    try:
        return datetime.fromtimestamp(timestamp / 1000).strftime("%m-%d %H:%M")
    except Exception:
        return "-"


def format_kda(match):
    return f"{match.get('kills', 0)}/{match.get('deaths', 0)}/{match.get('assists', 0)}"


def get_match_position(match):
    return map_position_label(
        match.get("team_position") or match.get("lane") or match.get("role")
    )


def get_match_result_text(match):
    return "승리" if match.get("win") else "패배"


def get_match_cs(match):
    return int(match.get("total_minions_killed", 0) or 0) + int(
        match.get("neutral_minions_killed", 0) or 0
    )


def _round(value, digits=1):
    return round(float(value), digits)


def summarize_recent_matches(matches):
    matches = matches or []
    position_counter = Counter()
    position_wins = Counter()
    champion_counter = Counter()
    champion_wins = Counter()

    total_kills = 0
    total_deaths = 0
    total_assists = 0
    total_cs = 0
    total_vision = 0
    total_damage = 0
    total_gold = 0
    total_wins = 0

    for match in matches:
        position = get_match_position(match)
        champion = match.get("champion_name") or "-"
        win = bool(match.get("win"))
        kills = int(match.get("kills", 0) or 0)
        deaths = int(match.get("deaths", 0) or 0)
        assists = int(match.get("assists", 0) or 0)

        position_counter[position] += 1
        champion_counter[champion] += 1
        total_kills += kills
        total_deaths += deaths
        total_assists += assists
        total_cs += get_match_cs(match)
        total_vision += int(match.get("vision_score", 0) or 0)
        total_damage += int(match.get("total_damage_dealt_to_champions", 0) or 0)
        total_gold += int(match.get("gold_earned", 0) or 0)

        if win:
            total_wins += 1
            position_wins[position] += 1
            champion_wins[champion] += 1

    match_count = len(matches)
    total_losses = max(match_count - total_wins, 0)
    recent_win_rate = _round((total_wins / match_count) * 100, 1) if match_count else 0.0
    recent_kda = _round((total_kills + total_assists) / max(total_deaths, 1), 2) if match_count else 0.0
    avg_cs = _round(total_cs / match_count, 1) if match_count else 0.0
    avg_vision = _round(total_vision / match_count, 1) if match_count else 0.0
    avg_damage = _round(total_damage / match_count, 1) if match_count else 0.0
    avg_gold = _round(total_gold / match_count, 1) if match_count else 0.0

    position_stats = []
    for position, count in position_counter.most_common():
        wins = position_wins[position]
        losses = count - wins
        position_stats.append({
            "position": position,
            "count": count,
            "wins": wins,
            "losses": losses,
            "win_rate": _round((wins / count) * 100, 1) if count else 0.0,
            "share": _round((count / match_count) * 100, 1) if match_count else 0.0,
        })

    champion_stats = []
    for champion, count in champion_counter.most_common():
        wins = champion_wins[champion]
        losses = count - wins
        champion_stats.append({
            "champion_name": champion,
            "count": count,
            "wins": wins,
            "losses": losses,
            "win_rate": _round((wins / count) * 100, 1) if count else 0.0,
        })

    preferred_positions = [
        item["position"]
        for item in position_stats
        if item["position"] != ANY_POSITION
    ][:3]

    while len(preferred_positions) < 3:
        preferred_positions.append(ANY_POSITION)

    main_champion = champion_stats[0]["champion_name"] if champion_stats else "-"

    return {
        "match_count": match_count,
        "wins": total_wins,
        "losses": total_losses,
        "recent_win_rate": recent_win_rate,
        "recent_kda": recent_kda,
        "avg_cs": avg_cs,
        "avg_vision": avg_vision,
        "avg_damage": avg_damage,
        "avg_gold": avg_gold,
        "position_stats": position_stats,
        "champion_stats": champion_stats,
        "preferred_positions": preferred_positions[:3],
        "main_champion": main_champion,
    }


def build_user_profile(account, matches=None, existing_user=None):
    summary = summarize_recent_matches(matches or [])
    existing_user = existing_user or {}

    positions = summary["preferred_positions"]
    if not summary["match_count"]:
        positions = existing_user.get(
            "positions",
            [ANY_POSITION, ANY_POSITION, ANY_POSITION],
        )

    account_tier = normalize_tier_name(
        account.get("tier") or existing_user.get("tier", "언랭크")
    )
    account_rank = str(account.get("rank") or "").strip().upper()
    if account_tier == "언랭크":
        account_tier_detail = None
    else:
        account_tier_detail = RANK_DETAIL_MAP.get(
            account_rank,
            existing_user.get("tier_detail", 2),
        )

    return {
        "selected": existing_user.get("selected", True),
        "name": account.get("game_name", ""),
        "tier": account_tier,
        "tier_detail": account_tier_detail,
        "positions": [normalize_position_name(position) for position in positions],
        "account_tag_line": account.get("tag_line", ""),
        "account_puuid": account.get("puuid", ""),
        "account_queue_type": account.get("queue_type"),
        "account_rank": account.get("rank"),
        "account_league_points": account.get("league_points"),
        "recent_match_count": summary["match_count"],
        "recent_wins": summary["wins"],
        "recent_losses": summary["losses"],
        "recent_win_rate": summary["recent_win_rate"],
        "recent_kda": summary["recent_kda"],
        "recent_avg_cs": summary["avg_cs"],
        "recent_avg_vision": summary["avg_vision"],
        "recent_avg_damage": summary["avg_damage"],
        "recent_avg_gold": summary["avg_gold"],
        "recent_main_champion": summary["main_champion"],
        "recent_position_stats": summary["position_stats"],
        "recent_champion_stats": summary["champion_stats"][:5],
    }


def normalize_match_detail(detail):
    participants = []

    for participant in detail.get("participants", []):
        display_name = (
            participant.get("riot_id_game_name")
            or participant.get("summoner_name")
            or "-"
        )
        participants.append({
            "summoner_name": display_name,
            "champion_name": participant.get("champion_name", "-"),
            "position": map_position_label(
                participant.get("team_position")
                or participant.get("lane")
                or participant.get("role")
            ),
            "result": "승리" if participant.get("win") else "패배",
            "kda": (
                f"{participant.get('kills', 0)}/"
                f"{participant.get('deaths', 0)}/"
                f"{participant.get('assists', 0)}"
            ),
            "cs": int(participant.get("total_minions_killed", 0) or 0)
            + int(participant.get("neutral_minions_killed", 0) or 0),
            "damage": participant.get("total_damage_dealt_to_champions", 0) or 0,
            "vision": participant.get("vision_score", 0) or 0,
        })

    return participants
