from api_clients.match_api_client import MatchApiClient


def search_accounts(keyword, limit=20):
    client = MatchApiClient()
    return client.search_accounts(keyword, limit)


def get_recent_matches_by_riot_id(game_name, tag_line, limit=10):
    client = MatchApiClient()
    return client.get_recent_matches_by_riot_id(game_name, tag_line, limit)


def get_match_detail(match_id):
    client = MatchApiClient()
    return client.get_match_detail(match_id)
