from application.account_queries import (
    bootstrap_admin,
    create_user,
    get_auth_setup_status,
    get_current_user,
    get_match_detail,
    get_recent_matches_by_riot_id,
    list_accounts,
    list_users,
    login,
    search_accounts,
)
from application.match_analysis import (
    build_user_profile,
    format_kda,
    format_match_datetime,
    get_match_cs,
    get_match_position,
    get_match_result_text,
    normalize_match_detail,
    summarize_recent_matches,
)
from application.result_formatters import format_alerts, format_team_result, format_warnings
from application.table_data import extract_selected_users, extract_table_data
from application.team_building import build_teams
from repositories.dataset_repository import (
    DatasetRepository,
    clear_auth_token,
    load_auth_token,
    load_auth_username,
    load_server_base_url,
    load_theme_mode,
    save_auth_token,
    save_auth_username,
    save_dataset,
    save_server_base_url,
    save_theme_mode,
)


class TeamApp:
    @staticmethod
    def get_dataset_list():
        return DatasetRepository.list_files()

    @staticmethod
    def load_dataset(file_name):
        return DatasetRepository.load(file_name)

    @staticmethod
    def create_dataset(name):
        return DatasetRepository.create(name)

    @staticmethod
    def save_dataset(file_name, users):
        save_dataset(file_name, users)

    @staticmethod
    def delete_dataset(file_name):
        DatasetRepository.delete(file_name)

    @staticmethod
    def load_server_base_url():
        return load_server_base_url()

    @staticmethod
    def save_server_base_url(base_url):
        save_server_base_url(base_url)

    @staticmethod
    def load_auth_token():
        return load_auth_token()

    @staticmethod
    def save_auth_token(token):
        save_auth_token(token)

    @staticmethod
    def clear_auth_token():
        clear_auth_token()

    @staticmethod
    def load_auth_username():
        return load_auth_username()

    @staticmethod
    def save_auth_username(username):
        save_auth_username(username)

    @staticmethod
    def load_theme_mode():
        return load_theme_mode()

    @staticmethod
    def save_theme_mode(theme_mode):
        save_theme_mode(theme_mode)

    search_accounts = staticmethod(search_accounts)
    list_accounts = staticmethod(list_accounts)
    login = staticmethod(login)
    bootstrap_admin = staticmethod(bootstrap_admin)
    get_auth_setup_status = staticmethod(get_auth_setup_status)
    get_current_user = staticmethod(get_current_user)
    list_users = staticmethod(list_users)
    create_user = staticmethod(create_user)
    get_recent_matches_by_riot_id = staticmethod(get_recent_matches_by_riot_id)
    get_match_detail = staticmethod(get_match_detail)
    summarize_recent_matches = staticmethod(summarize_recent_matches)
    build_user_profile = staticmethod(build_user_profile)
    normalize_match_detail = staticmethod(normalize_match_detail)
    extract_table_data = staticmethod(extract_table_data)
    extract_selected_users = staticmethod(extract_selected_users)
    build_teams = staticmethod(build_teams)
    format_team_result = staticmethod(format_team_result)
    format_warnings = staticmethod(format_warnings)
    format_alerts = staticmethod(format_alerts)
    format_match_datetime = staticmethod(format_match_datetime)
    format_kda = staticmethod(format_kda)
    get_match_position = staticmethod(get_match_position)
    get_match_result_text = staticmethod(get_match_result_text)
    get_match_cs = staticmethod(get_match_cs)


team_app = TeamApp()
