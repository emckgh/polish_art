"""Service for searching artworks."""
from typing import Optional
from uuid import UUID

from src.domain.entities import Artwork, ArtworkStatus
from src.repositories.interfaces import ArtworkRepository


class ArtworkSearchService:
    """Service for searching and managing artworks."""
    
    def __init__(self, repository: ArtworkRepository):
        """Initialize service with repository."""
        self._repository = repository
    
    @property
    def repository(self) -> ArtworkRepository:
        """Expose repository for direct access."""
        return self._repository
    
    def add_artwork(self, artwork: Artwork) -> Artwork:
        """Add artwork to collection."""
        return self._repository.save(artwork)
    
    def get_by_id(self, artwork_id: UUID) -> Optional[Artwork]:
        """Get artwork by ID."""
        return self._repository.find_by_id(artwork_id)
    
    def search_by_artist(
        self, 
        artist_name: str,
        limit: int = 50
    ) -> list[Artwork]:
        """Search artworks by artist name."""
        all_artworks = self._repository.find_all(
            limit=limit * 2, 
            offset=0
        )
        
        matches = []
        for artwork in all_artworks:
            if artwork.artist and self._matches_artist(
                artwork.artist.name, 
                artist_name
            ):
                matches.append(artwork)
        
        return matches[:limit]
    
    def search_by_title(
        self, 
        title: str,
        limit: int = 50
    ) -> list[Artwork]:
        """Search artworks by title."""
        all_artworks = self._repository.find_all(
            limit=limit * 2,
            offset=0
        )
        
        matches = []
        for artwork in all_artworks:
            if self._matches_title(artwork.title, title):
                matches.append(artwork)
        
        return matches[:limit]
    
    def _matches_artist(
        self, 
        artwork_artist: str, 
        search_term: str
    ) -> bool:
        """Check if artist name matches search term."""
        return search_term.lower() in artwork_artist.lower()
    
    def _matches_title(
        self, 
        artwork_title: str,
        search_term: str
    ) -> bool:
        """Check if title matches search term."""
        return search_term.lower() in artwork_title.lower()
