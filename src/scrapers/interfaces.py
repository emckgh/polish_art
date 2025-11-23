"""Interface for image search providers."""
from abc import ABC, abstractmethod
from pathlib import Path

from src.domain.search_entities import ImageSearchResult, SearchSource


class ImageSearchProvider(ABC):
    """Interface for image search provider implementations."""
    
    @abstractmethod
    def get_source(self) -> SearchSource:
        """Get the search source identifier."""
        pass
    
    @abstractmethod
    def search_by_image(
        self, 
        image_path: Path
    ) -> list[ImageSearchResult]:
        """Search for image and return results."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass
