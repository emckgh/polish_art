"""Domain entities for Polish Looted Art Discovery Engine."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ArtworkStatus(Enum):
    """Status of artwork in the system."""
    KNOWN_LOOTED = "known_looted"
    SUSPECTED = "suspected"
    RECOVERED = "recovered"
    VERIFIED = "verified"


class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "jpg"
    PNG = "png"
    TIFF = "tiff"


@dataclass(frozen=True)
class Artist:
    """Artist information."""
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = None


@dataclass
class Artwork:
    """Core artwork entity representing a piece of art."""
    
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    artist: Optional[Artist] = None
    creation_year: Optional[int] = None
    description: str = ""
    status: ArtworkStatus = ArtworkStatus.SUSPECTED
    
    # Visual identification
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    image_mime_type: Optional[str] = None
    image_hash: Optional[str] = None
    
    # Provenance
    last_known_location: Optional[str] = None
    last_known_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate artwork data."""
        if not self.title and not self.artist:
            raise ValueError("Artwork must have title or artist")
        
        if self.creation_year and self.creation_year < 0:
            raise ValueError("Creation year cannot be negative")


@dataclass
class ImageFeatures:
    """Complete feature set for artwork image."""
    
    # Identity
    artwork_id: UUID = field(default_factory=uuid4)
    
    # Perceptual Hashes (for fast similarity)
    phash: str = ""
    dhash: str = ""
    ahash: str = ""
    
    # Semantic Embeddings (for deep similarity)
    clip_embedding: Optional[list[float]] = None
    
    # Image Metadata
    width_pixels: int = 0
    height_pixels: int = 0
    aspect_ratio: float = 0.0
    format: str = ""
    file_size_bytes: int = 0
    color_space: str = ""
    
    # Quality Metrics
    sharpness_score: Optional[float] = None
    contrast_score: Optional[float] = None
    brightness_avg: Optional[float] = None
    is_grayscale: bool = False
    
    # Dominant Colors (RGB tuples as JSON)
    dominant_colors: Optional[list[tuple[int, int, int]]] = None
    
    # Timestamps
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "v1.0.0"


@dataclass(frozen=True)
class Match:
    """Potential match between query and candidate artwork."""
    
    query_artwork_id: UUID
    candidate_artwork_id: UUID
    similarity_score: float
    visual_similarity: float
    metadata_similarity: float
    confidence_level: str
    matched_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate match data."""
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError(
                "Similarity score must be between 0.0 and 1.0"
            )
        
        if self.query_artwork_id == self.candidate_artwork_id:
            raise ValueError("Cannot match artwork with itself")


@dataclass
class Provenance:
    """Provenance record tracking artwork ownership history."""
    
    id: UUID = field(default_factory=uuid4)
    artwork_id: UUID = field(default_factory=uuid4)
    owner_name: Optional[str] = None
    location: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    source: str = ""
    notes: str = ""
    is_suspicious: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
