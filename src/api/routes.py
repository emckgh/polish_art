"""FastAPI routes for artwork browsing."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.api.schemas import (
    ArtworkListSchema,
    ArtworkSchema,
    SearchQuerySchema
)
from src.constants import CacheConstants, HttpConstants, PaginationConstants
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
    page: int = Query(
        PaginationConstants.DEFAULT_PAGE, 
        ge=PaginationConstants.DEFAULT_PAGE
    ),
    page_size: int = Query(
        PaginationConstants.DEFAULT_PAGE_SIZE,
        ge=PaginationConstants.DEFAULT_PAGE,
        le=PaginationConstants.MAX_PAGE_SIZE
    ),
    service: ArtworkSearchService = Depends(get_artwork_service)
):
    """List all artworks with pagination."""
    offset = (page - PaginationConstants.DEFAULT_PAGE) * page_size
    artworks = service.repository.find_all(
        limit=page_size,
        offset=offset
    )
    
    total = len(service.repository.find_all(
        limit=PaginationConstants.MAX_RECORDS_FOR_COUNT, 
        offset=0
    ))
    total_pages = (total + page_size - PaginationConstants.DEFAULT_PAGE) // page_size
    
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
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Artwork not found"
        )
    return artwork_to_dict(artwork)


@router.get("/artworks/search/query")
async def search_artworks(
    q: str = Query(
        ..., 
        min_length=PaginationConstants.MIN_SEARCH_QUERY_LENGTH
    ),
    page: int = Query(
        PaginationConstants.DEFAULT_PAGE,
        ge=PaginationConstants.DEFAULT_PAGE
    ),
    page_size: int = Query(
        PaginationConstants.DEFAULT_PAGE_SIZE,
        ge=PaginationConstants.DEFAULT_PAGE,
        le=PaginationConstants.MAX_PAGE_SIZE
    ),
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
    
    offset = (page - PaginationConstants.DEFAULT_PAGE) * page_size
    paginated = results_list[offset:offset + page_size]
    
    total = len(results_list)
    total_pages = (
        (total + page_size - PaginationConstants.DEFAULT_PAGE) // page_size
    )
    
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
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Artwork not found"
        )
    
    if not artwork.image_data:
        raise HTTPException(
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Image not available for this artwork"
        )
    
    return Response(
        content=artwork.image_data,
        media_type=artwork.image_mime_type or "image/jpeg",
        headers={
            "Cache-Control": (
                f"public, max-age={HttpConstants.CACHE_DURATION_ONE_DAY}"
            ),
            "ETag": (
                artwork.image_hash[:CacheConstants.ETAG_HASH_LENGTH] 
                if artwork.image_hash else None
            )
        }
    )


@router.get("/artworks/{artwork_id}/features")
async def get_artwork_features(
    artwork_id: str,
    repository: ArtworkRepository = Depends(get_repository)
):
    """Get computer vision features for an artwork."""
    from src.repositories.feature_repository import SQLiteFeatureRepository
    
    # Verify artwork exists
    artwork = repository.find_by_id(artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Get features
    feature_repo = SQLiteFeatureRepository("sqlite:///artworks.db")
    features = feature_repo.find_by_artwork_id(artwork_id)
    
    if not features:
        raise HTTPException(
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Features not extracted for this artwork"
        )
    
    return {
        "artwork_id": features.artwork_id,
        "phash": features.phash,
        "dhash": features.dhash,
        "ahash": features.ahash,
        "clip_embedding": features.clip_embedding,
        "width_pixels": features.width_pixels,
        "height_pixels": features.height_pixels,
        "aspect_ratio": features.aspect_ratio,
        "format": features.format,
        "file_size_bytes": features.file_size_bytes,
        "color_space": features.color_space,
        "sharpness_score": features.sharpness_score,
        "contrast_score": features.contrast_score,
        "brightness_avg": features.brightness_avg,
        "is_grayscale": features.is_grayscale,
        "dominant_colors": features.dominant_colors,
        "extraction_timestamp": features.extraction_timestamp,
        "model_version": features.model_version
    }


@router.get("/artworks/{artwork_id}/similar")
async def find_similar_artworks(
    artwork_id: str,
    method: str = Query("hybrid", regex="^(hash|clip|hybrid)$"),
    limit: int = Query(10, ge=1, le=50),
    repository: ArtworkRepository = Depends(get_repository)
):
    """Find similar artworks using CV features.
    
    Args:
        artwork_id: Source artwork ID
        method: Similarity method (hash, clip, or hybrid)
        limit: Maximum number of results
    
    Returns:
        List of similar artworks with similarity scores
    """
    from src.repositories.feature_repository import SQLiteFeatureRepository
    from src.services.similarity_service import SimilarityService
    
    # Verify artwork exists
    artwork = repository.find_by_id(artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Initialize services
    feature_repo = SQLiteFeatureRepository("sqlite:///artworks.db")
    similarity_service = SimilarityService(feature_repo, repository)
    
    # Find similar artworks based on method
    if method == "hash":
        results = similarity_service.find_similar_by_hash(
            artwork_id=artwork_id,
            threshold=15,
            limit=limit
        )
    elif method == "clip":
        results = similarity_service.find_similar_by_clip(
            artwork_id=artwork_id,
            threshold=0.75,
            limit=limit
        )
    else:  # hybrid
        results = similarity_service.find_similar_hybrid(
            artwork_id=artwork_id,
            hash_threshold=15,
            clip_threshold=0.75,
            limit=limit
        )
    
    return {
        "source_artwork_id": artwork_id,
        "method": method,
        "count": len(results),
        "similar_artworks": results
    }


@router.get("/artworks/duplicates/detect")
async def detect_duplicates(
    threshold: int = Query(5, ge=0, le=20),
    repository: ArtworkRepository = Depends(get_repository)
):
    """Detect potential duplicate artworks using perceptual hashes.
    
    Args:
        threshold: Maximum Hamming distance to consider duplicates (lower = stricter)
    
    Returns:
        List of duplicate groups
    """
    from src.repositories.feature_repository import SQLiteFeatureRepository
    from src.services.similarity_service import SimilarityService
    
    # Initialize services
    feature_repo = SQLiteFeatureRepository("sqlite:///artworks.db")
    similarity_service = SimilarityService(feature_repo, repository)
    
    # Find duplicates
    duplicates = similarity_service.find_duplicates(threshold=threshold)
    
    return {
        "threshold": threshold,
        "duplicate_groups": len(duplicates),
        "groups": duplicates
    }
