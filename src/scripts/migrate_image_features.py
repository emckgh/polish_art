"""
Migration script to add CV feature columns to image_features table.
Run this once to update the database schema.
"""
import sqlite3
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Database file path
DATABASE_FILE = "artworks.db"


def migrate():
    """Add new columns to image_features table"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    print("Checking current schema...")
    cursor.execute("PRAGMA table_info(image_features)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"Existing columns: {sorted(existing_columns)}")
    
    # Define new columns to add
    new_columns = {
        'phash': 'TEXT',
        'dhash': 'TEXT',
        'ahash': 'TEXT',
        'clip_embedding': 'TEXT',  # JSON array
        'width_pixels': 'INTEGER',
        'height_pixels': 'INTEGER',
        'aspect_ratio': 'REAL',
        'format': 'TEXT',
        'file_size_bytes': 'INTEGER',
        'color_space': 'TEXT',
        'sharpness_score': 'REAL',
        'contrast_score': 'REAL',
        'brightness_avg': 'REAL',
        'is_grayscale': 'INTEGER',  # SQLite uses 0/1 for boolean
        'dominant_colors': 'TEXT',  # JSON array
        'model_version': 'TEXT'
    }
    
    print("\nApplying migrations...")
    migrations_applied = 0
    
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE image_features ADD COLUMN {column_name} {column_type}"
                print(f"  Adding column: {column_name} ({column_type})")
                cursor.execute(sql)
                migrations_applied += 1
            except sqlite3.OperationalError as e:
                print(f"  ✗ Error adding {column_name}: {e}")
        else:
            print(f"  ✓ Column {column_name} already exists")
    
    conn.commit()
    
    print("\nVerifying schema...")
    cursor.execute("PRAGMA table_info(image_features)")
    final_columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"Final columns: {sorted(final_columns.keys())}")
    
    conn.close()
    
    print(f"\n✓ Migration complete! Applied {migrations_applied} changes.")
    return migrations_applied


if __name__ == "__main__":
    print("=" * 60)
    print("Image Features Schema Migration")
    print("=" * 60)
    print()
    
    try:
        changes = migrate()
        if changes > 0:
            print("\nDatabase schema updated successfully!")
        else:
            print("\nNo changes needed - schema is up to date.")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
