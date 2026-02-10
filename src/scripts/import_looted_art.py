"""
Import scraped looted art data into the Polish Art Database.

This script takes JSON data from the scraper and imports it into
the database, creating artwork entries with proper metadata.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import requests
from typing import Dict, Any, Optional
import urllib3

# Disable SSL warnings for lootedart.gov.pl
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.sqlite_repository import SQLiteArtworkRepository
from src.domain.entities import Artwork, Artist, ArtworkStatus
from uuid import UUID


def download_image(url: str, output_path: Path, session: Optional[requests.Session] = None, max_retries: int = 3) -> bool:
    """Download image from URL using session to maintain cookies with retry logic."""
    import time
    
    for attempt in range(max_retries):
        try:
            # Use session if provided, otherwise create new request
            if session:
                response = session.get(url, timeout=30, stream=True, verify=False)
            else:
                response = requests.get(url, timeout=30, stream=True, verify=False)
            response.raise_for_status()
            
            # Check if we actually got an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type.lower():
                print(f"  ✗ Not an image: got {content_type}")
                return False
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except (requests.exceptions.RequestException, IOError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  ⚠ Retry {attempt + 1}/{max_retries} after {wait_time}s: {str(e)[:50]}")
                time.sleep(wait_time)
            else:
                print(f"  ✗ Failed after {max_retries} attempts: {str(e)[:50]}")
                return False
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return False
    
    return False


def import_artwork(data: Dict[str, Any], repo: SQLiteArtworkRepository, image_dir: Path, session: Optional[requests.Session] = None):
    """
    Import single artwork into database.
    
    Returns:
        True if imported successfully
        None if skipped (already exists)
        False if failed
    """
    
    try:
        # Check if already imported by obid
        obid = data.get('obid')
        if obid:
            # Check if card_number already exists (using title as proxy since we don't store obid)
            title = data.get('title', 'Untitled')
            existing = repo.find_all(limit=10000, offset=0)
            for artwork in existing:
                if artwork.title == title:
                    return None  # Skip duplicate
        
        artwork_id = uuid4()  # Keep as UUID, not string
        
        # Parse artist if available
        artist = None
        if data.get('artist'):
            artist_name = data['artist']
            # Try to parse "Name (dates)" format
            match = re.match(r'(.+?)\s*\((\d{4})-(\d{4})\)', artist_name)
            if match:
                artist = Artist(
                    name=match.group(1).strip(),
                    nationality="Polish",
                    birth_year=int(match.group(2)),
                    death_year=int(match.group(3))
                )
            else:
                artist = Artist(name=artist_name, nationality="Polish")
        
        # Parse year if available (try date_of_creation from scraper, fallback to creation_year)
        creation_year = None
        year_str = data.get('date_of_creation') or data.get('creation_year', '')
        if year_str:
            # Extract first 4-digit year
            match = re.search(r'\d{4}', year_str)
            if match:
                creation_year = int(match.group())
        
        # Get owner/location
        last_known_location = data.get('owner') or data.get('last_known_location')
        
        # Download image if available
        image_hash = None
        image_url = None
        image_data = None
        
        if data.get('images') and len(data['images']) > 0:
            # Find first real image (skip UI icons)
            for img in data['images']:
                img_url = img.get('url', '')
                if img_url and 'dzielo_id' in img_url and 'zdjecie_id' in img_url:
                    image_url = img_url
                    break
            
            if image_url:
                image_filename = f"{artwork_id}.jpg"
                image_path = image_dir / image_filename
                
                print(f"  Downloading image from: {image_url[:80]}...")
                if download_image(image_url, image_path, session):
                    # Store image data
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    # Frontend expects image_hash to contain the image URL
                    image_hash = image_url
                    print(f"  ✓ Image saved ({len(image_data)} bytes)")
                else:
                    image_url = None  # Failed to download
        
        # Build description from available fields
        desc_parts = []
        if data.get('description'):
            desc_parts.append(data['description'])
        if data.get('technique'):
            desc_parts.append(f"Technique: {data['technique']}")
        if data.get('dimensions'):
            desc_parts.append(f"Dimensions: {data['dimensions']}")
        if data.get('loss_circumstances'):
            desc_parts.append(f"Loss circumstances: {data['loss_circumstances']}")
        
        description = '\n'.join(desc_parts) if desc_parts else ''
        
        # Create artwork entity
        artwork = Artwork(
            id=artwork_id,
            title=data.get('title', 'Untitled'),
            artist=artist,
            creation_year=creation_year,
            description=description,
            image_url=image_url,
            image_data=image_data,
            image_hash=image_hash,
            last_known_location=last_known_location,
            status=ArtworkStatus.SUSPECTED
        )
        
        # Save to database
        repo.save(artwork)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def main():
    """Main import function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Import looted art data into database'
    )
    parser.add_argument(
        'json_file',
        help='Path to JSON file from scraper'
    )
    parser.add_argument(
        '--db',
        default='data/artworks.db',
        help='Database file path'
    )
    parser.add_argument(
        '--image-dir',
        default='data/images',
        help='Directory to save images'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip artworks that already exist'
    )
    
    args = parser.parse_args()
    
    # Load JSON data
    print(f"Loading data from {args.json_file}...")
    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    artworks = data.get('artworks', [])
    print(f"Found {len(artworks)} artworks to import\n")
    
    # Initialize repository
    repo = SQLiteArtworkRepository(f"sqlite:///{args.db}")
    
    # Check how many are already imported
    existing_count = len(repo.find_all(limit=10000, offset=0))
    print(f"Database currently has {existing_count} artworks\n")
    
    # Create image directory
    image_dir = Path(args.image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)
    
    # Create session and get cookies from lootedart.gov.pl
    print("Establishing session with lootedart.gov.pl...")
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Visit search page to get cookies
    try:
        response = session.get('http://lootedart.gov.pl/en/product-war-losses/advanced-search', timeout=10)
        print(f"  Session established (cookies: {len(session.cookies)})\n")
    except Exception as e:
        print(f"  ⚠ Warning: Could not establish session: {e}\n")
    
    # Import artworks
    successful = 0
    failed = 0
    skipped = 0
    
    for i, artwork_data in enumerate(artworks, 1):
        title = artwork_data.get('title', 'Untitled')
        print(f"[{i}/{len(artworks)}] {title}")
        
        result = import_artwork(artwork_data, repo, image_dir, session)
        if result is True:
            successful += 1
            print(f"  ✓ Imported")
        elif result is None:
            skipped += 1
            print(f"  ⊘ Skipped (already exists)")
        else:
            failed += 1
        
        print()
    
    print("=" * 60)
    print(f"Import complete!")
    print(f"  Successful: {successful}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total processed: {successful + skipped + failed}/{len(artworks)}")
    print("=" * 60)


if __name__ == '__main__':
    import re  # Add missing import
    main()
