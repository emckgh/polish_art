#!/usr/bin/env python3
"""
Build a server export SQLite DB from local data/artworks.db with culling options.

Use this to produce a file to rsync to your VPS. Run on your LAN machine.

Usage:
  python scripts/build_and_sync_server_db.py --output data/server_export.db
  python scripts/build_and_sync_server_db.py --output data/server_export.db --strip-images-unless-include --no-vision-detail

Culling options:
  --strip-all-images           Set image_data to NULL for all artworks (smallest export).
  --strip-images-unless-include  Keep image_data only where artworks.include_image_on_server is 1 (column must exist).
  --strip-images-unless-interesting  Keep image_data only for artworks that have at least one vision_api_requests row with has_interesting_results=1.
  --no-vision-detail           Omit vision_api_matches and vision_api_entities (keep vision_api_requests and vision_api_domain_stats).
  --no-image-features          Omit image_features table.
  --no-matches                 Omit matches table.
  --no-provenances             Omit provenances table.

If no strip-* option is given, image_data is copied for all artworks (largest export).
"""
import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "artworks.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "server_export.db"


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


def table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def build_export(
    source_path: Path,
    output_path: Path,
    limit: Optional[int],
    strip_all_images: bool,
    strip_images_unless_include: bool,
    strip_images_unless_interesting: bool,
    no_vision_detail: bool,
    no_image_features: bool,
    no_matches: bool,
    no_provenances: bool,
) -> None:
    if not source_path.exists():
        print(f"Source database not found: {source_path}", file=sys.stderr)
        sys.exit(1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(source_path)
    src.row_factory = sqlite3.Row
    if output_path.exists():
        output_path.unlink()
    dest = sqlite3.connect(output_path)
    dest.row_factory = sqlite3.Row
    tables = list_tables(src)
    for t in tables:
        sql = get_create_sql(src, t)
        if sql:
            dest.execute(sql)
    if limit is not None:
        cursor = src.execute("SELECT id FROM artworks ORDER BY rowid LIMIT ?", (limit,))
    else:
        cursor = src.execute("SELECT id FROM artworks ORDER BY rowid")
    artwork_ids = [r[0] for r in cursor.fetchall()]
    if not artwork_ids:
        print("No artworks in source database.", file=sys.stderr)
        dest.close()
        src.close()
        sys.exit(1)
    placeholders = ",".join("?" * len(artwork_ids))
    has_include_col = table_has_column(src, "artworks", "include_image_on_server")
    artwork_ids_to_keep_image = set()
    if strip_images_unless_interesting:
        try:
            cur = src.execute(
                "SELECT DISTINCT artwork_id FROM vision_api_requests WHERE has_interesting_results = 1"
            )
            artwork_ids_to_keep_image = {r[0] for r in cur.fetchall()}
        except sqlite3.OperationalError:
            pass
    if strip_all_images:
        select_cols = (
            "id, title, artist_name, artist_birth_year, artist_death_year, artist_nationality, "
            "creation_year, description, status, image_url, NULL AS image_data, image_mime_type, image_hash, "
            "last_known_location, last_known_date, created_at, updated_at"
        )
        if has_include_col:
            select_cols += ", include_image_on_server"
        cur = src.execute(
            f"SELECT {select_cols} FROM artworks WHERE id IN ({placeholders})",
            artwork_ids,
        )
        rows = cur.fetchall()
        cols = list(rows[0].keys())
        for row in rows:
            dest.execute(
                "INSERT INTO artworks (" + ",".join(cols) + ") VALUES (" + ",".join("?" * len(cols)) + ")",
                tuple(row[c] for c in cols),
            )
    elif strip_images_unless_include and has_include_col:
        cur = src.execute(
            "SELECT id, title, artist_name, artist_birth_year, artist_death_year, artist_nationality, "
            "creation_year, description, status, image_url, "
            "CASE WHEN include_image_on_server = 1 THEN image_data ELSE NULL END AS image_data, "
            "image_mime_type, image_hash, last_known_location, last_known_date, created_at, updated_at, include_image_on_server "
            f"FROM artworks WHERE id IN ({placeholders})",
            artwork_ids,
        )
        rows = cur.fetchall()
        cols = list(rows[0].keys())
        for row in rows:
            dest.execute(
                "INSERT INTO artworks (" + ",".join(cols) + ") VALUES (" + ",".join("?" * len(cols)) + ")",
                tuple(row[c] for c in cols),
            )
    elif strip_images_unless_interesting:
        cur = src.execute(f"SELECT * FROM artworks WHERE id IN ({placeholders})", artwork_ids)
        rows = cur.fetchall()
        cols = list(rows[0].keys())
        for row in rows:
            r = dict(row)
            if r["id"] not in artwork_ids_to_keep_image:
                r["image_data"] = None
            dest.execute(
                "INSERT INTO artworks (" + ",".join(cols) + ") VALUES (" + ",".join("?" * len(cols)) + ")",
                tuple(r[c] for c in cols),
            )
    else:
        cur = src.execute(f"SELECT * FROM artworks WHERE id IN ({placeholders})", artwork_ids)
        rows = cur.fetchall()
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

    if not no_provenances:
        copy_table(
            "provenances",
            "SELECT * FROM provenances WHERE artwork_id IN (" + placeholders + ")",
            artwork_ids,
        )
    if not no_matches:
        copy_table(
            "matches",
            "SELECT * FROM matches WHERE query_artwork_id IN ("
            + placeholders
            + ") AND candidate_artwork_id IN ("
            + placeholders
            + ")",
            artwork_ids + artwork_ids,
        )
    if not no_image_features:
        copy_table(
            "image_features",
            "SELECT * FROM image_features WHERE artwork_id IN (" + placeholders + ")",
            artwork_ids,
        )
    request_ids = []
    try:
        for row in src.execute(
            "SELECT * FROM vision_api_requests WHERE artwork_id IN (" + placeholders + ")",
            artwork_ids,
        ).fetchall():
            request_ids.append(row["id"])
            dest.execute(
                "INSERT INTO vision_api_requests VALUES ("
                + ",".join("?" * len(row))
                + ")",
                tuple(row),
            )
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e).lower():
            raise
    req_placeholders = ",".join("?" * len(request_ids)) if request_ids else ""
    if not no_vision_detail and request_ids:
        copy_table(
            "vision_api_matches",
            "SELECT * FROM vision_api_matches WHERE request_id IN (" + req_placeholders + ")",
            request_ids,
        )
        copy_table(
            "vision_api_entities",
            "SELECT * FROM vision_api_entities WHERE request_id IN (" + req_placeholders + ")",
            request_ids,
        )
    try:
        for row in src.execute("SELECT * FROM vision_api_domain_stats").fetchall():
            dest.execute(
                "INSERT INTO vision_api_domain_stats VALUES (" + ",".join("?" * len(row)) + ")",
                tuple(row),
            )
    except sqlite3.OperationalError:
        pass
    dest.commit()
    dest.close()
    src.close()
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {output_path} ({size_mb:.2f} MB) with {len(artwork_ids)} artworks.")
    print("To sync to VPS: rsync -avz", str(output_path), "polishart@YOUR_VPS:polish_art/data/artworks.db")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build server export DB with culling options. Run locally; then rsync to VPS."
    )
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Source SQLite DB")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output export DB path")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of artworks (default: all)")
    ap.add_argument(
        "--strip-all-images",
        action="store_true",
        help="Set image_data to NULL for all artworks",
    )
    ap.add_argument(
        "--strip-images-unless-include",
        action="store_true",
        help="Keep image_data only where artworks.include_image_on_server is 1",
    )
    ap.add_argument(
        "--strip-images-unless-interesting",
        action="store_true",
        help="Keep image_data only for artworks with has_interesting_results in vision_api_requests",
    )
    ap.add_argument(
        "--no-vision-detail",
        action="store_true",
        help="Omit vision_api_matches and vision_api_entities",
    )
    ap.add_argument("--no-image-features", action="store_true", help="Omit image_features table")
    ap.add_argument("--no-matches", action="store_true", help="Omit matches table")
    ap.add_argument("--no-provenances", action="store_true", help="Omit provenances table")
    args = ap.parse_args()
    source = args.source if args.source.is_absolute() else PROJECT_ROOT / args.source
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    strip_policy = sum(
        [
            args.strip_all_images,
            args.strip_images_unless_include,
            args.strip_images_unless_interesting,
        ]
    )
    if strip_policy > 1:
        print("Use at most one of --strip-all-images, --strip-images-unless-include, --strip-images-unless-interesting.", file=sys.stderr)
        sys.exit(1)
    build_export(
        source_path=source,
        output_path=output,
        limit=args.limit,
        strip_all_images=args.strip_all_images,
        strip_images_unless_include=args.strip_images_unless_include,
        strip_images_unless_interesting=args.strip_images_unless_interesting,
        no_vision_detail=args.no_vision_detail,
        no_image_features=args.no_image_features,
        no_matches=args.no_matches,
        no_provenances=args.no_provenances,
    )


if __name__ == "__main__":
    main()
