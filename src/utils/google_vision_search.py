"""
Google Cloud Vision API integration for reverse image search.

This module provides functionality to search for similar images on the web
using Google's Vision API Web Detection feature. Given an artwork image,
it can find:
- Exact matches across the web
- Partial matches (cropped/edited versions)  
- Visually similar images
- Pages containing the image
- Best guess labels and descriptions

Setup:
1. Enable Vision API: https://console.cloud.google.com/apis/library/vision.googleapis.com
2. Set up authentication:
   - Service account: Set GOOGLE_APPLICATION_CREDENTIALS env var
   - Or use: gcloud auth application-default login
3. Install: pip install google-cloud-vision

Usage:
    from src.utils.google_vision_search import VisionSearch
    
    searcher = VisionSearch()
    results = searcher.reverse_image_search(
        image_path="data/artworks/painting.jpg"
    )
    
    for match in results.full_matches:
        print(f"Found at: {match.url}")
"""

import os
import json
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import requests

try:
    from google.cloud import vision
    from google.cloud.vision_v1 import types
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False


@dataclass
class ImageMatch:
    """Represents a web match for an image."""
    url: str
    score: Optional[float] = None  # Confidence score if available
    page_title: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WebPage:
    """Represents a web page containing the image."""
    url: str
    page_title: Optional[str] = None
    full_matching_images: List[str] = None
    partial_matching_images: List[str] = None
    
    def __post_init__(self):
        if self.full_matching_images is None:
            self.full_matching_images = []
        if self.partial_matching_images is None:
            self.partial_matching_images = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReverseImageSearchResult:
    """Complete result from reverse image search."""
    source_image: str
    full_matches: List[ImageMatch]
    partial_matches: List[ImageMatch]
    visually_similar: List[ImageMatch]
    pages_with_image: List[WebPage]
    best_guess_labels: List[str]
    web_entities: List[Dict[str, Any]]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_image': self.source_image,
            'full_matches': [m.to_dict() for m in self.full_matches],
            'partial_matches': [m.to_dict() for m in self.partial_matches],
            'visually_similar': [m.to_dict() for m in self.visually_similar],
            'pages_with_image': [p.to_dict() for p in self.pages_with_image],
            'best_guess_labels': self.best_guess_labels,
            'web_entities': self.web_entities,
            'timestamp': self.timestamp
        }


