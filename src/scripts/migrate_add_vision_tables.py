#!/usr/bin/env python3
"""
Migration: Add Vision API tracking tables.

Creates vision_api_requests, vision_api_matches, vision_api_entities, 
and vision_api_domain_stats tables if they don't exist.

Usage:
    python src/scripts/migrate_add_vision_tables.py
"""
import sqlite3
import sys
from pathlib import Path


def main() -> None:
    db_path = Path("data/artworks.db")
    
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("Creating Vision API tables...")
    
    # Check if tables already exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cur.fetchall()}
    
    # vision_api_requests table
    if 'vision_api_requests' not in existing_tables:
        print("Creating vision_api_requests table...")
        cur.execute("""
            CREATE TABLE vision_api_requests (
                id TEXT PRIMARY KEY,
                artwork_id TEXT NOT NULL,
                request_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                image_source TEXT NOT NULL,
                api_cost_units INTEGER NOT NULL DEFAULT 1,
                total_full_matches INTEGER NOT NULL DEFAULT 0,
                total_partial_matches INTEGER NOT NULL DEFAULT 0,
                total_similar_images INTEGER NOT NULL DEFAULT 0,
                total_pages_with_image INTEGER NOT NULL DEFAULT 0,
                best_match_score REAL,
                has_interesting_results INTEGER NOT NULL DEFAULT 0,
                processing_time_ms INTEGER,
                FOREIGN KEY (artwork_id) REFERENCES artworks (id)
            )
        """)
        cur.execute("""
            CREATE INDEX idx_vision_requests_artwork 
            ON vision_api_requests(artwork_id)
        """)
        cur.execute("""
            CREATE INDEX idx_vision_requests_interesting 
            ON vision_api_requests(has_interesting_results)
        """)
        print("✓ Created vision_api_requests table")
    else:
        # Check if has_interesting_results column exists
        cur.execute("PRAGMA table_info(vision_api_requests)")
        columns = {row[1] for row in cur.fetchall()}
        if 'has_interesting_results' not in columns:
            print("Adding has_interesting_results column...")
            cur.execute("""
                ALTER TABLE vision_api_requests 
                ADD COLUMN has_interesting_results INTEGER NOT NULL DEFAULT 0
            """)
            cur.execute("""
                CREATE INDEX idx_vision_requests_interesting 
                ON vision_api_requests(has_interesting_results)
            """)
            print("✓ Added has_interesting_results column")
        else:
            print("✓ vision_api_requests table already exists")
    
    # vision_api_matches table
    if 'vision_api_matches' not in existing_tables:
        print("Creating vision_api_matches table...")
        cur.execute("""
            CREATE TABLE vision_api_matches (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                match_type TEXT NOT NULL,
                url TEXT,
                page_title TEXT,
                image_url TEXT,
                domain TEXT,
                domain_category TEXT,
                is_suspicious_domain INTEGER DEFAULT 0,
                FOREIGN KEY (request_id) REFERENCES vision_api_requests (id)
            )
        """)
        cur.execute("""
            CREATE INDEX idx_vision_matches_request 
            ON vision_api_matches(request_id)
        """)
        cur.execute("""
            CREATE INDEX idx_vision_matches_domain 
            ON vision_api_matches(domain)
        """)
        print("✓ Created vision_api_matches table")
    else:
        print("✓ vision_api_matches table already exists")
    
    # vision_api_entities table
    if 'vision_api_entities' not in existing_tables:
        print("Creating vision_api_entities table...")
        cur.execute("""
            CREATE TABLE vision_api_entities (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                description TEXT NOT NULL,
                score REAL,
                FOREIGN KEY (request_id) REFERENCES vision_api_requests (id)
            )
        """)
        cur.execute("""
            CREATE INDEX idx_vision_entities_request 
            ON vision_api_entities(request_id)
        """)
        print("✓ Created vision_api_entities table")
    else:
        print("✓ vision_api_entities table already exists")
    
    # vision_api_domain_stats table
    if 'vision_api_domain_stats' not in existing_tables:
        print("Creating vision_api_domain_stats table...")
        cur.execute("""
            CREATE TABLE vision_api_domain_stats (
                id TEXT PRIMARY KEY,
                artwork_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                match_count INTEGER NOT NULL DEFAULT 1,
                first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artwork_id) REFERENCES artworks (id),
                UNIQUE (artwork_id, domain)
            )
        """)
        cur.execute("""
            CREATE INDEX idx_vision_domain_artwork 
            ON vision_api_domain_stats(artwork_id)
        """)
        cur.execute("""
            CREATE INDEX idx_vision_domain_name 
            ON vision_api_domain_stats(domain)
        """)
        print("✓ Created vision_api_domain_stats table")
    else:
        print("✓ vision_api_domain_stats table already exists")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Migration complete! Vision API tables are ready.")


if __name__ == "__main__":
    main()
