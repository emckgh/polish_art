"""
Clear all data from the database and import fresh data from looted art.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.sqlite_repository import SQLiteArtworkRepository
from sqlalchemy import create_engine, text

def clear_database(db_path='artworks.db'):
    """Delete all records from all tables."""
    print(f"Clearing database: {db_path}")
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    with engine.connect() as conn:
        # Delete in order (respecting foreign keys)
        # Check which tables exist first
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        existing_tables = [row[0] for row in result]
        
        tables_to_clear = ['features', 'clip_embeddings', 'artworks', 'artists']
        
        for table in tables_to_clear:
            if table in existing_tables:
                result = conn.execute(text(f'DELETE FROM {table}'))
                conn.commit()
                print(f"  Cleared {table}: {result.rowcount} rows deleted")
            else:
                print(f"  Skipped {table}: table does not exist")
    
    print("✓ Database cleared\n")

def count_artworks(db_path='artworks.db'):
    """Count artworks in database."""
    repo = SQLiteArtworkRepository(f'sqlite:///{db_path}')
    artworks = repo.find_all(limit=1000, offset=0)
    return len(artworks)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear database')
    parser.add_argument('--db', default='artworks.db', help='Database file')
    args = parser.parse_args()
    
    before = count_artworks(args.db)
    print(f"Artworks before: {before}\n")
    
    clear_database(args.db)
    
    after = count_artworks(args.db)
    print(f"Artworks after: {after}")
