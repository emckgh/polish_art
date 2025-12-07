"""
Google Custom Search API integration for artwork image discovery.

This module provides functionality to search for artwork images using Google's 
Custom Search JSON API. Results can be used to populate the artwork database.

Setup:
1. Get API Key: https://developers.google.com/custom-search/v1/introduction
2. Create Custom Search Engine: https://programmablesearchengine.google.com/
3. Set environment variables:
   - GOOGLE_API_KEY: Your API key
   - GOOGLE_SEARCH_ENGINE_ID: Your custom search engine ID

Usage:
    from src.utils.google_image_search import GoogleImageSearch
    
    searcher = GoogleImageSearch()
    results = searcher.search_artwork_images(
        query="Polish folk art painting",
        num_results=10
    )
"""

import os
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class ImageSearchResult:
    """Represents a single image search result."""
    title: str
    link: str
    thumbnail_link: str
    context_link: str  # Source page URL
    display_link: str  # Domain name
    snippet: str  # Description
    mime_type: str
    file_format: str
    width: int
    height: int
    byte_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'link': self.link,
            'thumbnail_link': self.thumbnail_link,
            'context_link': self.context_link,
            'display_link': self.display_link,
            'snippet': self.snippet,
            'mime_type': self.mime_type,
            'file_format': self.file_format,
            'width': self.width,
            'height': self.height,
            'byte_size': self.byte_size
        }


class GoogleImageSearch:
    """Client for Google Custom Search API image searches."""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None
    ):
        """
        Initialize Google Image Search client.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            search_engine_id: Custom Search Engine ID (defaults to GOOGLE_SEARCH_ENGINE_ID env var)
        
        Raises:
            ValueError: If credentials are not provided
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not self.api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        if not self.search_engine_id:
            raise ValueError(
                "Search Engine ID not found. Set GOOGLE_SEARCH_ENGINE_ID environment variable "
                "or pass search_engine_id parameter."
            )
        
        self._request_count = 0
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Simple rate limiting to avoid API throttling."""
        # Google allows 100 queries per day on free tier
        # Add 1 second delay between requests to be safe
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_request_time = time.time()
    
    def search_artwork_images(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 1,
        image_size: Optional[str] = None,
        image_type: Optional[str] = None,
        file_type: Optional[str] = None,
        rights: Optional[str] = None,
        safe_search: str = "off",
        country: Optional[str] = None
    ) -> List[ImageSearchResult]:
        """
        Search for artwork images using Google Custom Search API.
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-10 per request)
            start_index: Starting index for pagination (1-based)
            image_size: Filter by size: 'huge', 'icon', 'large', 'medium', 'small', 'xlarge', 'xxlarge'
            image_type: Filter by type: 'clipart', 'face', 'lineart', 'stock', 'photo', 'animated'
            file_type: Filter by format: 'jpg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'
            rights: Filter by usage rights: 'cc_publicdomain', 'cc_attribute', 'cc_sharealike', 
                   'cc_noncommercial', 'cc_nonderived'
            safe_search: Safe search setting: 'off', 'medium', 'high'
            country: Country code for search results (e.g., 'pl' for Poland)
        
        Returns:
            List of ImageSearchResult objects
        
        Raises:
            requests.RequestException: If API request fails
        """
        self._rate_limit()
        
        # Build request parameters
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'searchType': 'image',
            'num': min(num_results, 10),  # Max 10 per request
            'start': start_index,
            'safe': safe_search
        }
        
        # Add optional filters
        if image_size:
            params['imgSize'] = image_size
        if image_type:
            params['imgType'] = image_type
        if file_type:
            params['fileType'] = file_type
        if rights:
            params['rights'] = rights
        if country:
            params['gl'] = country
        
        # Make API request
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        self._request_count += 1
        
        # Parse results
        data = response.json()
        results = []
        
        for item in data.get('items', []):
            result = ImageSearchResult(
                title=item.get('title', ''),
                link=item.get('link', ''),
                thumbnail_link=item.get('image', {}).get('thumbnailLink', ''),
                context_link=item.get('image', {}).get('contextLink', ''),
                display_link=item.get('displayLink', ''),
                snippet=item.get('snippet', ''),
                mime_type=item.get('mime', ''),
                file_format=item.get('fileFormat', ''),
                width=item.get('image', {}).get('width', 0),
                height=item.get('image', {}).get('height', 0),
                byte_size=item.get('image', {}).get('byteSize')
            )
            results.append(result)
        
        return results
    
    def search_paginated(
        self,
        query: str,
        total_results: int = 50,
        **kwargs
    ) -> List[ImageSearchResult]:
        """
        Search with automatic pagination to get more than 10 results.
        
        Args:
            query: Search query
            total_results: Total number of results to fetch (max 100 on free tier)
            **kwargs: Additional arguments passed to search_artwork_images
        
        Returns:
            Combined list of ImageSearchResult objects
        """
        all_results = []
        start_index = 1
        
        while len(all_results) < total_results:
            batch_size = min(10, total_results - len(all_results))
            
            try:
                batch = self.search_artwork_images(
                    query=query,
                    num_results=batch_size,
                    start_index=start_index,
                    **kwargs
                )
                
                if not batch:
                    break
                
                all_results.extend(batch)
                start_index += len(batch)
                
            except requests.RequestException as e:
                print(f"Error fetching batch starting at {start_index}: {e}")
                break
        
        return all_results
    
    def search_polish_art(
        self,
        artist: Optional[str] = None,
        period: Optional[str] = None,
        style: Optional[str] = None,
        num_results: int = 10
    ) -> List[ImageSearchResult]:
        """
        Specialized search for Polish artwork.
        
        Args:
            artist: Artist name to search for
            period: Time period (e.g., "19th century", "medieval")
            style: Art style (e.g., "folk art", "portrait", "landscape")
            num_results: Number of results to return
        
        Returns:
            List of ImageSearchResult objects
        """
        # Build query
        query_parts = []
        
        if artist:
            query_parts.append(artist)
        
        query_parts.append("Polish")
        
        if style:
            query_parts.append(style)
        else:
            query_parts.append("art")
        
        if period:
            query_parts.append(period)
        
        query = " ".join(query_parts)
        
        return self.search_artwork_images(
            query=query,
            num_results=num_results,
            image_size='large',  # Prefer larger images
            file_type='jpg',  # JPEG for photos
            country='pl'  # Focus on Polish results
        )
    
    def get_request_count(self) -> int:
        """Get the number of API requests made in this session."""
        return self._request_count


def download_image(url: str, output_path: str, timeout: int = 30) -> bool:
    """
    Download an image from URL to local file.
    
    Args:
        url: Image URL
        output_path: Local file path to save image
        timeout: Request timeout in seconds
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def format_results_summary(results: List[ImageSearchResult]) -> str:
    """
    Format search results as a readable summary.
    
    Args:
        results: List of search results
    
    Returns:
        Formatted string summary
    """
    summary = []
    summary.append(f"\nFound {len(results)} image(s):\n")
    summary.append("=" * 80)
    
    for i, result in enumerate(results, 1):
        summary.append(f"\n{i}. {result.title}")
        summary.append(f"   URL: {result.link}")
        summary.append(f"   Source: {result.display_link}")
        summary.append(f"   Size: {result.width}x{result.height}")
        summary.append(f"   Format: {result.file_format}")
        if result.snippet:
            summary.append(f"   Description: {result.snippet[:100]}...")
        summary.append("-" * 80)
    
    return "\n".join(summary)
