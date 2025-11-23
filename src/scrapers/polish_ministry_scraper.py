"""Web scraper for Polish Ministry of Culture looted art database."""
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config.scraper_config import PolishMinistryScraperConfig
from src.infrastructure.errors import ScrapingError


class PolishMinistryWebScraper:
    """Scraper for lootedart.gov.pl database."""
    
    def __init__(self):
        """Initialize scraper with configuration."""
        self._config = PolishMinistryScraperConfig()
        self._session = self._create_session()
        self._last_request_time = 0.0
    
    def _create_session(self) -> requests.Session:
        """Create configured HTTP session."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self._config.USER_AGENT
        })
        return session
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._config.DELAY_BETWEEN_REQUESTS_SECONDS:
            sleep_time = (
                self._config.DELAY_BETWEEN_REQUESTS_SECONDS - 
                time_since_last
            )
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def fetch_category_page(
        self, 
        category_id: int
    ) -> Optional[BeautifulSoup]:
        """Fetch and parse a category page."""
        url = self._config.CATEGORY_URL_TEMPLATE.format(
            category_id=category_id
        )
        
        self._rate_limit()
        
        for attempt in range(self._config.MAX_RETRIES):
            try:
                response = self._session.get(
                    url,
                    timeout=self._config.REQUEST_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                
                return BeautifulSoup(
                    response.content, 
                    "lxml"
                )
                
            except requests.RequestException as e:
                if attempt == self._config.MAX_RETRIES - 1:
                    raise ScrapingError(
                        f"Failed to fetch {url}: {e}"
                    )
                
                time.sleep(
                    self._config.RETRY_BACKOFF_SECONDS * (attempt + 1)
                )
        
        return None
    
    def extract_artworks_from_page(
        self, 
        soup: BeautifulSoup
    ) -> list[dict]:
        """Extract artwork data from parsed HTML."""
        artworks = []
        
        # Look for artwork items in common patterns
        artwork_items = soup.find_all(
            ["div", "article"], 
            class_=lambda x: x and (
                "item" in x.lower() or 
                "product" in x.lower() or
                "artwork" in x.lower()
            )
        )
        
        for item in artwork_items:
            artwork_data = self._parse_artwork_item(item)
            if artwork_data:
                artworks.append(artwork_data)
        
        return artworks
    
    def _parse_artwork_item(
        self, 
        item: BeautifulSoup
    ) -> Optional[dict]:
        """Parse individual artwork item."""
        try:
            title_elem = item.find(
                ["h2", "h3", "h4", "a"], 
                class_=lambda x: x and "title" in x.lower()
            )
            
            if not title_elem:
                title_elem = item.find(["h2", "h3", "h4"])
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            description_elem = item.find(
                ["p", "div"], 
                class_=lambda x: x and (
                    "description" in x.lower() or 
                    "content" in x.lower()
                )
            )
            description = (
                description_elem.get_text(strip=True) 
                if description_elem else ""
            )
            
            img_elem = item.find("img")
            image_url = None
            if img_elem and img_elem.get("src"):
                image_url = urljoin(
                    self._config.BASE_URL, 
                    img_elem["src"]
                )
            
            link_elem = item.find("a", href=True)
            page_url = None
            if link_elem:
                page_url = urljoin(
                    self._config.BASE_URL, 
                    link_elem["href"]
                )
            
            return {
                "title": title,
                "description": description,
                "image_url": image_url,
                "page_url": page_url
            }
            
        except Exception:
            return None
    
    def scrape_category(
        self, 
        category_id: int
    ) -> list[dict]:
        """Scrape all artworks from a category."""
        soup = self.fetch_category_page(category_id)
        
        if not soup:
            return []
        
        return self.extract_artworks_from_page(soup)
    
    def scrape_all_categories(self) -> dict[int, list[dict]]:
        """Scrape all categories and return results."""
        results = {}
        
        for category_id in self._config.ALL_CATEGORIES:
            artworks = self.scrape_category(category_id)
            results[category_id] = artworks
            
            time.sleep(self._config.DELAY_BETWEEN_REQUESTS_SECONDS)
        
        return results
