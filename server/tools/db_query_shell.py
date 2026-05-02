import sqlite3

try:
    from .common import DB_PATH
except ImportError:
    from common import DB_PATH


def main():
    print("SQLite query shell (type exit to quit)")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    while True:
        try:
            sql = input("SQL> ").strip()
            if sql.lower() in ("exit", "quit"):
                break
            if not sql:
                continue

            cursor.execute(sql)
            if sql.lower().startswith("select"):
                rows = cursor.fetchall()
                headers = [column[0] for column in cursor.description]
                print("\t".join(headers))
                for row in rows:
                    print("\t".join(str(value) for value in row))
            else:
                conn.commit()
                print("Query executed.")
        except Exception as exc:
            print(f"Error: {exc}")

    conn.close()
    print("Bye.")


if __name__ == "__main__":
    main()
