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
        nullable=False
    )
    
    perceptual_hash = Column(String(100), nullable=False)
    embedding_vector = Column(Text, nullable=False)
    width_pixels = Column(Integer, nullable=False)
    height_pixels = Column(Integer, nullable=False)
    format = Column(Enum(ImageFormat), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
