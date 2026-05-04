from ..stores.match_store import (
    get_match_detail as load_match_detail,
    get_recent_matches_by_puuid as load_recent_matches_by_puuid,
    get_recent_matches_by_riot_id as load_recent_matches_by_riot_id,
)
from ..stores.riot_account_store import (
    get_accounts_by_game_name as load_accounts_by_game_name,
    list_accounts as load_accounts,
    search_accounts_by_game_name as search_accounts,
)


class MatchService:
    def list_accounts(self, limit: int) -> dict:
        """저장된 Riot 계정 목록을 관리자 화면용 응답 형태로 묶어 반환한다."""
        accounts = load_accounts(limit)
        return {
            "count": len(accounts),
            "accounts": accounts,
        }

    def get_accounts_by_game_name(self, game_name: str) -> dict:
        """같은 게임 닉네임을 가진 저장 계정들을 묶어서 반환한다."""
        accounts = load_accounts_by_game_name(game_name)
        return {
            "game_name": game_name,
            "count": len(accounts),
            "accounts": accounts,
        }

    def search_accounts_by_game_name(self, keyword: str, limit: int) -> dict:
        """부분 검색어로 저장 계정을 찾아 목록 화면에 맞는 형태로 반환한다."""
        accounts = search_accounts(keyword, limit)
        return {
            "keyword": keyword,
            "count": len(accounts),
            "accounts": accounts,
        }

    def get_recent_matches_by_puuid(self, puuid: str, limit: int) -> dict:
        """한 사용자의 최근 경기 참가 이력을 PUUID 기준으로 반환한다."""
        matches = load_recent_matches_by_puuid(puuid, limit)
        return {
            "puuid": puuid,
            "count": len(matches),
            "matches": matches,
        }

    def get_recent_matches_by_riot_id(
        self, game_name: str, tag_line: str, limit: int
    ) -> dict:
        """닉네임과 태그 조합으로 최근 경기 참가 이력을 반환한다."""
        matches = load_recent_matches_by_riot_id(game_name, tag_line, limit)
        return {
            "game_name": game_name,
            "tag_line": tag_line,
            "count": len(matches),
            "matches": matches,
        }

    def get_match_detail(self, match_id: str) -> dict:
        """저장된 경기 상세를 읽고, 없으면 일관된 에러 응답을 반환한다."""
        detail = load_match_detail(match_id)
        if detail is None:
            return {
                "error": "Match not found in Firestore",
                "match_id": match_id,
            }
        return detail
