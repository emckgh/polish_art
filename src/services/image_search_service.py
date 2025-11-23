"""Service for conducting multi-source image searches."""
from pathlib import Path

from src.domain.search_entities import (
    ImageSearchReport,
    SearchSource
)
from src.scrapers.interfaces import ImageSearchProvider


class ImageSearchService:
    """Service to search for images across multiple sources."""
    
    def __init__(self, providers: list[ImageSearchProvider]):
        """Initialize service with search providers."""
        self._providers = providers
    
    def search_image(
        self, 
        image_path: Path
    ) -> ImageSearchReport:
        """Search for image across all configured providers."""
        report = ImageSearchReport(image_path=str(image_path))
        
        available_providers = [
            p for p in self._providers 
            if p.is_available()
        ]
        
        for provider in available_providers:
            source = provider.get_source()
            report.sources_searched.append(source)
            
            results = provider.search_by_image(image_path)
            
            for result in results:
                report.add_result(result)
        
        from datetime import datetime
        report.search_completed = datetime.utcnow()
        
        return report
    
    def get_available_sources(self) -> list[SearchSource]:
        """Get list of available search sources."""
        return [
            p.get_source() 
            for p in self._providers 
            if p.is_available()
        ]
