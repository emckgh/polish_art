"""Service for importing artworks into database."""
from src.domain.entities import Artwork
from src.repositories.interfaces import ArtworkRepository


class ArtworkImportService:
    """Service for importing artworks into database."""
    
    def __init__(self, repository: ArtworkRepository):
        """Initialize service with repository."""
        self._repository = repository
    
    def import_artwork(self, artwork: Artwork) -> Artwork:
        """Import single artwork into database."""
        return self._repository.save(artwork)
    
    def import_batch(
        self, 
        artworks: list[Artwork]
    ) -> dict[str, int]:
        """Import batch of artworks and return statistics."""
        imported_count = 0
        failed_count = 0
        
        for artwork in artworks:
            try:
                self._repository.save(artwork)
                imported_count += 1
            except Exception:
                failed_count += 1
        
        return {
            "imported": imported_count,
            "failed": failed_count,
            "total": len(artworks)
        }