class VisionSearch:
    """Client for Google Cloud Vision API reverse image search."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Vision Search client.
        
        Args:
            credentials_path: Optional path to service account JSON.
                            If not provided, uses GOOGLE_APPLICATION_CREDENTIALS
                            or gcloud default credentials.
        
        Raises:
            ImportError: If google-cloud-vision is not installed
            Exception: If authentication fails
        """
        if not VISION_AVAILABLE:
            raise ImportError(
                "google-cloud-vision is not installed. "
                "Install it with: pip install google-cloud-vision"
            )
        
        # Set credentials if provided
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            self.client = vision.ImageAnnotatorClient()
            self._request_count = 0
        except Exception as e:
            raise Exception(
                f"Failed to initialize Vision API client: {e}\n"
                "Make sure you've set up authentication:\n"
                "1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable, or\n"
                "2. Run: gcloud auth application-default login"
            )
    
    def reverse_image_search(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        max_results: int = 50
    ) -> ReverseImageSearchResult:
        """
        Perform reverse image search using Vision API.
        
        Args:
            image_path: Path to local image file
            image_url: URL to image
            image_bytes: Raw image bytes
            max_results: Maximum number of results per category
        
        Returns:
            ReverseImageSearchResult with all matches
        
        Raises:
            ValueError: If no image source provided
        """
        # Load image
        if image_path:
            with open(image_path, 'rb') as f:
                content = f.read()
            source = image_path
        elif image_url:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            content = response.content
            source = image_url
        elif image_bytes:
            content = image_bytes
            source = "bytes"
        else:
            raise ValueError("Must provide image_path, image_url, or image_bytes")
        
        # Create Vision API image object
        image = vision.Image(content=content)
        
        # Perform web detection
        response = self.client.web_detection(
            image=image,
            max_results=max_results
        )
        
        self._request_count += 1
        
        # Parse results
        web_detection = response.web_detection
        
        # Full matches (exact images)
        full_matches = []
        for match in web_detection.full_matching_images:
            full_matches.append(ImageMatch(
                url=match.url,
                score=match.score if hasattr(match, 'score') else None
            ))
        
        # Partial matches (cropped/edited versions)
        partial_matches = []
        for match in web_detection.partial_matching_images:
            partial_matches.append(ImageMatch(
                url=match.url,
                score=match.score if hasattr(match, 'score') else None
            ))
        
        # Visually similar images
        visually_similar = []
        for match in web_detection.visually_similar_images:
            visually_similar.append(ImageMatch(
                url=match.url,
                score=match.score if hasattr(match, 'score') else None
            ))
        
        # Pages containing the image
        pages_with_image = []
        for page in web_detection.pages_with_matching_images:
            web_page = WebPage(
                url=page.url,
                page_title=page.page_title if hasattr(page, 'page_title') else None,
                full_matching_images=[img.url for img in page.full_matching_images],
                partial_matching_images=[img.url for img in page.partial_matching_images]
            )
            pages_with_image.append(web_page)
        
        # Best guess labels
        best_guess_labels = []
        if web_detection.best_guess_labels:
            best_guess_labels = [label.label for label in web_detection.best_guess_labels]
        
        # Web entities (related concepts)
        web_entities = []
        for entity in web_detection.web_entities:
            web_entities.append({
                'entity_id': entity.entity_id,
                'description': entity.description,
                'score': entity.score
            })
        
        return ReverseImageSearchResult(
            source_image=source,
            full_matches=full_matches,
            partial_matches=partial_matches,
            visually_similar=visually_similar,
            pages_with_image=pages_with_image,
            best_guess_labels=best_guess_labels,
            web_entities=web_entities,
            timestamp=datetime.now().isoformat()
        )
    
    def batch_search(
        self,
        image_paths: List[str],
        output_dir: Optional[str] = None
    ) -> List[ReverseImageSearchResult]:
        """
        Perform reverse image search on multiple images.
        
        Args:
            image_paths: List of image file paths
            output_dir: Optional directory to save results JSON
        
        Returns:
            List of ReverseImageSearchResult objects
        """
        results = []
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"Processing {i}/{len(image_paths)}: {image_path}")
            
            try:
                result = self.reverse_image_search(image_path=image_path)
                results.append(result)
                
                # Save individual result if output_dir specified
                if output_dir:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    
                    filename = Path(image_path).stem + '_results.json'
                    filepath = output_path / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
                    
                    print(f"  ✓ Saved results to {filepath}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        return results
    
    def find_higher_resolution(
        self,
        image_path: str,
        min_width: int = 1000
    ) -> List[ImageMatch]:
        """
        Find higher resolution versions of an image.
        
        Args:
            image_path: Path to image
            min_width: Minimum width in pixels
        
        Returns:
            List of higher-res image matches
        """
        result = self.reverse_image_search(image_path=image_path)
        
        # Get image dimensions from URLs where possible
        higher_res = []
        
        for match in result.full_matches + result.visually_similar:
            # Try to fetch image headers to check size
            try:
                response = requests.head(match.url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    # Check if it's an image
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type:
                        higher_res.append(match)
            except:
                # Add anyway if we can't check
                higher_res.append(match)
        
        return higher_res
    
    def identify_source(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Identify the source/provenance of an artwork image.
        
        Args:
            image_path: Path to artwork image
        
        Returns:
            Dictionary with source information
        """
        result = self.reverse_image_search(image_path=image_path)
        
        # Analyze domains
        domains = {}
        for page in result.pages_with_image:
            from urllib.parse import urlparse
            domain = urlparse(page.url).netloc
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(page.url)
        
        # Categorize domains
        museum_domains = [d for d in domains if any(
            term in d for term in ['museum', 'gallery', 'mnw', 'mnk', 'polona']
        )]
        
        auction_domains = [d for d in domains if any(
            term in d for term in ['christie', 'sotheby', 'auction', 'artnet']
        )]
        
        academic_domains = [d for d in domains if any(
            term in d for term in ['edu', 'jstor', 'academia', 'archive.org']
        )]
        
        return {
            'best_guess': result.best_guess_labels[0] if result.best_guess_labels else None,
            'total_matches': len(result.full_matches) + len(result.partial_matches),
            'total_pages': len(result.pages_with_image),
            'domains': domains,
            'museum_sources': museum_domains,
            'auction_sources': auction_domains,
            'academic_sources': academic_domains,
            'web_entities': result.web_entities[:5]  # Top 5 entities
        }
    
    def get_request_count(self) -> int:
        """Get number of API requests made in this session."""
        return self._request_count


def format_search_results(result: ReverseImageSearchResult) -> str:
    """
    Format search results as readable text.
    
    Args:
        result: ReverseImageSearchResult object
    
    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("REVERSE IMAGE SEARCH RESULTS")
    lines.append("=" * 80)
    lines.append(f"\nSource: {result.source_image}")
    lines.append(f"Timestamp: {result.timestamp}")
    
    if result.best_guess_labels:
        lines.append(f"\nBest Guess: {', '.join(result.best_guess_labels)}")
    
    lines.append(f"\n--- Full Matches ({len(result.full_matches)}) ---")
    for match in result.full_matches[:10]:
        lines.append(f"  {match.url}")
    
    lines.append(f"\n--- Partial Matches ({len(result.partial_matches)}) ---")
    for match in result.partial_matches[:10]:
        lines.append(f"  {match.url}")
    
    lines.append(f"\n--- Visually Similar ({len(result.visually_similar)}) ---")
    for match in result.visually_similar[:10]:
        lines.append(f"  {match.url}")
    
    lines.append(f"\n--- Pages with Image ({len(result.pages_with_image)}) ---")
    for page in result.pages_with_image[:10]:
        title = f" - {page.page_title}" if page.page_title else ""
        lines.append(f"  {page.url}{title}")
    
    if result.web_entities:
        lines.append(f"\n--- Related Concepts ---")
        for entity in result.web_entities[:10]:
            score = f" ({entity['score']:.2f})" if entity.get('score') else ""
            lines.append(f"  {entity.get('description', 'N/A')}{score}")
    
    lines.append("\n" + "=" * 80)
    
    return "\n".join(lines)
