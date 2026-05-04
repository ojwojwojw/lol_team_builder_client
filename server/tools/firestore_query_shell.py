from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.backend.firestore_store import get_client


HELP_TEXT = """Commands:
  help
  collections
  show <collection> [limit]
  get <collection> <document_id>
  exit
"""


def list_collections() -> None:
    client = get_client()
    collections = sorted(collection.id for collection in client.collections())
    if not collections:
        print("(no collections)")
        return

    for name in collections:
        print(name)


def show_collection(collection_name: str, limit: int = 20) -> None:
    docs = get_client().collection(collection_name).limit(limit).stream()
    count = 0
    for snapshot in docs:
        payload = snapshot.to_dict() or {}
        print(f"[{snapshot.id}]")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print()
        count += 1

    if count == 0:
        print("(no documents)")


def get_document(collection_name: str, document_id: str) -> None:
    snapshot = get_client().collection(collection_name).document(document_id).get()
    if not snapshot.exists:
        print("document not found")
        return

    payload = snapshot.to_dict() or {}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    print("Firestore query shell")
    print(HELP_TEXT)

    while True:
        try:
            raw = input("firestore> ").strip()
        except EOFError:
            break

        if not raw:
            continue
        if raw.lower() in {"exit", "quit"}:
            break
        if raw.lower() == "help":
            print(HELP_TEXT)
            continue
        if raw.lower() == "collections":
            list_collections()
            continue

        parts = raw.split()
        command = parts[0].lower()

        try:
            if command == "show" and len(parts) >= 2:
                limit = int(parts[2]) if len(parts) >= 3 else 20
                show_collection(parts[1], limit)
            elif command == "get" and len(parts) >= 3:
                get_document(parts[1], parts[2])
            else:
                print("unknown command")
                print(HELP_TEXT)
        except Exception as exc:
            print(f"error: {exc}")

    print("bye")


if __name__ == "__main__":
    main()
