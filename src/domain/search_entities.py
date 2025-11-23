"""Domain entities for image search results."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class SearchSource(Enum):
    """Source where image search was performed."""
    GOOGLE_IMAGES = "google_images"
    TINEYE = "tineye"
    AUCTION_HOUSE = "auction_house"
    MUSEUM_DATABASE = "museum_database"
    ART_MARKETPLACE = "art_marketplace"


class SearchStatus(Enum):
    """Status of search operation."""
    SUCCESS = "success"
    FAILED = "failed"
    NO_RESULTS = "no_results"
    API_ERROR = "api_error"


@dataclass
class ImageSearchResult:
    """Result from searching for an image at a specific source."""
    
    id: UUID = field(default_factory=uuid4)
    source: SearchSource = SearchSource.GOOGLE_IMAGES
    status: SearchStatus = SearchStatus.SUCCESS
    url_found: Optional[str] = None
    page_title: Optional[str] = None
    page_url: Optional[str] = None
    similarity_score: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


@dataclass
class ImageSearchReport:
    """Comprehensive report of image search across sources."""
    
    id: UUID = field(default_factory=uuid4)
    image_path: str = ""
    image_hash: Optional[str] = None
    sources_searched: list[SearchSource] = field(default_factory=list)
    results_found: list[ImageSearchResult] = field(default_factory=list)
    total_matches: int = 0
    search_started: datetime = field(default_factory=datetime.utcnow)
    search_completed: Optional[datetime] = None
    
    def add_result(self, result: ImageSearchResult) -> None:
        """Add search result to report."""
        self.results_found.append(result)
        if result.status == SearchStatus.SUCCESS and result.url_found:
            self.total_matches += 1
    
    def get_results_by_source(
        self, 
        source: SearchSource
    ) -> list[ImageSearchResult]:
        """Get results filtered by source."""
        return [
            r for r in self.results_found 
            if r.source == source
        ]
    
    def was_found(self) -> bool:
        """Check if image was found anywhere."""
        return self.total_matches > 0
