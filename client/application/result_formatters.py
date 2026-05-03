from domain.team_builder import calc_position_fit_bonus, calc_recent_form_bonus


def _format_tier_detail(value):
    return "-" if value in (None, "", "-") else str(value)


def format_team_result(team1, team2):
    def format_team(team):
        lines = []
        for pos, user in team.items():
            detail = _format_tier_detail(user.get("tier_detail", 2))
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


def format_warnings(warnings):
    if not warnings:
        return None

    lines = ["라인 밸런스 경고", ""]

    for warning in warnings:
        t1 = warning.get("team1", {})
        t2 = warning.get("team2", {})
        lines.append(f"[{warning.get('position', '?')}]")
        lines.append(
            f"  {t1.get('name', '?')} ({t1.get('tier', '?')} / {_format_tier_detail(t1.get('detail', 2))})"
            f" vs {t2.get('name', '?')} ({t2.get('tier', '?')} / {_format_tier_detail(t2.get('detail', 2))})"
        )
        lines.append(
            f"  차이: {warning.get('diff', 0)} / 허용치: {warning.get('limit', 0)}"
        )
        lines.append("-" * 30)

    return "\n".join(lines)


def format_alerts(alerts):
    if not alerts:
        return None

    lines = ["밸런스 주의", ""]

    for alert in alerts:
        message = alert.get("message", "")
        if message:
            lines.append(f"- {message}")

    return "\n".join(lines)
