"""SQLite implementation of artwork repository."""
from typing import Optional
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.entities import Artwork, Artist, ArtworkStatus
from src.repositories.interfaces import ArtworkRepository
from src.repositories.models import ArtworkModel, Base


class SQLiteArtworkRepository(ArtworkRepository):
    """SQLite implementation of artwork repository."""
    
    def __init__(self, database_url: str):
        """Initialize repository with database connection."""
        self._engine = create_engine(database_url)
        if "mode=ro" not in database_url:
            Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)
    
    def save(self, artwork: Artwork) -> Artwork:
        """Save artwork to database."""
        session = self._session_factory()
        try:
            model = self._to_model(artwork)
            session.merge(model)
            session.commit()
            return artwork
        finally:
            session.close()
    
    def find_by_id(self, artwork_id) -> Optional[Artwork]:
        """Find artwork by ID."""
        session = self._session_factory()
        try:
            # Support both UUID and int IDs
            if isinstance(artwork_id, str):
                from uuid import UUID
                artwork_id = UUID(artwork_id)
            
            model = session.query(ArtworkModel).filter(
                ArtworkModel.id == artwork_id
            ).first()
            return self._to_entity(model) if model else None
        finally:
            session.close()
    
    def find_all(self, limit: int, offset: int) -> list[Artwork]:
        """Find all artworks with pagination."""
        session = self._session_factory()
        try:
            models = session.query(ArtworkModel).limit(
                limit
            ).offset(offset).all()
            # Convert to entities but skip loading image_data
            return [self._to_entity(m, skip_image_data=True) for m in models]
        finally:
            session.close()
    
    def delete(self, artwork_id: UUID) -> bool:
        """Delete artwork by ID."""
        session = self._session_factory()
        try:
            result = session.query(ArtworkModel).filter(
                ArtworkModel.id == artwork_id
            ).delete()
            session.commit()
            return result > 0
        finally:
            session.close()
    
    def _to_model(self, artwork: Artwork) -> ArtworkModel:
        """Convert entity to database model."""
        return ArtworkModel(
            id=artwork.id,
            title=artwork.title,
            artist_name=artwork.artist.name if artwork.artist else None,
            artist_birth_year=artwork.artist.birth_year if artwork.artist else None,
            artist_death_year=artwork.artist.death_year if artwork.artist else None,
            artist_nationality=artwork.artist.nationality if artwork.artist else None,
            creation_year=artwork.creation_year,
            description=artwork.description,
            status=artwork.status,
            image_url=artwork.image_url,
            image_data=artwork.image_data,
            image_mime_type=artwork.image_mime_type,
            image_hash=artwork.image_hash,
            last_known_location=artwork.last_known_location,
            last_known_date=artwork.last_known_date,
            created_at=artwork.created_at,
            updated_at=artwork.updated_at
        )
    
    def _to_entity(self, model: ArtworkModel, skip_image_data: bool = False) -> Artwork:
        """Convert database model to entity."""
        artist = None
        if model.artist_name:
            artist = Artist(
                name=model.artist_name,
                birth_year=model.artist_birth_year,
                death_year=model.artist_death_year,
                nationality=model.artist_nationality
            )
        
        # Skip loading image_data for list queries (performance)
        image_data = None if skip_image_data else model.image_data
        
        return Artwork(
            id=model.id,
            title=model.title,
            artist=artist,
            creation_year=model.creation_year,
            description=model.description,
            status=model.status,
            image_url=model.image_url,
            image_data=image_data,
            image_mime_type=model.image_mime_type,
            image_hash=model.image_hash,
            last_known_location=model.last_known_location,
            last_known_date=model.last_known_date,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
