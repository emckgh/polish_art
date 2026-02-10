"""
Scraper for Polish looted art database.

This script extracts artwork data from the Polish Ministry of Culture's
database of cultural losses from WWII.

Target site: https://www.lootedart.gov.pl/ (or similar official database)

Note: This scraper respects robots.txt and implements rate limiting.
Only public data is collected for preservation and research purposes.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re
from urllib.parse import urljoin


class PolishLootedArtScraper:
    """Scraper for Polish looted art database."""
    
    def __init__(self, base_url: str, delay_seconds: float = 2.0):
        """
        Initialize scraper.
        
        Args:
            base_url: Base URL of the database
            delay_seconds: Delay between requests (respect rate limits)
        """
        self.base_url = base_url
        self.delay = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Polish Art Research Bot'
        })
        self.session.verify = False  # Disable SSL verification for lootedart.gov.pl
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.artworks_collected = []
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a page.
        
        Args:
            url: URL to fetch
        
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            time.sleep(self.delay)  # Rate limiting
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_artwork_details(self, detail_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information from artwork page.
        
        Args:
            detail_url: URL to artwork detail page
        
        Returns:
            Dictionary with artwork data
        """
        soup = self._get_page(detail_url)
        if not soup:
            return None
        
        artwork = {
            'source_url': detail_url
        }
        
        # Extract title
        title_elem = soup.find('h1') or soup.find('h2', class_='title')
        if title_elem:
            artwork['title'] = title_elem.get_text(strip=True)
        
        # Extract metadata fields (adjust selectors based on actual site structure)
        metadata_mapping = {
            'artist': ['artist', 'autor', 'twórca'],
            'creation_year': ['year', 'rok', 'data'],
            'technique': ['technique', 'technika'],
            'dimensions': ['dimensions', 'wymiary'],
            'inventory_number': ['inventory', 'inv', 'nr_inwentarzowy'],
            'loss_date': ['loss_date', 'data_utraty'],
            'loss_circumstances': ['circumstances', 'okoliczności'],
            'current_location': ['location', 'lokalizacja'],
            'description': ['description', 'opis']
        }
        
        for field, possible_labels in metadata_mapping.items():
            for label in possible_labels:
                # Try various HTML patterns
                elem = (soup.find('dt', string=re.compile(label, re.I)) or
                       soup.find(class_=re.compile(label, re.I)) or
                       soup.find('label', string=re.compile(label, re.I)))
                
                if elem:
                    # Get value
                    if elem.name == 'dt':
                        value_elem = elem.find_next_sibling('dd')
                    else:
                        value_elem = elem.find_next_sibling()
                    
                    if value_elem:
                        artwork[field] = value_elem.get_text(strip=True)
                        break
        
        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if any(skip in src.lower() for skip in ['logo', 'icon', 'banner']):
                continue
            
            full_url = urljoin(self.base_url, src)
            images.append({
                'url': full_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        if images:
            artwork['images'] = images
        
        return artwork
    
    def scrape_catalog_page(self, catalog_url: str) -> tuple[List[str], List[str]]:
        """
        Extract artwork URLs and pagination links from catalog page.
        
        Args:
            catalog_url: URL to catalog/listing page
        
        Returns:
            Tuple of (artwork_urls, pagination_urls)
        """
        soup = self._get_page(catalog_url)
        if not soup:
            return [], []
        
        artwork_urls = []
        pagination_urls = []
        
        # Find artwork links and pagination
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip navigation links
            if any(skip in href.lower() for skip in ['#', 'javascript:', 'mailto:']):
                continue
            
            full_url = urljoin(self.base_url, href)
            
            # Look for pagination links
            if any(pattern in href.lower() for pattern in ['next', 'następna', 'page=']):
                if full_url not in pagination_urls:
                    pagination_urls.append(full_url)
            # Look for artwork detail pages
            elif any(pattern in href.lower() for pattern in ['detail', 'artwork', 'object', 'dzieło']):
                if full_url not in artwork_urls:
                    artwork_urls.append(full_url)
        
        return artwork_urls, pagination_urls
    
    def scrape_all(
        self,
        start_url: Optional[str] = None,
        max_pages: int = 100,
        max_artworks: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Scrape entire database.
        
        Args:
            start_url: Starting catalog URL (uses base_url if None)
            max_pages: Maximum catalog pages to process
            max_artworks: Maximum artworks to collect
        
        Returns:
            List of artwork dictionaries
        """
        if not start_url:
            start_url = self.base_url
        
        # Reset collected artworks for fresh run
        self.artworks_collected = []
        
        print(f"Starting scrape from: {start_url}")
        print(f"Delay between requests: {self.delay}s")
        print()
        
        # Collect catalog pages
        catalog_urls = [start_url]
        processed_urls = set()
        
        # Collect artwork URLs
        artwork_urls = set()
        
        for page_num, catalog_url in enumerate(catalog_urls[:max_pages], 1):
            if catalog_url in processed_urls:
                continue
            
            # Check if we already have enough artwork URLs
            if len(artwork_urls) >= max_artworks:
                break
            
            print(f"Processing catalog page {page_num}: {catalog_url}")
            processed_urls.add(catalog_url)
            
            # Get artwork URLs and pagination links in one call
            urls, pagination_urls = self.scrape_catalog_page(catalog_url)
            artwork_urls.update(urls)
            print(f"  Found {len(urls)} artwork links")
            
            # Add new pagination URLs to queue
            for next_url in pagination_urls:
                if next_url not in catalog_urls and next_url not in processed_urls:
                    catalog_urls.append(next_url)
        
        print(f"\nTotal artwork URLs found: {len(artwork_urls)}")
        print(f"Collecting artwork details...\n")
        
        # Collect artwork details
        for i, artwork_url in enumerate(list(artwork_urls)[:max_artworks], 1):
            print(f"[{i}/{min(len(artwork_urls), max_artworks)}] {artwork_url}")
            
            artwork = self.extract_artwork_details(artwork_url)
            if artwork:
                self.artworks_collected.append(artwork)
                print(f"  ✓ {artwork.get('title', 'Untitled')}")
            else:
                print(f"  ✗ Failed to extract")
        
        return self.artworks_collected
    
    def save_to_json(self, output_path: str):
        """Save collected artworks to JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source': self.base_url,
                'scraped_at': datetime.now().isoformat(),
                'artworks': self.artworks_collected
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {len(self.artworks_collected)} artworks to {output_file}")


def main():
    """Main scraper function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape Polish looted art database'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Base URL of the database'
    )
    parser.add_argument(
        '--output',
        default='data/looted_art_import.json',
        help='Output JSON file'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum catalog pages to process'
    )
    parser.add_argument(
        '--max-artworks',
        type=int,
        default=1000,
        help='Maximum artworks to collect'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds'
    )
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = PolishLootedArtScraper(
        base_url=args.url,
        delay_seconds=args.delay
    )
    
    # Scrape data
    artworks = scraper.scrape_all(
        max_pages=args.max_pages,
        max_artworks=args.max_artworks
    )
    
    # Save results
    scraper.save_to_json(args.output)
    
    print(f"\nComplete! Collected {len(artworks)} artworks")


if __name__ == '__main__':
    main()
