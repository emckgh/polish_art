#!/usr/bin/env python3
"""
Add artworks.include_image_on_server column if missing (for server export culling).

Run once on your local database:
  python scripts/migrate_add_include_image_on_server.py
  python scripts/migrate_add_include_image_on_server.py --db data/artworks.db
"""
import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "data" / "artworks.db"
COLUMN = "include_image_on_server"


def main() -> None:
    ap = argparse.ArgumentParser(description="Add include_image_on_server column to artworks if missing.")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite database")
    args = ap.parse_args()
    db_path = args.db if args.db.is_absolute() else PROJECT_ROOT / args.db
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(artworks)")
    columns = [row[1] for row in cur.fetchall()]
    if COLUMN in columns:
        print(f"Column {COLUMN} already exists. Nothing to do.")
        conn.close()
        return
    cur.execute(f"ALTER TABLE artworks ADD COLUMN {COLUMN} INTEGER DEFAULT 1")
    cur.execute(f"UPDATE artworks SET {COLUMN} = 1 WHERE {COLUMN} IS NULL")
    conn.commit()
    conn.close()
    print(f"Added column {COLUMN} and set default to 1 for existing rows.")


if __name__ == "__main__":
    main()
