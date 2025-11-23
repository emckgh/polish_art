"""FastAPI routes for artwork browsing."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.api.schemas import (
    ArtworkListSchema,
    ArtworkSchema,
    SearchQuerySchema
)
from src.repositories.interfaces import ArtworkRepository
from src.repositories.sqlite_repository import (
    SQLiteArtworkRepository
)
from src.services.artwork_service import ArtworkSearchService


router = APIRouter(prefix="/api", tags=["artworks"])


def artwork_to_dict(artwork):
    """Convert Artwork entity to dict for API response."""
    return {
        "id": str(artwork.id),
        "title": artwork.title,
        "artist": {
            "name": artwork.artist.name,
            "nationality": artwork.artist.nationality,
            "birth_year": artwork.artist.birth_year,
            "death_year": artwork.artist.death_year
        } if artwork.artist else None,
        "creation_year": artwork.creation_year,
        "description": artwork.description,
        "image_url": artwork.image_url,
        "image_hash": artwork.image_hash,
        "status": artwork.status.value,
        "last_known_location": artwork.last_known_location,
        "last_known_date": artwork.last_known_date,
        "created_at": artwork.created_at,
        "updated_at": artwork.updated_at
    }


def get_repository() -> ArtworkRepository:
    """Dependency injection for repository."""
    return SQLiteArtworkRepository("sqlite:///artworks.db")


def get_artwork_service(
    repo: ArtworkRepository = Depends(get_repository)
) -> ArtworkSearchService:
    """Dependency injection for artwork service."""
    return ArtworkSearchService(repository=repo)


@router.get("/artworks", response_model=ArtworkListSchema)
async def list_artworks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: ArtworkSearchService = Depends(get_artwork_service)
):
    """List all artworks with pagination."""
    offset = (page - 1) * page_size
    artworks = service.repository.find_all(
        limit=page_size,
        offset=offset
    )
    
    total = len(service.repository.find_all(limit=10000, offset=0))
    total_pages = (total + page_size - 1) // page_size
    
    artwork_dicts = [artwork_to_dict(a) for a in artworks]
    
    return ArtworkListSchema(
        items=artwork_dicts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/artworks/{artwork_id}")
async def get_artwork(
    artwork_id: str,
    service: ArtworkSearchService = Depends(get_artwork_service)
):
    """Get artwork by ID."""
    artwork = service.repository.find_by_id(artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found"
        )
    return artwork_to_dict(artwork)


@router.get("/artworks/search/query")
async def search_artworks(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: ArtworkSearchService = Depends(get_artwork_service)
):
    """Search artworks by artist or title."""
    artist_results = service.search_by_artist(q)
    title_results = service.search_by_title(q)
    
    all_results = {a.id: a for a in artist_results}
    for artwork in title_results:
        if artwork.id not in all_results:
            all_results[artwork.id] = artwork
    
    results_list = list(all_results.values())
    
    offset = (page - 1) * page_size
    paginated = results_list[offset:offset + page_size]
    
    total = len(results_list)
    total_pages = (total + page_size - 1) // page_size
    
    artwork_dicts = [artwork_to_dict(a) for a in paginated]
    
    return ArtworkListSchema(
        items=artwork_dicts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/artworks/{artwork_id}/image")
async def get_artwork_image(
    artwork_id: str,
    service: ArtworkSearchService = Depends(get_artwork_service)
):
    """Get artwork image as binary data."""
    artwork = service.repository.find_by_id(artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found"
        )
    
    if not artwork.image_data:
        raise HTTPException(
            status_code=404,
            detail="Image not available for this artwork"
        )
    
    return Response(
        content=artwork.image_data,
        media_type=artwork.image_mime_type or "image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "ETag": artwork.image_hash[:32] if artwork.image_hash else None
        }
    )
