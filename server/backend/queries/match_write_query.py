import json
import sqlite3


def to_json_text(value):
    """Convert nested Python data to JSON text for raw backup columns."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


class MatchWriteQuery:
    # Query contains write SQL only. Business orchestration stays in the service.

    def __init__(self, connection: sqlite3.Connection):
        """Bind one SQLite connection and reuse its cursor for this unit of work."""
        self.connection = connection
        self.cursor = connection.cursor()

    def store_account(self, account: dict) -> None:
        """Insert or refresh one riot_account row with ranked metadata."""
        self.cursor.execute(
            """
            INSERT INTO riot_account (
                puuid,
                game_name,
                tag_line,
                summoner_id,
                summoner_level,
                profile_icon_id,
                queue_type,
                tier,
                rank,
                league_points,
                wins,
                losses,
                fetched_at,
                raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(puuid) DO UPDATE SET
                game_name = excluded.game_name,
                tag_line = excluded.tag_line,
                summoner_id = COALESCE(excluded.summoner_id, riot_account.summoner_id),
                summoner_level = COALESCE(excluded.summoner_level, riot_account.summoner_level),
                profile_icon_id = COALESCE(excluded.profile_icon_id, riot_account.profile_icon_id),
                queue_type = CASE
                    WHEN json_extract(excluded.raw_json, '$.tier_sync_warning.error') IS NOT NULL
                        THEN riot_account.queue_type
                    ELSE excluded.queue_type
                END,
                tier = CASE
                    WHEN json_extract(excluded.raw_json, '$.tier_sync_warning.error') IS NOT NULL
                        THEN riot_account.tier
                    ELSE excluded.tier
                END,
                rank = CASE
                    WHEN json_extract(excluded.raw_json, '$.tier_sync_warning.error') IS NOT NULL
                        THEN riot_account.rank
                    ELSE excluded.rank
                END,
                league_points = CASE
                    WHEN json_extract(excluded.raw_json, '$.tier_sync_warning.error') IS NOT NULL
                        THEN riot_account.league_points
                    ELSE excluded.league_points
                END,
                wins = CASE
                    WHEN json_extract(excluded.raw_json, '$.tier_sync_warning.error') IS NOT NULL
                        THEN riot_account.wins
                    ELSE excluded.wins
                END,
                losses = CASE
                    WHEN json_extract(excluded.raw_json, '$.tier_sync_warning.error') IS NOT NULL
                        THEN riot_account.losses
                    ELSE excluded.losses
                END,
                fetched_at = CURRENT_TIMESTAMP,
                raw_json = excluded.raw_json
            """,
            (
                account.get("puuid"),
                account.get("game_name"),
                account.get("tag_line"),
                account.get("summoner_id"),
                account.get("summoner_level"),
                account.get("profile_icon_id"),
                account.get("queue_type"),
                account.get("tier"),
                account.get("rank"),
                account.get("league_points"),
                account.get("wins"),
                account.get("losses"),
                to_json_text(account),
            ),
        )

    def store_match_summary(self, match_data: dict) -> None:
        """Insert one row of match-level metadata into match_summary."""
        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})
        self.cursor.execute(
            """
            INSERT INTO match_summary (
                match_id, data_version, game_creation, game_duration, game_end_timestamp,
                game_id, game_mode, game_name, game_start_timestamp, game_type,
                game_version, map_id, platform_id, queue_id, tournament_code,
                participant_count, raw_json
            )
            SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM match_summary WHERE match_id = ?
            )
            """,
            (
                metadata.get("matchId"),
                metadata.get("dataVersion"),
                info.get("gameCreation"),
                info.get("gameDuration"),
                info.get("gameEndTimestamp"),
                info.get("gameId"),
                info.get("gameMode"),
                info.get("gameName"),
                info.get("gameStartTimestamp"),
                info.get("gameType"),
                info.get("gameVersion"),
                info.get("mapId"),
                info.get("platformId"),
                info.get("queueId"),
                info.get("tournamentCode"),
                len(info.get("participants", [])),
                to_json_text(match_data),
                metadata.get("matchId"),
            ),
        )

    def store_teams(self, match_id: str, teams: list) -> None:
        """Insert team rows for one match into team_summary."""
        for team in teams:
            self.cursor.execute(
                """
                INSERT INTO team_summary (
                    match_id, team_id, win, bans_json, objectives_json, raw_json
                )
                SELECT ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM team_summary WHERE match_id = ? AND team_id = ?
                )
                """,
                (
                    match_id,
                    team.get("teamId"),
                    int(bool(team.get("win"))),
                    to_json_text(team.get("bans")),
                    to_json_text(team.get("objectives")),
                    to_json_text(team),
                    match_id,
                    team.get("teamId"),
                ),
            )

    def store_participants(self, match_id: str, participants: list) -> None:
        """Insert participant detail rows for one match.

        When adding a new stat column, update both `columns` and `values`
        in the same order.
        """
        columns = [
            "match_id",
            "puuid",
            "participant_id",
            "team_id",
            "summoner_name",
            "riot_id_game_name",
            "riot_id_tagline",
            "profile_icon",
            "summoner_level",
            "champion_id",
            "champion_name",
            "champion_transform",
            "lane",
            "role",
            "team_position",
            "individual_position",
            "win",
            "kills",
            "deaths",
            "assists",
            "kda",
            "total_damage_dealt_to_champions",
            "total_damage_taken",
            "damage_self_mitigated",
            "gold_earned",
            "gold_spent",
            "total_minions_killed",
            "neutral_minions_killed",
            "vision_score",
            "wards_placed",
            "wards_killed",
            "detector_wards_placed",
            "time_played",
            "total_time_spent_dead",
            "longest_time_spent_living",
            "champ_level",
            "item0",
            "item1",
            "item2",
            "item3",
            "item4",
            "item5",
            "item6",
            "double_kills",
            "triple_kills",
            "quadra_kills",
            "penta_kills",
            "unreal_kills",
            "first_blood_kill",
            "first_blood_assist",
            "inhibitor_kills",
            "inhibitor_takedowns",
            "inhibitors_lost",
            "nexus_kills",
            "nexus_takedowns",
            "nexus_lost",
            "turret_kills",
            "turret_takedowns",
            "turrets_lost",
            "total_heal",
            "total_heals_on_teammates",
            "total_damage_shielded_on_teammates",
            "total_units_healed",
            "total_cc_time",
            "total_time_cc_dealt",
            "total_damage_dealt",
            "physical_damage_dealt_to_champions",
            "magic_damage_dealt_to_champions",
            "true_damage_dealt_to_champions",
            "perks_json",
            "challenges_json",
            "raw_json",
        ]

        for participant in participants:
            values = (
                match_id,
                participant.get("puuid"),
                participant.get("participantId"),
                participant.get("teamId"),
                participant.get("summonerName"),
                participant.get("riotIdGameName"),
                participant.get("riotIdTagline"),
                participant.get("profileIcon"),
                participant.get("summonerLevel"),
                participant.get("championId"),
                participant.get("championName"),
                participant.get("championTransform"),
                participant.get("lane"),
                participant.get("role"),
                participant.get("teamPosition"),
                participant.get("individualPosition"),
                int(bool(participant.get("win"))),
                participant.get("kills"),
                participant.get("deaths"),
                participant.get("assists"),
                participant.get("challenges", {}).get("kda"),
                participant.get("totalDamageDealtToChampions"),
                participant.get("totalDamageTaken"),
                participant.get("damageSelfMitigated"),
                participant.get("goldEarned"),
                participant.get("goldSpent"),
                participant.get("totalMinionsKilled"),
                participant.get("neutralMinionsKilled"),
                participant.get("visionScore"),
                participant.get("wardsPlaced"),
                participant.get("wardsKilled"),
                participant.get("detectorWardsPlaced"),
                participant.get("timePlayed"),
                participant.get("totalTimeSpentDead"),
                participant.get("longestTimeSpentLiving"),
                participant.get("champLevel"),
                participant.get("item0"),
                participant.get("item1"),
                participant.get("item2"),
                participant.get("item3"),
                participant.get("item4"),
                participant.get("item5"),
                participant.get("item6"),
                participant.get("doubleKills"),
                participant.get("tripleKills"),
                participant.get("quadraKills"),
                participant.get("pentaKills"),
                participant.get("unrealKills"),
                int(bool(participant.get("firstBloodKill"))),
                int(bool(participant.get("firstBloodAssist"))),
                participant.get("inhibitorKills"),
                participant.get("inhibitorTakedowns"),
                participant.get("inhibitorsLost"),
                participant.get("nexusKills"),
                participant.get("nexusTakedowns"),
                participant.get("nexusLost"),
                participant.get("turretKills"),
                participant.get("turretTakedowns"),
                participant.get("turretsLost"),
                participant.get("totalHeal"),
                participant.get("totalHealsOnTeammates"),
                participant.get("totalDamageShieldedOnTeammates"),
                participant.get("totalUnitsHealed"),
                participant.get("totalCCDealt"),
                participant.get("timeCCingOthers"),
                participant.get("totalDamageDealt"),
                participant.get("physicalDamageDealtToChampions"),
                participant.get("magicDamageDealtToChampions"),
                participant.get("trueDamageDealtToChampions"),
                to_json_text(participant.get("perks")),
                to_json_text(participant.get("challenges")),
                to_json_text(participant),
                match_id,
                participant.get("puuid"),
            )

            self.cursor.execute(
                f"""
                INSERT INTO participant_detail (
                    {", ".join(columns)}
                )
                SELECT {", ".join(["?" for _ in columns])}
                WHERE NOT EXISTS (
                    SELECT 1 FROM participant_detail WHERE match_id = ? AND puuid = ?
                )
                """,
                values,
            )

    def commit(self) -> None:
        """Commit all pending inserts for the current connection."""
        self.connection.commit()
