"""
Custom scraper for lootedart.gov.pl database.
"""

import requests
import urllib3
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from datetime import datetime
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_artwork(session, obid):
    """Scrape a single artwork by object ID (obid)."""
    url = f'http://lootedart.gov.pl/en/product-war-losses/object?obid={obid}'
    
    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        artwork = {
            'obid': obid,
            'source_url': url
        }
        
        # Extract title from h1 or h2 (may be empty)
        title = soup.find('h1') or soup.find('h2', class_=lambda x: x and 'title' in str(x).lower())
        if title:
            title_text = title.get_text(strip=True)
            if title_text:
                artwork['title'] = title_text
        
        # Parse structured fields from form-group divs
        field_mapping = {
            'Title of object': 'title',
            'Author / School / Workshop': 'artist',
            'Card number': 'card_number',
            'Division': 'division',
            'Object type': 'object_type',
            'Date of creation': 'date_of_creation',
            'Material': 'material',
            'Technique': 'technique',
            'Owner': 'owner',
            'Inventory number': 'inventory_number',
            'Recovered': 'recovered',
            'Diameter': 'diameter',
            'Weight': 'weight'
        }
        
        # Track unknown fields
        unknown_fields = []
        
        # Find all form-group divs
        for form_group in soup.find_all('div', class_='form-group'):
            label_div = form_group.find('div', class_='control-label')
            if label_div:
                label_text = label_div.get_text(strip=True).rstrip(':')
                
                if label_text in field_mapping:
                    value_div = form_group.find('div', class_='col-sm-7')
                    if value_div:
                        value = value_div.get_text(strip=True).replace('&nbsp;', '').strip()
                        if value:  # Only add non-empty values
                            artwork[field_mapping[label_text]] = value
                elif label_text:  # Non-empty label not in mapping
                    value_div = form_group.find('div', class_='col-sm-7')
                    if value_div:
                        value = value_div.get_text(strip=True).replace('&nbsp;', '').strip()
                        if value:  # Only log if there's a value
                            unknown_fields.append({
                                'label': label_text,
                                'value': value[:100]  # Truncate long values
                            })
        
        # Store unknown fields for later review
        if unknown_fields:
            artwork['_unknown_fields'] = unknown_fields
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'banner', 'flag']):
                if src.startswith('/'):
                    src = f'http://lootedart.gov.pl{src}'
                images.append({
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        
        if images:
            artwork['images'] = images
        
        return artwork
        
    except Exception as e:
        print(f"Error scraping obid {obid}: {e}")
        return None

def get_artwork_obids_from_listing(session, max_artworks=10):
    """Get artwork object IDs from the listing pages with pagination."""
    obids = []
    limitstart = 0
    limit = 10  # Results per page
    
    # Submit search form once to get all results
    search_url = 'http://lootedart.gov.pl/en/product-war-losses/advanced-search'
    form_data = {
        'tytul': '',
        'autor': '',
        'nr_karty': '',
        'sygnatura': '',
        'wysokosc': '',
        'szerokosc': '',
        'glebokosc': '',
        'dlugosc': '',
        'srednica': '',
        'waga': ''
    }
    
    while len(obids) < max_artworks:
        try:
            # Add pagination parameter to URL
            paginated_url = f'{search_url}?limitstart={limitstart}'
            
            # POST search form data
            r = session.post(paginated_url, data=form_data, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            found_on_page = 0
            # Find all links to object pages
            for link in soup.find_all('a', href=True):
                href = str(link.get('href', ''))
                if '/object?obid=' in href:
                    # Extract obid
                    match = re.search(r'obid=(\d+)', href)
                    if match:
                        obid = match.group(1)
                        if obid not in obids:
                            obids.append(obid)
                            found_on_page += 1
                            if len(obids) >= max_artworks:
                                return obids
            
            # If no new artworks found on this page, we've reached the end
            if found_on_page == 0:
                print(f"  No more artworks found at limitstart={limitstart}")
                break
            
            print(f"  Page (limitstart={limitstart}): found {found_on_page} artworks (total: {len(obids)})")
            limitstart += limit
            time.sleep(0.5)  # Rate limiting between pages
            
        except Exception as e:
            print(f"  Error at limitstart={limitstart}: {e}")
            break
    
    return obids

def scrape_first_n(n=10, output_file='data/looted_art_import.json'):
    """Scrape first N artworks from the database."""
    print(f"Scraping first {n} artworks from lootedart.gov.pl\n")
    
    # Create session with proper headers
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'http://lootedart.gov.pl/en/product-war-losses/advanced-search'
    })
    
    # Visit search page first to get cookies
    print("Initializing session...")
    session.get('http://lootedart.gov.pl/en/product-war-losses/advanced-search')
    print(f"Session ready with {len(session.cookies)} cookies\n")
    
    # Get artwork object IDs from listing page
    print("Extracting artwork IDs from listing...")
    obids = get_artwork_obids_from_listing(session, max_artworks=n)
    print(f"Found {len(obids)} artwork IDs\n")
    
    artworks = []
    
    for i, obid in enumerate(obids, 1):
        print(f"[{i}/{len(obids)}] Scraping obid {obid}...", end=' ')
        
        artwork = scrape_artwork(session, obid)
        
        # Accept artwork if it has a title OR card number (some objects have no title)
        if artwork and (artwork.get('title') or artwork.get('card_number')):
            artworks.append(artwork)
            title = artwork.get('title') or f"[Untitled - Card {artwork.get('card_number', 'unknown')}]"
            print(f"✓ {title[:60]}")
        else:
            print("✗ Not found or empty")
        
        time.sleep(1)  # Rate limiting
    
    # Save to JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'http://lootedart.gov.pl',
            'scraped_at': datetime.now().isoformat(),
            'artworks': artworks
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(artworks)} artworks to {output_path}")
    
    # Report unknown fields found
    all_unknown_fields = {}
    for artwork in artworks:
        if '_unknown_fields' in artwork:
            for field in artwork['_unknown_fields']:
                label = field['label']
                if label not in all_unknown_fields:
                    all_unknown_fields[label] = {
                        'count': 0,
                        'example_value': field['value']
                    }
                all_unknown_fields[label]['count'] += 1
    
    if all_unknown_fields:
        print("\n" + "="*60)
        print("⚠️  UNKNOWN FIELDS DETECTED")
        print("="*60)
        print("The following fields were found but not in the field mapping:")
        print()
        for label, info in sorted(all_unknown_fields.items()):
            print(f"  • {label}")
            print(f"    Count: {info['count']} artwork(s)")
            print(f"    Example: {info['example_value']}")
            print()
        print("Consider adding these to field_mapping in scrape_lootedart_gov_pl.py")
        print("="*60)
    
    return artworks

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=10, help='Number of artworks to scrape')
    parser.add_argument('--output', default='data/looted_art_import.json', help='Output file')
    args = parser.parse_args()
    
    scrape_first_n(args.count, args.output)
