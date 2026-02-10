#!/usr/bin/env python3
"""
Create a small SQLite extract of data/artworks.db for test/deploy (e.g. under 100MB for PA).

Usage:
  python scripts/extract_db_sample.py [--limit N] [--strip-images] [--output PATH]

  --limit N       Number of artworks to include (default: 100)
  --strip-images  Set image_data to NULL in copies (saves most of the size; default: True for small extract)
  --output PATH   Output file (default: data/artworks_extract.db)

Preserves referential integrity: related rows in provenances, matches, image_features,
vision_api_requests/matches/entities are copied for the selected artworks.
vision_api_domain_stats is copied in full (small table).
"""
import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "artworks.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "artworks_extract.db"

# Tables that reference artworks (artwork_id or both sides of match)
ARTWORK_TABLES = [
    "artworks",
    "provenances",
    "matches",
    "image_features",
    "vision_api_requests",
]
# vision_api_matches and vision_api_entities reference vision_api_requests
REQUEST_TABLES = ["vision_api_matches", "vision_api_entities"]
# Standalone (copy all or filter by artwork IDs in JSON)
OTHER_TABLES = ["vision_api_domain_stats"]


def get_create_sql(conn: sqlite3.Connection, table: str) -> Optional[str]:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=? AND sql IS NOT NULL",
        (table,),
    ).fetchone()
    return row[0] if row else None


def list_tables(conn: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]


def extract(
    source_path: Path,
    output_path: Path,
    limit: int,
    strip_images: bool,
) -> None:
    if not source_path.exists():
        print(f"Source database not found: {source_path}", file=sys.stderr)
        sys.exit(1)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(source_path)
    src.row_factory = sqlite3.Row

    # Create empty dest with same schema
    if output_path.exists():
        output_path.unlink()
    dest = sqlite3.connect(output_path)
    dest.row_factory = sqlite3.Row

    tables = list_tables(src)
    for t in tables:
        sql = get_create_sql(src, t)
        if sql:
            dest.execute(sql)

    # Pick N artwork IDs (order by rowid for deterministic subset)
    cursor = src.execute(
        "SELECT id FROM artworks ORDER BY rowid LIMIT ?", (limit,)
    )
    artwork_ids = [r[0] for r in cursor.fetchall()]
    if not artwork_ids:
        print("No artworks in source database.", file=sys.stderr)
        sys.exit(1)

    placeholders = ",".join("?" * len(artwork_ids))

    # Copy artworks (optionally strip image_data)
    if strip_images:
        cur = src.execute(
            "SELECT id, title, artist_name, artist_birth_year, artist_death_year, artist_nationality, "
            "creation_year, description, status, image_url, NULL AS image_data, image_mime_type, image_hash, "
            "last_known_location, last_known_date, created_at, updated_at FROM artworks WHERE id IN ("
            + placeholders
            + ")",
            artwork_ids,
        )
    else:
        cur = src.execute(
            "SELECT * FROM artworks WHERE id IN (" + placeholders + ")",
            artwork_ids,
        )
    rows = cur.fetchall()
    if not rows:
        dest.close()
        src.close()
        sys.exit(1)
    cols = list(rows[0].keys())
    for row in rows:
        dest.execute(
            "INSERT INTO artworks (" + ",".join(cols) + ") VALUES (" + ",".join("?" * len(cols)) + ")",
            tuple(row[c] for c in cols),
        )

    def copy_table(name: str, select_sql: str, params: list) -> None:
        try:
            for row in src.execute(select_sql, params).fetchall():
                dest.execute(
                    "INSERT INTO " + name + " VALUES (" + ",".join("?" * len(row)) + ")",
                    tuple(row),
                )
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e).lower():
                raise

    # provenances
    copy_table(
        "provenances",
        "SELECT * FROM provenances WHERE artwork_id IN (" + placeholders + ")",
        artwork_ids,
    )

    # matches (both query and candidate in our set)
    copy_table(
        "matches",
        "SELECT * FROM matches WHERE query_artwork_id IN (" + placeholders + ") AND candidate_artwork_id IN (" + placeholders + ")",
        artwork_ids + artwork_ids,
    )

    # image_features
    copy_table(
        "image_features",
        "SELECT * FROM image_features WHERE artwork_id IN (" + placeholders + ")",
        artwork_ids,
    )

    # vision_api_requests
    request_ids = []
    try:
        for row in src.execute(
            "SELECT * FROM vision_api_requests WHERE artwork_id IN (" + placeholders + ")",
            artwork_ids,
        ).fetchall():
            request_ids.append(row["id"])
            dest.execute(
                "INSERT INTO vision_api_requests VALUES (" + ",".join("?" * len(row)) + ")",
                tuple(row),
            )
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e).lower():
            raise

    req_placeholders = ",".join("?" * len(request_ids)) if request_ids else ""

    # vision_api_matches
    if request_ids:
        copy_table(
            "vision_api_matches",
            "SELECT * FROM vision_api_matches WHERE request_id IN (" + req_placeholders + ")",
            request_ids,
        )

    # vision_api_entities
    if request_ids:
        copy_table(
            "vision_api_entities",
            "SELECT * FROM vision_api_entities WHERE request_id IN (" + req_placeholders + ")",
            request_ids,
        )

    # vision_api_domain_stats (copy all; small)
    try:
        for row in src.execute("SELECT * FROM vision_api_domain_stats").fetchall():
            dest.execute(
                "INSERT INTO vision_api_domain_stats VALUES (" + ",".join("?" * len(row)) + ")",
                tuple(row),
            )
    except sqlite3.OperationalError:
        pass  # Table might not exist in older DBs

    dest.commit()
    dest.close()
    src.close()

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {output_path} ({size_mb:.2f} MB) with {len(artwork_ids)} artworks (strip_images={strip_images}).")


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a small SQLite extract for test/deploy.")
    ap.add_argument("--limit", type=int, default=100, help="Number of artworks (default: 100)")
    ap.add_argument(
        "--strip-images",
        action="store_true",
        default=True,
        help="Set image_data to NULL to reduce size (default: True)",
    )
    ap.add_argument(
        "--no-strip-images",
        action="store_false",
        dest="strip_images",
        help="Keep image_data in extract (larger file)",
    )
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output DB path")
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Source DB path")
    args = ap.parse_args()

    extract(args.source, args.output, args.limit, args.strip_images)


if __name__ == "__main__":
    main()
