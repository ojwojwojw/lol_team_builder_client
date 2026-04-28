"""
Team Presenter - UI에서 사용할 비즈니스 로직 분리
MainWindow와 service 계층 사이를 중재하는 Presenter
"""
from service.dataset_service import DatasetService, load_config
from service.team_builder import build_best_teams, calc_power


class TeamPresenter:
    """UI에서 사용할 비즈니스 로직을 제공하는 Presenter"""

    # ---------------- DATASET ----------------
    @staticmethod
    def get_dataset_list():
        """데이터셋 파일 목록 반환"""
        return DatasetService.list_files()

    @staticmethod
    def load_dataset(file_name):
        """데이터셋 로드"""
        return DatasetService.load(file_name)

    @staticmethod
    def create_dataset(name):
        """새 데이터셋 생성"""
        return DatasetService.create(name)

    @staticmethod
    def save_dataset(file_name, users):
        """데이터셋 저장"""
        DatasetService.save(file_name, users)

    # ---------------- TABLE DATA ----------------
    @staticmethod
    def extract_table_data(table):
        """
        테이블에서 사용자 데이터 추출
        Returns: (users list) or (None, error message)
        """
        users = []

        for r in range(table.rowCount()):
            name_edit = table.cellWidget(r, 1)

            if not name_edit or not name_edit.text().strip():
                return None, f"{r+1}번째 이름 비어있음"

            chk = table.cellWidget(r, 0)
            tier_cb = table.cellWidget(r, 2)
            detail_cb = table.cellWidget(r, 3)

            users.append({
                "selected": chk.isChecked() if chk else False,
                "name": name_edit.text().strip(),
                "tier": tier_cb.currentText() if tier_cb else "",
                "tier_detail": int(detail_cb.currentText()) if detail_cb else 1,
                "positions": [
                    table.cellWidget(r, 4).currentText() if table.cellWidget(r, 4) else "",
                    table.cellWidget(r, 5).currentText() if table.cellWidget(r, 5) else "",
                    table.cellWidget(r, 6).currentText() if table.cellWidget(r, 6) else "",
                ],
            })

        return users, None

    @staticmethod
    def extract_selected_users(table):
        """
        선택된 사용자만 추출
        Returns: users list
        """
        selected = []

        for r in range(table.rowCount()):
            chk = table.cellWidget(r, 0)
            if not chk or not chk.isChecked():
                continue

            name_edit = table.cellWidget(r, 1)
            tier_cb = table.cellWidget(r, 2)
            detail_cb = table.cellWidget(r, 3)

            p1 = table.cellWidget(r, 4)
            p2 = table.cellWidget(r, 5)
            p3 = table.cellWidget(r, 6)

            if any(x is None for x in [name_edit, tier_cb, p1, p2, p3]):
                continue

            name = name_edit.text().strip()
            if not name:
                continue

            selected.append({
                "name": name,
                "tier": tier_cb.currentText(),
                "tier_detail": int(detail_cb.currentText()),
                "positions": [
                    p1.currentText(),
                    p2.currentText(),
                    p3.currentText(),
                ],
            })

        return selected

    # ---------------- TEAM BUILDING ----------------
    def build_teams(self, selected_users):
        """
        선택된 유저로 팀 생성
        Returns: dict with a1, a2, t1_score, t2_score, diff, warnings, alerts
        """
        if len(selected_users) < 10:
            return None, "10명을 체크해주세요!"

        selected = selected_users[:10]
        tier_score = load_config()

        try:
            result = build_best_teams(selected, tier_score)
        except Exception as e:
            return None, str(e)

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
        """팀 점수: 각 유저의 power(tier x detail x config 가중치)의 합"""
        return sum(calc_power(u, tier_score) for u in team)

    # ---------------- FORMATTING ----------------
    @staticmethod
    def format_team_result(team1, team2):
        """팀 결과를 문자열로 포맷"""
        def format_team(team):
            lines = []
            for pos, user in team.items():
                detail = user.get("tier_detail", 2)
                lines.append(f"{pos} - {user['name']} ({user['tier']} / {detail})")
            return "\n".join(lines)

        return (
            "[TEAM1]\n"
            + format_team(team1)
            + "\n\n[TEAM2]\n"
            + format_team(team2)
        )

    @staticmethod
    def format_warnings(warnings):
        """라인 밸런스 경고 메시지 포맷"""
        if not warnings:
            return None

        msg = "라인 밸런스 경고\n\n"

        for w in warnings:
            t1 = w.get("team1", {})
            t2 = w.get("team2", {})

            msg += (
                f"[{w.get('position', '?')}]\n"
                f"  {t1.get('name', '?')} ({t1.get('tier', '?')} / {t1.get('detail', 2)})"
                f"  vs "
                f"{t2.get('name', '?')} ({t2.get('tier', '?')} / {t2.get('detail', 2)})\n"
                f"  차이: {w.get('diff', 0)} / 허용치: {w.get('limit', 0)}\n"
                f"{'-' * 30}\n"
            )

        return msg

    @staticmethod
    def format_alerts(alerts):
        """밸런스 주의 알람 메시지 포맷"""
        if not alerts:
            return None

        lines = ["밸런스 주의", ""]

        for alert in alerts:
            message = alert.get("message", "")
            if message:
                lines.append(f"- {message}")

        return "\n".join(lines)


team_presenter = TeamPresenter()
