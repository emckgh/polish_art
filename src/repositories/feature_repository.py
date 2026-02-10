"""Repository for image features storage and retrieval."""
import json
from typing import Optional, Protocol
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.domain.entities import ImageFeatures
from src.repositories.models import Base, ImageFeaturesModel


class FeatureRepository(Protocol):
    """Protocol for image features repository."""
    
    def save(self, features: ImageFeatures) -> ImageFeatures:
        """Store extracted features."""
        ...
    
    def find_by_artwork_id(
        self, 
        artwork_id: UUID
    ) -> Optional[ImageFeatures]:
        """Get features for specific artwork."""
        ...
    
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[ImageFeatures]:
        """List all features with pagination."""
        ...
    
    def find_by_hash(
        self,
        hash_value: str,
        hash_type: str = "phash"
    ) -> list[ImageFeatures]:
        """Find artworks with specific hash."""
        ...
    
    def delete(self, artwork_id: UUID) -> bool:
        """Remove features for artwork."""
        ...


class SQLiteFeatureRepository:
    """SQLite implementation of feature repository."""
    
    def __init__(self, connection_string: str):
        """Initialize repository with database connection.
        
        Args:
            connection_string: SQLAlchemy connection string
        """
        self._engine = create_engine(connection_string)
        if "mode=ro" not in connection_string:
            Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)
    
    def _to_entity(self, model: ImageFeaturesModel) -> ImageFeatures:
        """Convert database model to domain entity."""
        # Parse JSON fields
        clip_embedding = None
        if model.clip_embedding:
            clip_embedding = json.loads(model.clip_embedding)
        
        dominant_colors = None
        if model.dominant_colors:
            colors_list = json.loads(model.dominant_colors)
            dominant_colors = [tuple(c) for c in colors_list]
        
        return ImageFeatures(
            artwork_id=model.artwork_id,
            phash=model.phash,
            dhash=model.dhash,
            ahash=model.ahash,
            clip_embedding=clip_embedding,
            width_pixels=model.width_pixels,
            height_pixels=model.height_pixels,
            aspect_ratio=model.aspect_ratio,
            format=model.format,
            file_size_bytes=model.file_size_bytes,
            color_space=model.color_space or "",
            sharpness_score=model.sharpness_score,
            contrast_score=model.contrast_score,
            brightness_avg=model.brightness_avg,
            is_grayscale=model.is_grayscale,
            dominant_colors=dominant_colors,
            extraction_timestamp=model.extraction_timestamp,
            model_version=model.model_version
        )
    
    def _to_model(self, entity: ImageFeatures) -> ImageFeaturesModel:
        """Convert domain entity to database model."""
        # Serialize JSON fields
        clip_embedding_json = None
        if entity.clip_embedding:
            clip_embedding_json = json.dumps(entity.clip_embedding)
        
        dominant_colors_json = None
        if entity.dominant_colors:
            dominant_colors_json = json.dumps(entity.dominant_colors)
        
        return ImageFeaturesModel(
            artwork_id=entity.artwork_id,
            phash=entity.phash,
            dhash=entity.dhash,
            ahash=entity.ahash,
            clip_embedding=clip_embedding_json,
            width_pixels=entity.width_pixels,
            height_pixels=entity.height_pixels,
            aspect_ratio=entity.aspect_ratio,
            format=entity.format,
            file_size_bytes=entity.file_size_bytes,
            color_space=entity.color_space,
            sharpness_score=entity.sharpness_score,
            contrast_score=entity.contrast_score,
            brightness_avg=entity.brightness_avg,
            is_grayscale=entity.is_grayscale,
            dominant_colors=dominant_colors_json,
            extraction_timestamp=entity.extraction_timestamp,
            model_version=entity.model_version
        )
    
    def save(self, features: ImageFeatures) -> ImageFeatures:
        """Store or update extracted features."""
        session: Session = self._session_factory()
        try:
            # Check if features already exist
            existing = session.query(ImageFeaturesModel).filter_by(
                artwork_id=features.artwork_id
            ).first()
            
            if existing:
                # Update existing
                existing.phash = features.phash
                existing.dhash = features.dhash
                existing.ahash = features.ahash
                existing.clip_embedding = (
                    json.dumps(features.clip_embedding) 
                    if features.clip_embedding else None
                )
                existing.width_pixels = features.width_pixels
                existing.height_pixels = features.height_pixels
                existing.aspect_ratio = features.aspect_ratio
                existing.format = features.format
                existing.file_size_bytes = features.file_size_bytes
                existing.color_space = features.color_space
                existing.sharpness_score = features.sharpness_score
                existing.contrast_score = features.contrast_score
                existing.brightness_avg = features.brightness_avg
                existing.is_grayscale = features.is_grayscale
                existing.dominant_colors = (
                    json.dumps(features.dominant_colors)
                    if features.dominant_colors else None
                )
                existing.extraction_timestamp = features.extraction_timestamp
                existing.model_version = features.model_version
            else:
                # Create new
                model = self._to_model(features)
                session.add(model)
            
            session.commit()
            return features
        finally:
            session.close()
    
    def find_by_artwork_id(
        self, 
        artwork_id: UUID
    ) -> Optional[ImageFeatures]:
        """Get features for specific artwork."""
        session: Session = self._session_factory()
        try:
            model = session.query(ImageFeaturesModel).filter_by(
                artwork_id=artwork_id
            ).first()
            
            if model:
                return self._to_entity(model)
            return None
        finally:
            session.close()
    
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[ImageFeatures]:
        """List all features with pagination."""
        session: Session = self._session_factory()
        try:
            models = session.query(ImageFeaturesModel).limit(
                limit
            ).offset(offset).all()
            
            return [self._to_entity(m) for m in models]
        finally:
            session.close()
    
    def find_by_hash(
        self,
        hash_value: str,
        hash_type: str = "phash"
    ) -> list[ImageFeatures]:
        """Find artworks with specific hash."""
        session: Session = self._session_factory()
        try:
            if hash_type == "phash":
                models = session.query(ImageFeaturesModel).filter_by(
                    phash=hash_value
                ).all()
            elif hash_type == "dhash":
                models = session.query(ImageFeaturesModel).filter_by(
                    dhash=hash_value
                ).all()
            elif hash_type == "ahash":
                models = session.query(ImageFeaturesModel).filter_by(
                    ahash=hash_value
                ).all()
            else:
                return []
            
            return [self._to_entity(m) for m in models]
        finally:
            session.close()
    
    def delete(self, artwork_id: UUID) -> bool:
        """Remove features for artwork."""
        session: Session = self._session_factory()
        try:
            result = session.query(ImageFeaturesModel).filter_by(
                artwork_id=artwork_id
            ).delete()
            session.commit()
            return result > 0
        finally:
            session.close()
