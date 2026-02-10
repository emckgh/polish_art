"""SQLAlchemy models for database tables."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from src.domain.entities import ArtworkStatus, ImageFormat


Base = declarative_base()


class ArtworkModel(Base):
    """Database model for artworks."""
    
    __tablename__ = "artworks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    
    # Artist information
    artist_name = Column(String(200))
    artist_birth_year = Column(Integer)
    artist_death_year = Column(Integer)
    artist_nationality = Column(String(100))
    
    creation_year = Column(Integer)
    description = Column(Text)
    status = Column(Enum(ArtworkStatus), nullable=False)
    
    # Visual identification
    image_url = Column(String(1000))
    image_data = Column(LargeBinary)
    image_mime_type = Column(String(50))
    image_hash = Column(String(100))
    
    # Provenance
    last_known_location = Column(String(200))
    last_known_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    # Sync: when False, server export script omits image_data for this artwork
    include_image_on_server = Column(Boolean, default=True, nullable=True)
    
    # Relationships
    provenances = relationship("ProvenanceModel", back_populates="artwork")
    matches_as_query = relationship(
        "MatchModel",
        foreign_keys="MatchModel.query_artwork_id",
        back_populates="query_artwork"
    )
    matches_as_candidate = relationship(
        "MatchModel",
        foreign_keys="MatchModel.candidate_artwork_id",
        back_populates="candidate_artwork"
    )


class MatchModel(Base):
    """Database model for artwork matches."""
    
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    query_artwork_id = Column(
        UUID(as_uuid=True),
        ForeignKey("artworks.id"),
        nullable=False
    )
    candidate_artwork_id = Column(
        UUID(as_uuid=True),
        ForeignKey("artworks.id"),
        nullable=False
    )
    
    similarity_score = Column(Float, nullable=False)
    visual_similarity = Column(Float, nullable=False)
    metadata_similarity = Column(Float, nullable=False)
    confidence_level = Column(String(50), nullable=False)
    
    matched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    query_artwork = relationship(
        "ArtworkModel",
        foreign_keys=[query_artwork_id],
        back_populates="matches_as_query"
    )
    candidate_artwork = relationship(
        "ArtworkModel",
        foreign_keys=[candidate_artwork_id],
        back_populates="matches_as_candidate"
    )


class ProvenanceModel(Base):
    """Database model for provenance records."""
    
    __tablename__ = "provenances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    artwork_id = Column(
        UUID(as_uuid=True),
        ForeignKey("artworks.id"),
        nullable=False
    )
    
    owner_name = Column(String(200))
    location = Column(String(200))
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    source = Column(String(500), nullable=False)
    notes = Column(Text)
    is_suspicious = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    artwork = relationship("ArtworkModel", back_populates="provenances")


class ImageFeaturesModel(Base):
    """Database model for extracted image features."""
    
    __tablename__ = "image_features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    artwork_id = Column(
        UUID(as_uuid=True),
        ForeignKey("artworks.id"),
        nullable=False,
        unique=True
    )
    
    # Perceptual hashes (indexed for fast lookup)
    phash = Column(String(64), nullable=False)
    dhash = Column(String(64), nullable=False)
    ahash = Column(String(64), nullable=False)
    
    # CLIP embedding (stored as JSON array)
    clip_embedding = Column(Text)  # JSON: [0.123, -0.456, ...]
    
    # Image metadata
    width_pixels = Column(Integer, nullable=False)
    height_pixels = Column(Integer, nullable=False)
    aspect_ratio = Column(Float, nullable=False)
    format = Column(String(10), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    color_space = Column(String(20))
    
    # Quality metrics
    sharpness_score = Column(Float)
    contrast_score = Column(Float)
    brightness_avg = Column(Float)
    is_grayscale = Column(Boolean, default=False)
    
    # Dominant colors (stored as JSON)
    dominant_colors = Column(Text)  # JSON: [[255,0,0], [0,255,0], ...]
    
    # Metadata
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50), nullable=False)


class VisionAPIRequestModel(Base):
    """Database model for Google Vision API requests."""
    
    __tablename__ = "vision_api_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    artwork_id = Column(
        UUID(as_uuid=True),
        ForeignKey("artworks.id"),
        nullable=False
    )
    
    request_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    image_source = Column(String(20), nullable=False)  # 'database' or 'url'
    api_cost_units = Column(Integer, default=1, nullable=False)
    
    # Summary statistics
    total_full_matches = Column(Integer, default=0, nullable=False)
    total_partial_matches = Column(Integer, default=0, nullable=False)
    total_similar_images = Column(Integer, default=0, nullable=False)
    total_pages_with_image = Column(Integer, default=0, nullable=False)
    
    best_match_score = Column(Float)
    has_interesting_results = Column(Boolean, default=False, nullable=False)
    processing_time_ms = Column(Integer)
    
    # Relationships
    matches = relationship("VisionAPIMatchModel", back_populates="request", cascade="all, delete-orphan")
    entities = relationship("VisionAPIEntityModel", back_populates="request", cascade="all, delete-orphan")


class VisionAPIMatchModel(Base):
    """Database model for Vision API image matches."""
    
    __tablename__ = "vision_api_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vision_api_requests.id"),
        nullable=False
    )
    
    match_type = Column(String(20), nullable=False)  # 'full', 'partial', 'similar'
    image_url = Column(String(2000), nullable=False)
    confidence_score = Column(Float)
    page_url = Column(String(2000))
    page_title = Column(String(500))
    domain = Column(String(200))
    domain_category = Column(String(50))  # 'auction', 'museum', 'marketplace', 'social', 'other'
    
    # Relationships
    request = relationship("VisionAPIRequestModel", back_populates="matches")


class VisionAPIEntityModel(Base):
    """Database model for Vision API web entities."""
    
    __tablename__ = "vision_api_entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vision_api_requests.id"),
        nullable=False
    )
    
    entity_description = Column(String(500))
    entity_score = Column(Float)
    
    # Relationships
    request = relationship("VisionAPIRequestModel", back_populates="entities")


class VisionAPIDomainStatsModel(Base):
    """Database model for aggregated domain statistics."""
    
    __tablename__ = "vision_api_domain_stats"
    
    domain = Column(String(200), primary_key=True)
    category = Column(String(50))
    total_appearances = Column(Integer, default=1, nullable=False)
    artworks_found = Column(Text)  # JSON array of artwork IDs
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    flagged_suspicious = Column(Boolean, default=False, nullable=False)
