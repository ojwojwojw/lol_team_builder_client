from ..database import DB_PATH, get_connection, init_db
from ..queries.match_read_query import MatchReadQuery
from ..queries.match_write_query import MatchWriteQuery
from ..queries.riot_api_query import (
    fetch_account,
    fetch_match_detail,
    fetch_match_ids,
    fetch_ranked_entries,
    fetch_summoner_by_puuid,
    select_preferred_ranked_entry,
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

    def _build_stored_account_payload(self, account_result: dict, api_key: str) -> dict:
        """Build one DB-ready riot_account payload including ranked metadata."""
        puuid = account_result["puuid"]
        payload = {
            "puuid": puuid,
            "game_name": account_result["raw_account"].get("gameName"),
            "tag_line": account_result["raw_account"].get("tagLine"),
            "summoner_id": None,
            "summoner_level": None,
            "profile_icon_id": None,
            "queue_type": None,
            "tier": None,
            "rank": None,
            "league_points": None,
            "wins": None,
            "losses": None,
            "raw_account": account_result["raw_account"],
            "raw_summoner": None,
            "raw_ranked_entries": [],
            "tier_sync_warning": None,
        }

        summoner_result = fetch_summoner_by_puuid(puuid, api_key)
        if "error" not in summoner_result:
            payload["summoner_id"] = summoner_result.get("id")
            payload["summoner_level"] = summoner_result.get("summoner_level")
            payload["profile_icon_id"] = summoner_result.get("profile_icon_id")
            payload["raw_summoner"] = summoner_result.get("raw_summoner")

        ranked_result = fetch_ranked_entries(puuid, api_key)
        if "error" in ranked_result:
            payload["tier_sync_warning"] = ranked_result
            return payload

        preferred_entry = select_preferred_ranked_entry(ranked_result["entries"])
        payload["raw_ranked_entries"] = ranked_result.get("entries", [])
        payload["queue_type"] = preferred_entry.get("queueType") if preferred_entry else None
        payload["tier"] = preferred_entry.get("tier") if preferred_entry else None
        payload["rank"] = preferred_entry.get("rank") if preferred_entry else None
        payload["league_points"] = preferred_entry.get("leaguePoints") if preferred_entry else None
        payload["wins"] = preferred_entry.get("wins") if preferred_entry else None
        payload["losses"] = preferred_entry.get("losses") if preferred_entry else None
        return payload

    def refresh_account_tier(self, game_name: str, tag_line: str, api_key: str) -> dict:
        """Refresh one riot_account row from Riot APIs without fetching matches."""
        conn = None
        try:
            init_db()

            account_result = fetch_account(game_name, tag_line, api_key)
            if "error" in account_result:
                return account_result

            stored_account_payload = self._build_stored_account_payload(
                account_result,
                api_key,
            )

            conn = get_connection()
            match_write_query = MatchWriteQuery(conn)
            match_write_query.store_account(stored_account_payload)
            match_write_query.commit()

            return {
                "game_name": stored_account_payload.get("game_name"),
                "tag_line": stored_account_payload.get("tag_line"),
                "puuid": stored_account_payload.get("puuid"),
                "summoner_id": stored_account_payload.get("summoner_id"),
                "queue_type": stored_account_payload.get("queue_type"),
                "tier": stored_account_payload.get("tier"),
                "rank": stored_account_payload.get("rank"),
                "league_points": stored_account_payload.get("league_points"),
                "wins": stored_account_payload.get("wins"),
                "losses": stored_account_payload.get("losses"),
                "tier_sync_warning": stored_account_payload.get("tier_sync_warning"),
                "db_path": str(DB_PATH.resolve()),
            }
        except Exception as exc:
            return {
                "error": "Failed to refresh account tier",
                "game_name": game_name,
                "tag_line": tag_line,
                "detail": str(exc),
                "db_path": str(DB_PATH.resolve()),
            }
        finally:
            if conn is not None:
                conn.close()

    def refresh_account_tiers_for_accounts(self, accounts: list[dict], api_key: str) -> dict:
        """Refresh tier metadata only for selected riot_account rows."""
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
                "selected_account_count": 0,
                "processed_account_count": 0,
                "results": [],
                "failed_accounts": [],
                "db_path": str(DB_PATH.resolve()),
                "error": "No valid accounts were provided",
            }

        results = []
        failed_accounts = []

        for account in normalized_accounts:
            result = self.refresh_account_tier(
                account["game_name"],
                account["tag_line"],
                api_key,
            )
            results.append(result)

            if "error" in result:
                failed_accounts.append({
                    "game_name": account["game_name"],
                    "tag_line": account["tag_line"],
                    "error": result["error"],
                })

        return {
            "selected_account_count": len(accounts),
            "processed_account_count": len(normalized_accounts),
            "results": results,
            "failed_accounts": failed_accounts,
            "db_path": str(DB_PATH.resolve()),
        }

    def store_recent_matches(
        self, game_name: str, tag_line: str, api_key: str, count: int = 5
    ) -> dict:
        """Fetch account and recent matches, then store each layer into SQLite."""
        conn = None
        try:
            init_db()

            account_result = fetch_account(game_name, tag_line, api_key)
            if "error" in account_result:
                return account_result

            stored_account_payload = self._build_stored_account_payload(
                account_result,
                api_key,
            )

            puuid = account_result["puuid"]
            match_ids_result = fetch_match_ids(puuid, api_key, count)
            if "error" in match_ids_result:
                return match_ids_result

            conn = get_connection()
            match_read_query = MatchReadQuery(conn)
            match_write_query = MatchWriteQuery(conn)
            match_write_query.store_account(stored_account_payload)

            requested_match_ids = [
                (match_id or "").strip()
                for match_id in match_ids_result["match_ids"]
                if (match_id or "").strip()
            ]
            existing_match_ids = match_read_query.get_existing_match_ids(
                requested_match_ids
            )
            pending_match_ids = [
                match_id
                for match_id in requested_match_ids
                if match_id not in existing_match_ids
            ]

            stored_match_ids = []
            skipped_existing_match_ids = []
            failed_matches = []

            for match_id in requested_match_ids:
                if match_id in existing_match_ids:
                    skipped_existing_match_ids.append(match_id)
                    continue

                match_result = fetch_match_detail(match_id, api_key)
                if "error" in match_result:
                    failed_matches.append({"match_id": match_id, "error": match_result})
                    continue

                match_data = match_result.get("raw_match") or {}
                match_write_query.store_match_summary(match_data)
                match_write_query.store_teams(
                    match_id, match_data.get("info", {}).get("teams", [])
                )
                match_write_query.store_participants(
                    match_id,
                    match_data.get("info", {}).get("participants", []),
                )
                stored_match_ids.append(match_id)

            match_write_query.commit()

            return {
                "game_name": stored_account_payload.get("game_name"),
                "tag_line": stored_account_payload.get("tag_line"),
                "puuid": puuid,
                "queue_type": stored_account_payload.get("queue_type"),
                "tier": stored_account_payload.get("tier"),
                "rank": stored_account_payload.get("rank"),
                "league_points": stored_account_payload.get("league_points"),
                "tier_sync_warning": stored_account_payload.get("tier_sync_warning"),
                "requested_count": count,
                "requested_match_ids": requested_match_ids,
                "existing_match_ids": sorted(existing_match_ids),
                "pending_match_ids": pending_match_ids,
                "skipped_existing_match_ids": skipped_existing_match_ids,
                "riot_detail_request_count": len(pending_match_ids),
                "stored_match_ids": stored_match_ids,
                "stored_count": len(stored_match_ids),
                "failed_matches": failed_matches,
                "db_path": str(DB_PATH.resolve()),
            }
        except Exception as exc:
            return {
                "error": "Failed to store recent matches",
                "game_name": game_name,
                "tag_line": tag_line,
                "requested_count": count,
                "detail": str(exc),
                "db_path": str(DB_PATH.resolve()),
            }
        finally:
            if conn is not None:
                conn.close()

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
