import sqlite3


class MatchReadQuery:
    # Query contains read SQL only. Response shaping stays in the service.

    def __init__(self, connection: sqlite3.Connection):
        """Bind one SQLite connection and reuse its cursor for read operations."""
        self.connection = connection
        self.cursor = connection.cursor()
        self.cursor.row_factory = None

    def get_recent_matches_by_puuid(self, puuid: str, limit: int) -> list[dict]:
        """Return recent matches for one player using stored participant rows."""
        self.cursor.execute(
            """
            SELECT
                m.match_id,
                m.game_mode,
                m.queue_id,
                m.game_creation,
                m.game_start_timestamp,
                m.game_duration,
                p.puuid,
                p.summoner_name,
                p.riot_id_game_name,
                p.riot_id_tagline,
                p.team_id,
                p.team_position,
                p.lane,
                p.role,
                p.champion_name,
                p.win,
                p.kills,
                p.deaths,
                p.assists,
                p.kda,
                p.total_damage_dealt_to_champions,
                p.total_damage_taken,
                p.gold_earned,
                p.total_minions_killed,
                p.vision_score,
                p.item0,
                p.item1,
                p.item2,
                p.item3,
                p.item4,
                p.item5,
                p.item6
            FROM participant_detail AS p
            JOIN match_summary AS m
                ON m.match_id = p.match_id
            WHERE p.puuid = ?
            ORDER BY m.game_start_timestamp DESC
            LIMIT ?
            """,
            (puuid, limit),
        )
        return self._fetch_dicts()

    def get_accounts_by_game_name(self, game_name: str) -> list[dict]:
        """Return stored riot_account rows for one game name."""
        self.cursor.execute(
            """
            SELECT
                puuid,
                game_name,
                tag_line,
                fetched_at,
                raw_json
            FROM riot_account
            WHERE game_name = ?
            ORDER BY fetched_at DESC
            """,
            (game_name,),
        )
        return self._fetch_dicts()

    def list_accounts(self, limit: int) -> list[dict]:
        """Return stored riot_account rows ordered by latest fetch time."""
        self.cursor.execute(
            """
            SELECT
                puuid,
                game_name,
                tag_line,
                fetched_at,
                raw_json
            FROM riot_account
            ORDER BY fetched_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return self._fetch_dicts()

    def search_accounts_by_game_name(self, keyword: str, limit: int) -> list[dict]:
        """Return riot_account rows using a LIKE search on game_name."""
        self.cursor.execute(
            """
            SELECT
                puuid,
                game_name,
                tag_line,
                fetched_at,
                raw_json
            FROM riot_account
            WHERE game_name LIKE ?
            ORDER BY fetched_at DESC
            LIMIT ?
            """,
            (f"%{keyword}%", limit),
        )
        return self._fetch_dicts()

    def get_recent_matches_by_riot_id(
        self, game_name: str, tag_line: str, limit: int
    ) -> list[dict]:
        """Return recent matches using Riot ID stored in participant rows."""
        self.cursor.execute(
            """
            SELECT
                m.match_id,
                m.game_mode,
                m.queue_id,
                m.game_creation,
                m.game_start_timestamp,
                m.game_duration,
                p.puuid,
                p.summoner_name,
                p.riot_id_game_name,
                p.riot_id_tagline,
                p.team_id,
                p.team_position,
                p.lane,
                p.role,
                p.champion_name,
                p.win,
                p.kills,
                p.deaths,
                p.assists,
                p.kda,
                p.total_damage_dealt_to_champions,
                p.total_damage_taken,
                p.gold_earned,
                p.total_minions_killed,
                p.vision_score,
                p.item0,
                p.item1,
                p.item2,
                p.item3,
                p.item4,
                p.item5,
                p.item6
            FROM participant_detail AS p
            JOIN match_summary AS m
                ON m.match_id = p.match_id
            WHERE p.riot_id_game_name = ? AND p.riot_id_tagline = ?
            ORDER BY m.game_start_timestamp DESC
            LIMIT ?
            """,
            (game_name, tag_line, limit),
        )
        return self._fetch_dicts()

    def get_match_summary(self, match_id: str) -> dict | None:
        """Return one stored match summary row."""
        self.cursor.execute(
            """
            SELECT
                match_id,
                data_version,
                game_creation,
                game_duration,
                game_end_timestamp,
                game_id,
                game_mode,
                game_name,
                game_start_timestamp,
                game_type,
                game_version,
                map_id,
                platform_id,
                queue_id,
                tournament_code,
                participant_count
            FROM match_summary
            WHERE match_id = ?
            """,
            (match_id,),
        )
        return self._fetch_one_dict()

    def get_match_teams(self, match_id: str) -> list[dict]:
        """Return stored team rows for one match."""
        self.cursor.execute(
            """
            SELECT
                match_id,
                team_id,
                win,
                bans_json,
                objectives_json
            FROM team_summary
            WHERE match_id = ?
            ORDER BY team_id
            """,
            (match_id,),
        )
        return self._fetch_dicts()

    def get_match_participants(self, match_id: str) -> list[dict]:
        """Return participant rows for one stored match."""
        self.cursor.execute(
            """
            SELECT
                match_id,
                puuid,
                participant_id,
                team_id,
                summoner_name,
                riot_id_game_name,
                riot_id_tagline,
                champion_name,
                team_position,
                lane,
                role,
                win,
                kills,
                deaths,
                assists,
                kda,
                total_damage_dealt_to_champions,
                total_damage_taken,
                gold_earned,
                total_minions_killed,
                neutral_minions_killed,
                vision_score,
                wards_placed,
                wards_killed,
                detector_wards_placed,
                champ_level,
                item0,
                item1,
                item2,
                item3,
                item4,
                item5,
                item6,
                perks_json,
                challenges_json
            FROM participant_detail
            WHERE match_id = ?
            ORDER BY participant_id
            """,
            (match_id,),
        )
        return self._fetch_dicts()

    def _fetch_dicts(self) -> list[dict]:
        """Convert cursor results into a list of dictionaries."""
        columns = [column[0] for column in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def _fetch_one_dict(self) -> dict | None:
        """Convert one cursor row into a dictionary or None."""
        row = self.cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in self.cursor.description]
        return dict(zip(columns, row))
