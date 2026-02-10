"""
Recompute perceptual hashes for all artworks that have image data.

This script fixes the image_hash field which was incorrectly populated with URLs
instead of actual perceptual hashes during import.
"""

import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cv_pipeline.perceptual_hasher import PerceptualHasher
from src.utils.uuid_utils import format_uuid_with_hyphens


def recompute_hashes(db_path: str, image_dir: Path):
    """Recompute perceptual hashes for all artworks with images."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all artworks that have image_url (meaning they should have image files)
    cursor.execute("""
        SELECT id, image_url, image_hash 
        FROM artworks 
        WHERE image_url IS NOT NULL AND image_url != ''
    """)
    
    artworks = cursor.fetchall()
    total = len(artworks)
    
    print(f"Found {total} artworks with images")
    print(f"Initializing perceptual hasher...\n")
    
    hasher = PerceptualHasher()
    
    updated = 0
    failed = 0
    skipped = 0
    
    for i, (artwork_id, image_url, current_hash) in enumerate(artworks, 1):
        # Check if hash looks like it's already computed (not a URL)
        if current_hash and not current_hash.startswith('http'):
            skipped += 1
            continue
            
        # Find the image file (need to add hyphens to UUID)
        uuid_with_hyphens = format_uuid_with_hyphens(artwork_id)
        image_filename = f"{uuid_with_hyphens}.jpg"
        image_path = image_dir / image_filename
        
        if not image_path.exists():
            print(f"[{i}/{total}] ✗ Image not found: {image_filename}")
            failed += 1
            continue
        
        try:
            # Read image data
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Compute perceptual hash
            phash = hasher.compute_phash(image_data)
            
            # Update database
            cursor.execute("""
                UPDATE artworks 
                SET image_hash = ? 
                WHERE id = ?
            """, (phash, artwork_id))
            
            updated += 1
            
            if i % 100 == 0:
                print(f"[{i}/{total}] Progress: {updated} updated, {failed} failed, {skipped} skipped")
                conn.commit()  # Commit periodically
                
        except Exception as e:
            print(f"[{i}/{total}] ✗ Failed to process {artwork_id[:8]}...: {e}")
            failed += 1
    
    # Final commit
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("HASH RECOMPUTATION COMPLETE")
    print("="*60)
    print(f"Total artworks: {total}")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
    print(f"Skipped (already computed): {skipped}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Recompute perceptual hashes for artworks'
    )
    parser.add_argument(
        '--db',
        default='data/artworks.db',
        help='Database file path'
    )
    parser.add_argument(
        '--image-dir',
        default='data/images',
        help='Directory containing image files'
    )
    
    args = parser.parse_args()
    
    db_path = args.db
    image_dir = Path(args.image_dir)
    
    if not image_dir.exists():
        print(f"Error: Image directory not found: {image_dir}")
        sys.exit(1)
    
    recompute_hashes(db_path, image_dir)
