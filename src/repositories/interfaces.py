"""Repository interface definitions."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities import Artwork, Match, Provenance


class ArtworkRepository(ABC):
    """Interface for artwork data access."""
    
    @abstractmethod
    def save(self, artwork: Artwork) -> Artwork:
        """Save artwork to storage."""
        pass
    
    @abstractmethod
    def find_by_id(self, artwork_id: UUID) -> Optional[Artwork]:
        """Find artwork by ID."""
        pass
    
    @abstractmethod
    def find_all(self, limit: int, offset: int) -> list[Artwork]:
        """Find all artworks with pagination."""
        pass
    
    @abstractmethod
    def delete(self, artwork_id: UUID) -> bool:
        """Delete artwork by ID."""
        pass


class MatchRepository(ABC):
    """Interface for match data access."""
    
    @abstractmethod
    def save(self, match: Match) -> Match:
        """Save match to storage."""
        pass
    
    @abstractmethod
    def find_by_artwork(
        self, 
        artwork_id: UUID,
        min_score: float
    ) -> list[Match]:
        """Find matches for artwork above threshold."""
        pass


class ProvenanceRepository(ABC):
    """Interface for provenance data access."""
    
    @abstractmethod
    def save(self, provenance: Provenance) -> Provenance:
        """Save provenance record."""
        pass
    
    @abstractmethod
    def find_by_artwork(
        self, 
        artwork_id: UUID
    ) -> list[Provenance]:
        """Find provenance records for artwork."""
        pass
