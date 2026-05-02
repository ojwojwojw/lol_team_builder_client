from urllib.parse import quote

from ..database import DB_PATH, get_connection, init_db
from ..queries.match_write_query import MatchWriteQuery
from ..queries.riot_api_query import (
    fetch_account,
    fetch_match_detail,
    fetch_match_ids,
    fetch_riot_json,
)


class RiotService:
    # Service assembles the business flow for one feature.
    # It connects controller input to query calls and shapes the response.

    def get_puuid(self, game_name: str, tag_line: str, api_key: str) -> dict:
        """Look up puuid from Riot ID and return only the fields needed by the API."""
        result = fetch_account(game_name, tag_line, api_key)
        if "error" in result:
            return result
        return {
            "game_name": result["game_name"],
            "tag_line": result["tag_line"],
            "puuid": result["puuid"],
        }

    def get_match_ids(self, puuid: str, api_key: str, count: int) -> dict:
        """Fetch recent match ids for a given puuid."""
        return fetch_match_ids(puuid, api_key, count)

    def get_match_detail(self, match_id: str, api_key: str) -> dict:
        """Fetch one match and return a UI-friendly summary payload."""
        result = fetch_match_detail(match_id, api_key)
        if "error" in result:
            return result
        return {
            "match_id": result["match_id"],
            "game_mode": result["game_mode"],
            "queue_id": result["queue_id"],
            "game_start_timestamp": result["game_start_timestamp"],
            "participants": result["participants"],
        }

    def store_recent_matches(
        self, game_name: str, tag_line: str, api_key: str, count: int = 5
    ) -> dict:
        """Fetch account and recent matches, then store each layer into SQLite."""
        init_db()

        account_result = fetch_account(game_name, tag_line, api_key)
        if "error" in account_result:
            return account_result

        puuid = account_result["puuid"]
        match_ids_result = fetch_match_ids(puuid, api_key, count)
        if "error" in match_ids_result:
            return match_ids_result

        conn = get_connection()
        match_write_query = MatchWriteQuery(conn)
        match_write_query.store_account(account_result["raw_account"])

        stored_match_ids = []
        failed_matches = []
        for match_id in match_ids_result["match_ids"]:
            # Each match is processed independently so one failed match
            # does not cancel the entire batch save.
            url = (
                "https://asia.api.riotgames.com/lol/match/v5/matches/"
                f"{quote(match_id, safe='')}"
            )
            match_data, error = fetch_riot_json(url, api_key, "Failed to get match detail")
            if error:
                failed_matches.append({"match_id": match_id, "error": error})
                continue

            match_write_query.store_match_summary(match_data)
            match_write_query.store_teams(
                match_id, match_data.get("info", {}).get("teams", [])
            )
            match_write_query.store_participants(
                match_id,
                match_data.get("info", {}).get("participants", []),
            )
            stored_match_ids.append(match_id)

        # Query methods collect inserts; the service closes the unit of work.
        match_write_query.commit()
        conn.close()

        return {
            "game_name": account_result["raw_account"].get("gameName"),
            "tag_line": account_result["raw_account"].get("tagLine"),
            "puuid": puuid,
            "requested_count": count,
            "stored_match_ids": stored_match_ids,
            "stored_count": len(stored_match_ids),
            "failed_matches": failed_matches,
            "db_path": str(DB_PATH.resolve()),
        }

    def store_recent_matches_for_accounts(
        self, accounts: list[dict], api_key: str, count: int = 5
    ) -> dict:
        """Repeat the existing single-account save flow for selected stored accounts."""
        normalized_accounts = []
        seen = set()

        for account in accounts:
            game_name = (account.get("game_name") or "").strip().rstrip("#")
            tag_line = (account.get("tag_line") or "").strip().lstrip("#")
            if not game_name or not tag_line:
                continue

            key = (game_name.lower(), tag_line.lower())
            if key in seen:
                continue

            seen.add(key)
            normalized_accounts.append({
                "game_name": game_name,
                "tag_line": tag_line,
            })

        if not normalized_accounts:
            return {
                "requested_count": count,
                "selected_account_count": 0,
                "processed_account_count": 0,
                "results": [],
                "failed_accounts": [],
                "stored_match_total": 0,
                "db_path": str(DB_PATH.resolve()),
                "error": "No valid accounts were provided",
            }

        results = []
        failed_accounts = []
        stored_match_total = 0

        for account in normalized_accounts:
            result = self.store_recent_matches(
                account["game_name"],
                account["tag_line"],
                api_key,
                count,
            )
            results.append(result)

            if "error" in result:
                failed_accounts.append({
                    "game_name": account["game_name"],
                    "tag_line": account["tag_line"],
                    "error": result["error"],
                })
                continue

            stored_match_total += int(result.get("stored_count", 0) or 0)

        return {
            "requested_count": count,
            "selected_account_count": len(accounts),
            "processed_account_count": len(normalized_accounts),
            "results": results,
            "failed_accounts": failed_accounts,
            "stored_match_total": stored_match_total,
            "db_path": str(DB_PATH.resolve()),
        }
