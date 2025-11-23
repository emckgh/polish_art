"""Service for downloading and storing artwork images."""
import hashlib
import time
from typing import Optional

import requests

from src.domain.entities import Artwork
from src.infrastructure.errors import ScrapingError


class ImageDownloadService:
    """Service to download images from URLs and store them."""
    
    def __init__(self, delay_seconds: float = 2.0):
        """Initialize with rate limiting."""
        self._delay_seconds = delay_seconds
        self._last_request_time = 0.0
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with headers."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        return session
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._delay_seconds:
            time.sleep(self._delay_seconds - elapsed)
        
        self._last_request_time = time.time()
    
    def download_image(
        self, 
        url: str, 
        max_size_mb: int = 10
    ) -> Optional[tuple[bytes, str]]:
        """Download image from URL.
        
        Returns:
            Tuple of (image_data, mime_type) or None if failed
        """
        if not url:
            return None
        
        try:
            self._rate_limit()
            
            response = self._session.get(
                url, 
                timeout=30,
                stream=True
            )
            
            if response.status_code != 200:
                return None
            
            content_type = response.headers.get(
                'content-type', 
                'image/jpeg'
            )
            
            # Validate content type is actually an image
            if not content_type.startswith('image/'):
                print(f"Invalid content type {content_type} for {url}")
                return None
            
            # Download with size limit
            max_bytes = max_size_mb * 1024 * 1024
            image_data = b''
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    image_data += chunk
                    if len(image_data) > max_bytes:
                        raise ScrapingError(
                            f"Image too large: {url}"
                        )
            
            return (image_data, content_type)
            
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None
    
    def download_and_attach_image(
        self, 
        artwork: Artwork
    ) -> Artwork:
        """Download image and attach to artwork entity.
        
        Returns:
            Updated artwork with image_data populated
        """
        if not artwork.image_url:
            return artwork
        
        result = self.download_image(artwork.image_url)
        
        if result:
            image_data, mime_type = result
            
            # Calculate hash for deduplication
            image_hash = hashlib.sha256(image_data).hexdigest()
            
            # Create new artwork with image data
            # (Artwork is a dataclass, so we need to replace)
            from dataclasses import replace
            return replace(
                artwork,
                image_data=image_data,
                image_mime_type=mime_type,
                image_hash=image_hash
            )
        
        return artwork
