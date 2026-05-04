from api_clients.auth_api_client import AuthApiClient
from api_clients.match_api_client import MatchApiClient


def search_accounts(keyword, limit=20):
    client = MatchApiClient()
    return client.search_accounts(keyword, limit)


def list_accounts(limit=20):
    client = MatchApiClient()
    return client.list_accounts(limit)


def get_recent_matches_by_riot_id(game_name, tag_line, limit=10):
    client = MatchApiClient()
    return client.get_recent_matches_by_riot_id(game_name, tag_line, limit)


def get_match_detail(match_id):
    client = MatchApiClient()
    return client.get_match_detail(match_id)


def login(username, password):
    client = AuthApiClient()
    return client.login(username, password)


def bootstrap_admin(username, password):
    client = AuthApiClient()
    return client.bootstrap_admin(username, password)


def get_auth_setup_status():
    client = AuthApiClient()
    return client.get_setup_status()


def get_current_user():
    client = AuthApiClient()
    return client.get_me()


def list_users():
    client = AuthApiClient()
    return client.list_users()


def create_user(username, password):
    client = AuthApiClient()
    return client.create_user(username, password)
