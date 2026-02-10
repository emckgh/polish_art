"""
Recreate image_features table with correct schema.
This removes old columns and sets up the new CV feature columns.
"""
import sqlite3
from pathlib import Path

DATABASE_FILE = "artworks.db"


def recreate_table():
    """Recreate image_features table with new schema"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    print("Backing up existing data...")
    cursor.execute("SELECT artwork_id FROM image_features")
    old_data = cursor.fetchall()
    print(f"Found {len(old_data)} existing records (will be cleared)")
    
    print("\nDropping old table...")
    cursor.execute("DROP TABLE IF EXISTS image_features")
    
    print("Creating new table with correct schema...")
    cursor.execute("""
        CREATE TABLE image_features (
            id TEXT PRIMARY KEY,
            artwork_id TEXT NOT NULL UNIQUE,
            phash TEXT,
            dhash TEXT,
            ahash TEXT,
            clip_embedding TEXT,
            width_pixels INTEGER,
            height_pixels INTEGER,
            aspect_ratio REAL,
            format TEXT,
            file_size_bytes INTEGER,
            color_space TEXT,
            sharpness_score REAL,
            contrast_score REAL,
            brightness_avg REAL,
            is_grayscale INTEGER,
            dominant_colors TEXT,
            extraction_timestamp DATETIME,
            model_version TEXT,
            FOREIGN KEY (artwork_id) REFERENCES artworks (id)
        )
    """)
    
    conn.commit()
    
    print("\nVerifying new schema...")
    cursor.execute("PRAGMA table_info(image_features)")
    columns = cursor.fetchall()
    
    print(f"\n{'Column':<25} {'Type':<15} {'NotNull':<8}")
    print("-" * 50)
    for col in columns:
        col_id, name, col_type, not_null, default_val, pk = col
        print(f"{name:<25} {col_type:<15} {not_null:<8}")
    
    conn.close()
    
    print("\n✓ Table recreated successfully!")
    print(f"\nNote: {len(old_data)} old records were cleared.")
    print("Run extract_features.py to repopulate with new CV features.")


if __name__ == "__main__":
    print("=" * 60)
    print("Image Features Table Recreation")
    print("=" * 60)
    print()
    
    try:
        recreate_table()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
