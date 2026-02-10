"""Domain entities for Google Vision API tracking."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4


@dataclass
class VisionAPIMatch:
    """Represents a single image match from Vision API."""
    match_type: str  # 'full', 'partial', 'similar'
    image_url: str
    confidence_score: Optional[float] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    domain: Optional[str] = None
    domain_category: Optional[str] = None  # 'auction', 'museum', 'marketplace', 'social', 'other'


@dataclass
class VisionAPIEntity:
    """Represents a web entity identified by Vision API."""
    entity_description: str
    entity_score: Optional[float] = None


@dataclass
class VisionAPIRequest:
    """Represents a complete Vision API reverse image search request."""
    artwork_id: UUID
    image_source: str  # 'database' or 'url'
    total_full_matches: int = 0
    total_partial_matches: int = 0
    total_similar_images: int = 0
    total_pages_with_image: int = 0
    best_match_score: Optional[float] = None
    has_interesting_results: bool = False
    api_cost_units: int = 1
    processing_time_ms: Optional[int] = None
    matches: List[VisionAPIMatch] = field(default_factory=list)
    entities: List[VisionAPIEntity] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    request_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VisionAPIDomainStats:
    """Aggregated statistics for a domain."""
    domain: str
    category: Optional[str] = None
    total_appearances: int = 1
    artworks_found: List[str] = field(default_factory=list)  # List of artwork IDs
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    flagged_suspicious: bool = False
