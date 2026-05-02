import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "riot_matches.db"


def get_connection() -> sqlite3.Connection:
    """Create one SQLite connection using the project DB path."""
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create required tables if they do not exist yet."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS riot_account (
            puuid TEXT PRIMARY KEY,
            game_name TEXT,
            tag_line TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            raw_json TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS match_summary (
            match_id TEXT PRIMARY KEY,
            data_version TEXT,
            game_creation INTEGER,
            game_duration INTEGER,
            game_end_timestamp INTEGER,
            game_id INTEGER,
            game_mode TEXT,
            game_name TEXT,
            game_start_timestamp INTEGER,
            game_type TEXT,
            game_version TEXT,
            map_id INTEGER,
            platform_id TEXT,
            queue_id INTEGER,
            tournament_code TEXT,
            participant_count INTEGER,
            raw_json TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS team_summary (
            match_id TEXT,
            team_id INTEGER,
            win INTEGER,
            bans_json TEXT,
            objectives_json TEXT,
            raw_json TEXT,
            PRIMARY KEY (match_id, team_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS participant_detail (
            match_id TEXT,
            puuid TEXT,
            participant_id INTEGER,
            team_id INTEGER,
            summoner_name TEXT,
            riot_id_game_name TEXT,
            riot_id_tagline TEXT,
            profile_icon INTEGER,
            summoner_level INTEGER,
            champion_id INTEGER,
            champion_name TEXT,
            champion_transform INTEGER,
            lane TEXT,
            role TEXT,
            team_position TEXT,
            individual_position TEXT,
            win INTEGER,
            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,
            kda REAL,
            total_damage_dealt_to_champions INTEGER,
            total_damage_taken INTEGER,
            damage_self_mitigated INTEGER,
            gold_earned INTEGER,
            gold_spent INTEGER,
            total_minions_killed INTEGER,
            neutral_minions_killed INTEGER,
            vision_score INTEGER,
            wards_placed INTEGER,
            wards_killed INTEGER,
            detector_wards_placed INTEGER,
            time_played INTEGER,
            total_time_spent_dead INTEGER,
            longest_time_spent_living INTEGER,
            champ_level INTEGER,
            item0 INTEGER,
            item1 INTEGER,
            item2 INTEGER,
            item3 INTEGER,
            item4 INTEGER,
            item5 INTEGER,
            item6 INTEGER,
            double_kills INTEGER,
            triple_kills INTEGER,
            quadra_kills INTEGER,
            penta_kills INTEGER,
            unreal_kills INTEGER,
            first_blood_kill INTEGER,
            first_blood_assist INTEGER,
            inhibitor_kills INTEGER,
            inhibitor_takedowns INTEGER,
            inhibitors_lost INTEGER,
            nexus_kills INTEGER,
            nexus_takedowns INTEGER,
            nexus_lost INTEGER,
            turret_kills INTEGER,
            turret_takedowns INTEGER,
            turrets_lost INTEGER,
            total_heal INTEGER,
            total_heals_on_teammates INTEGER,
            total_damage_shielded_on_teammates INTEGER,
            total_units_healed INTEGER,
            total_cc_time INTEGER,
            total_time_cc_dealt INTEGER,
            total_damage_dealt INTEGER,
            physical_damage_dealt_to_champions INTEGER,
            magic_damage_dealt_to_champions INTEGER,
            true_damage_dealt_to_champions INTEGER,
            perks_json TEXT,
            challenges_json TEXT,
            raw_json TEXT,
            PRIMARY KEY (match_id, puuid)
        )
        """
    )

    conn.commit()
    conn.close()
