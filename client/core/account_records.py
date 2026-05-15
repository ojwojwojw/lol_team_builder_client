def dedupe_accounts(accounts):
    """Keep the latest unique Riot IDs while preserving non-standard rows."""
    sorted_accounts = sorted(
        accounts or [],
        key=lambda account: (
            str((account or {}).get("fetched_at") or ""),
            str((account or {}).get("id") or ""),
        ),
        reverse=True,
    )

    seen = set()
    deduped = []
    for account in sorted_accounts:
        if not isinstance(account, dict):
            continue

        game_name = str(account.get("game_name") or "").strip().lower()
        tag_line = str(account.get("tag_line") or "").strip().lower()
        if not game_name or not tag_line:
            deduped.append(account)
            continue

        key = (game_name, tag_line)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(account)

    return deduped
