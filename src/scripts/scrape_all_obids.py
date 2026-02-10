"""
Comprehensive scraper that iterates through all possible obid values.
Since we can't rely on pagination, we'll brute-force check obids from 1 to 70000.
"""
import requests
import urllib3
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from datetime import datetime
import re
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import the existing scrape_artwork function
from scripts.scrape_lootedart_gov_pl import scrape_artwork

def scrape_all_by_obid_range(start_obid=1, end_obid=70000, output_file='data/looted_art_all.json', checkpoint_interval=100):
    """Scrape artworks by iterating through all possible obids."""
    print(f"Scraping artworks by checking obids from {start_obid} to {end_obid}")
    print(f"Estimated {end_obid - start_obid + 1} obids to check\n")
    
    # Create session
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'http://lootedart.gov.pl/en/product-war-losses/advanced-search'
    })
    
    # Get cookies
    print("Initializing session...")
    session.get('http://lootedart.gov.pl/en/product-war-losses/advanced-search')
    print(f"Session ready\n")
    
    artworks = []
    checked = 0
    found = 0
    empty = 0
    errors = 0
    
    start_time = time.time()
    
    for obid in range(start_obid, end_obid + 1):
        checked += 1
        
        try:
            artwork = scrape_artwork(session, obid)
            
            if artwork and (artwork.get('title') or artwork.get('card_number')):
                artworks.append(artwork)
                found += 1
                title = artwork.get('title') or f"[Card {artwork.get('card_number')}]"
                print(f"[{checked}/{end_obid-start_obid+1}] obid {obid}: ✓ {title[:60]}")
            else:
                empty += 1
                if empty % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = checked / elapsed
                    remaining = (end_obid - obid) / rate / 60
                    print(f"[{checked}/{end_obid-start_obid+1}] Progress: {found} found, {empty} empty, ~{remaining:.0f}min remaining", end='\r')
        
        except Exception as e:
            errors += 1
            if errors % 10 == 0:
                print(f"[{checked}] Error at obid {obid}: {str(e)[:50]}")
        
        # Checkpoint save
        if found > 0 and found % checkpoint_interval == 0:
            save_checkpoint(artworks, output_file, found)
        
        time.sleep(0.2)  # Rate limiting
    
    # Final save
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'http://lootedart.gov.pl',
            'scraped_at': datetime.now().isoformat(),
            'obid_range': f'{start_obid}-{end_obid}',
            'artworks': artworks
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'='*80}")
    print(f"✓ Scraping complete!")
    print(f"  Checked: {checked} obids")
    print(f"  Found: {found} artworks")
    print(f"  Empty: {empty}")
    print(f"  Errors: {errors}")
    print(f"  Saved to: {output_path}")
    print(f"{'='*80}")
    
    return artworks

def save_checkpoint(artworks, output_file, count):
    """Save checkpoint file."""
    checkpoint_file = output_file.replace('.json', f'_checkpoint_{count}.json')
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'http://lootedart.gov.pl',
            'scraped_at': datetime.now().isoformat(),
            'checkpoint': True,
            'artworks': artworks
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[CHECKPOINT] Saved {count} artworks to {checkpoint_file}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=1, help='Start obid')
    parser.add_argument('--end', type=int, default=70000, help='End obid')
    parser.add_argument('--output', default='data/looted_art_all.json', help='Output file')
    parser.add_argument('--checkpoint', type=int, default=100, help='Checkpoint interval')
    args = parser.parse_args()
    
    scrape_all_by_obid_range(args.start, args.end, args.output, args.checkpoint)
