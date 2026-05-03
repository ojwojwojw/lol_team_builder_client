from ..database import get_connection, init_db
from ..queries.match_read_query import MatchReadQuery


class MatchService:
    # Service assembles DB read results into API-friendly response payloads.

    def list_accounts(self, limit: int) -> dict:
        """Return stored riot_account rows ordered by latest fetch time."""
        init_db()
        conn = get_connection()
        match_read_query = MatchReadQuery(conn)
        accounts = match_read_query.list_accounts(limit)
        conn.close()
        return {
            "count": len(accounts),
            "accounts": accounts,
        }

    def get_accounts_by_game_name(self, game_name: str) -> dict:
        """Return stored riot_account rows for one game name."""
        init_db()
        conn = get_connection()
        match_read_query = MatchReadQuery(conn)
        accounts = match_read_query.get_accounts_by_game_name(game_name)
        conn.close()
        return {
            "game_name": game_name,
            "count": len(accounts),
            "accounts": accounts,
        }

    def search_accounts_by_game_name(self, keyword: str, limit: int) -> dict:
        """Return stored riot_account rows using a game_name LIKE search."""
        init_db()
        conn = get_connection()
        match_read_query = MatchReadQuery(conn)
        accounts = match_read_query.search_accounts_by_game_name(keyword, limit)
        conn.close()
        return {
            "keyword": keyword,
            "count": len(accounts),
            "accounts": accounts,
        }

    def get_recent_matches_by_puuid(self, puuid: str, limit: int) -> dict:
        """Return recent stored matches for one puuid."""
        init_db()
        conn = get_connection()
        match_read_query = MatchReadQuery(conn)
        matches = match_read_query.get_recent_matches_by_puuid(puuid, limit)
        conn.close()
        return {
            "puuid": puuid,
            "count": len(matches),
            "matches": matches,
        }

    def get_recent_matches_by_riot_id(
        self, game_name: str, tag_line: str, limit: int
    ) -> dict:
        """Return recent stored matches for one Riot ID."""
        init_db()
        conn = get_connection()
        match_read_query = MatchReadQuery(conn)
        matches = match_read_query.get_recent_matches_by_riot_id(
            game_name,
            tag_line,
            limit,
        )
        conn.close()
        return {
            "game_name": game_name,
            "tag_line": tag_line,
            "count": len(matches),
            "matches": matches,
        }

    def get_match_detail(self, match_id: str) -> dict:
        """Return one stored match with summary, teams, and participants."""
        init_db()
        conn = get_connection()
        match_read_query = MatchReadQuery(conn)
        summary = match_read_query.get_match_summary(match_id)
        if summary is None:
            conn.close()
            return {
                "error": "Match not found in local database",
                "match_id": match_id,
            }

        teams = match_read_query.get_match_teams(match_id)
        participants = match_read_query.get_match_participants(match_id)
        conn.close()

        return {
            "match": summary,
            "teams": teams,
            "participants": participants,
        }
