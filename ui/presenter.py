"""
Team Presenter - separates UI-facing logic from widget code.
MainWindow talks to this presenter instead of calling services directly.
"""

from collections import Counter
from datetime import datetime

from service.dataset_service import (
    DatasetService,
    load_config,
    load_server_base_url,
    save_server_base_url,
)
from service.match_api_client import MatchApiClient
from service.team_builder import (
    build_best_teams,
    calc_position_fit_bonus,
    calc_power,
    calc_recent_form_bonus,
)
from util.constants import ANY_POSITION, normalize_position_name, normalize_tier_name


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


class TeamPresenter:
    """Presenter that provides UI-friendly entry points."""

    # ---------------- DATASET ----------------
    @staticmethod
    def get_dataset_list():
        return DatasetService.list_files()

    @staticmethod
    def load_dataset(file_name):
        return DatasetService.load(file_name)

    @staticmethod
    def create_dataset(name):
        return DatasetService.create(name)

    @staticmethod
    def save_dataset(file_name, users):
        DatasetService.save(file_name, users)

    # ---------------- API CLIENT ----------------
    @staticmethod
    def load_server_base_url():
        return load_server_base_url()

    @staticmethod
    def save_server_base_url(base_url):
        save_server_base_url(base_url)

    @staticmethod
    def search_accounts(keyword, limit=20):
        client = MatchApiClient()
        return client.search_accounts(keyword, limit)

    @staticmethod
    def get_recent_matches_by_riot_id(game_name, tag_line, limit=10):
        client = MatchApiClient()
        return client.get_recent_matches_by_riot_id(game_name, tag_line, limit)

    @staticmethod
    def get_match_detail(match_id):
        client = MatchApiClient()
        return client.get_match_detail(match_id)

    # ---------------- API DATA SHAPING ----------------
    @staticmethod
    def map_position_label(position):
        value = (position or "").strip().upper()
        return POSITION_LABEL_MAP.get(value, normalize_position_name(position))

    @staticmethod
    def format_match_datetime(timestamp):
        if not timestamp:
            return "-"

        try:
            return datetime.fromtimestamp(timestamp / 1000).strftime("%m-%d %H:%M")
        except Exception:
            return "-"

    @staticmethod
    def format_kda(match):
        return f"{match.get('kills', 0)}/{match.get('deaths', 0)}/{match.get('assists', 0)}"

    @staticmethod
    def get_match_position(match):
        return TeamPresenter.map_position_label(
            match.get("team_position") or match.get("lane") or match.get("role")
        )

    @staticmethod
    def get_match_result_text(match):
        return "승리" if match.get("win") else "패배"

    @staticmethod
    def get_match_cs(match):
        return int(match.get("total_minions_killed", 0) or 0) + int(
            match.get("neutral_minions_killed", 0) or 0
        )

    @staticmethod
    def _round(value, digits=1):
        return round(float(value), digits)

    @staticmethod
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
            position = TeamPresenter.get_match_position(match)
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
            total_cs += TeamPresenter.get_match_cs(match)
            total_vision += int(match.get("vision_score", 0) or 0)
            total_damage += int(match.get("total_damage_dealt_to_champions", 0) or 0)
            total_gold += int(match.get("gold_earned", 0) or 0)

            if win:
                total_wins += 1
                position_wins[position] += 1
                champion_wins[champion] += 1

        match_count = len(matches)
        total_losses = max(match_count - total_wins, 0)
        recent_win_rate = TeamPresenter._round((total_wins / match_count) * 100, 1) if match_count else 0.0
        recent_kda = TeamPresenter._round((total_kills + total_assists) / max(total_deaths, 1), 2) if match_count else 0.0
        avg_cs = TeamPresenter._round(total_cs / match_count, 1) if match_count else 0.0
        avg_vision = TeamPresenter._round(total_vision / match_count, 1) if match_count else 0.0
        avg_damage = TeamPresenter._round(total_damage / match_count, 1) if match_count else 0.0
        avg_gold = TeamPresenter._round(total_gold / match_count, 1) if match_count else 0.0

        position_stats = []
        for position, count in position_counter.most_common():
            wins = position_wins[position]
            losses = count - wins
            position_stats.append({
                "position": position,
                "count": count,
                "wins": wins,
                "losses": losses,
                "win_rate": TeamPresenter._round((wins / count) * 100, 1) if count else 0.0,
                "share": TeamPresenter._round((count / match_count) * 100, 1) if match_count else 0.0,
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
                "win_rate": TeamPresenter._round((wins / count) * 100, 1) if count else 0.0,
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

    @staticmethod
    def build_user_profile(account, matches=None, existing_user=None):
        summary = TeamPresenter.summarize_recent_matches(matches or [])
        existing_user = existing_user or {}

        positions = summary["preferred_positions"]
        if not summary["match_count"]:
            positions = existing_user.get(
                "positions",
                [ANY_POSITION, ANY_POSITION, ANY_POSITION],
            )

        return {
            "selected": existing_user.get("selected", True),
            "name": account.get("game_name", ""),
            "tier": normalize_tier_name(existing_user.get("tier", "실버")),
            "tier_detail": existing_user.get("tier_detail", 2),
            "positions": [normalize_position_name(position) for position in positions],
            "account_tag_line": account.get("tag_line", ""),
            "account_puuid": account.get("puuid", ""),
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

    @staticmethod
    def normalize_match_detail(detail):
        participants = []

        for participant in detail.get("participants", []):
            participants.append({
                "summoner_name": participant.get("summoner_name", "-"),
                "champion_name": participant.get("champion_name", "-"),
                "position": TeamPresenter.map_position_label(
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

    # ---------------- TABLE DATA ----------------
    @staticmethod
    def _get_row_meta(table, row):
        chk = table.cellWidget(row, 0)
        if not chk:
            return {}
        return dict(chk.property("user_meta") or {})

    @staticmethod
    def extract_table_data(table):
        users = []

        for row in range(table.rowCount()):
            name_edit = table.cellWidget(row, 1)

            if not name_edit or not name_edit.text().strip():
                return None, f"{row + 1}번째 줄의 이름이 비어 있습니다."

            chk = table.cellWidget(row, 0)
            tier_cb = table.cellWidget(row, 2)
            detail_cb = table.cellWidget(row, 3)
            p1 = table.cellWidget(row, 4)
            p2 = table.cellWidget(row, 5)
            p3 = table.cellWidget(row, 6)

            user = TeamPresenter._get_row_meta(table, row)
            user.update({
                "selected": chk.isChecked() if chk else False,
                "name": name_edit.text().strip(),
                "tier": tier_cb.currentText() if tier_cb else "",
                "tier_detail": int(detail_cb.currentText()) if detail_cb else 1,
                "positions": [
                    p1.currentText() if p1 else "",
                    p2.currentText() if p2 else "",
                    p3.currentText() if p3 else "",
                ],
            })
            users.append(user)

        return users, None

    @staticmethod
    def extract_selected_users(table):
        selected = []

        for row in range(table.rowCount()):
            chk = table.cellWidget(row, 0)
            if not chk or not chk.isChecked():
                continue

            name_edit = table.cellWidget(row, 1)
            tier_cb = table.cellWidget(row, 2)
            detail_cb = table.cellWidget(row, 3)
            p1 = table.cellWidget(row, 4)
            p2 = table.cellWidget(row, 5)
            p3 = table.cellWidget(row, 6)

            if any(widget is None for widget in [name_edit, tier_cb, detail_cb, p1, p2, p3]):
                continue

            name = name_edit.text().strip()
            if not name:
                continue

            user = TeamPresenter._get_row_meta(table, row)
            user.update({
                "name": name,
                "tier": tier_cb.currentText(),
                "tier_detail": int(detail_cb.currentText()),
                "positions": [
                    p1.currentText(),
                    p2.currentText(),
                    p3.currentText(),
                ],
            })
            selected.append(user)

        return selected

    # ---------------- TEAM BUILDING ----------------
    def build_teams(self, selected_users):
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

    @staticmethod
    def _calc_team_score(team, tier_score):
        return sum(calc_power(user, tier_score) for user in team)

    # ---------------- FORMATTING ----------------
    @staticmethod
    def format_team_result(team1, team2):
        def format_team(team):
            lines = []
            for pos, user in team.items():
                detail = user.get("tier_detail", 2)
                form = ""
                if user.get("recent_match_count"):
                    form_score = calc_recent_form_bonus(user) * 100
                    fit_score = calc_position_fit_bonus(user, pos) * 100
                    form = (
                        f", 최근승률 {user.get('recent_win_rate', 0)}%"
                        f", KDA {user.get('recent_kda', 0)}"
                        f", 폼 {form_score:+.1f}%"
                        f", 포지션적합 {fit_score:+.1f}%"
                    )
                lines.append(f"{pos} - {user['name']} ({user['tier']} / {detail}{form})")
            return "\n".join(lines)

        return "[TEAM1]\n" + format_team(team1) + "\n\n[TEAM2]\n" + format_team(team2)

    @staticmethod
    def format_warnings(warnings):
        if not warnings:
            return None

        lines = ["라인 밸런스 경고", ""]

        for warning in warnings:
            t1 = warning.get("team1", {})
            t2 = warning.get("team2", {})
            lines.append(f"[{warning.get('position', '?')}]")
            lines.append(
                f"  {t1.get('name', '?')} ({t1.get('tier', '?')} / {t1.get('detail', 2)})"
                f" vs {t2.get('name', '?')} ({t2.get('tier', '?')} / {t2.get('detail', 2)})"
            )
            lines.append(
                f"  차이: {warning.get('diff', 0)} / 허용치: {warning.get('limit', 0)}"
            )
            lines.append("-" * 30)

        return "\n".join(lines)

    @staticmethod
    def format_alerts(alerts):
        if not alerts:
            return None

        lines = ["밸런스 주의", ""]

        for alert in alerts:
            message = alert.get("message", "")
            if message:
                lines.append(f"- {message}")

        return "\n".join(lines)


team_presenter = TeamPresenter()
