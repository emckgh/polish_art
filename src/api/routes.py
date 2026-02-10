"""FastAPI routes for artwork browsing."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.api.schemas import (
    ArtworkListSchema,
    ArtworkSchema,
    SearchQuerySchema
)
from src.constants import (
    CacheConstants,
    HttpConstants,
    PaginationConstants,
    get_database_url,
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
    return SQLiteArtworkRepository(get_database_url())


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
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    logger.info(f"GET /api/artworks - page={page}, page_size={page_size}")
    
    start = time.time()
    offset = (page - PaginationConstants.DEFAULT_PAGE) * page_size
    
    logger.info(f"Calling repository.find_all(limit={page_size}, offset={offset})")
    artworks = service.repository.find_all(
        limit=page_size,
        offset=offset
    )
    repo_time = time.time() - start
    logger.info(f"Repository returned {len(artworks)} artworks in {repo_time:.2f}s")
    
    logger.info("Getting total count with COUNT(*) query...")
    start = time.time()
    # Use COUNT(*) instead of loading all records
    from src.repositories.sqlite_repository import SQLiteArtworkRepository
    from src.repositories.models import ArtworkModel
    repo = service.repository
    if isinstance(repo, SQLiteArtworkRepository):
        session = repo._session_factory()
        try:
            total = session.query(ArtworkModel).count()
        finally:
            session.close()
    else:
        total = len(service.repository.find_all(
            limit=PaginationConstants.MAX_RECORDS_FOR_COUNT, 
            offset=0
        ))
    count_time = time.time() - start
    logger.info(f"Total count: {total} (took {count_time:.2f}s)")
    
    total_pages = (total + page_size - PaginationConstants.DEFAULT_PAGE) // page_size
    
    logger.info("Converting artworks to dicts...")
    start = time.time()
    artwork_dicts = [artwork_to_dict(a) for a in artworks]
    dict_time = time.time() - start
    logger.info(f"Conversion to dicts completed in {dict_time:.2f}s")
    
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
    from uuid import UUID
    from src.repositories.feature_repository import SQLiteFeatureRepository
    
    # Verify artwork exists
    artwork = repository.find_by_id(artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Get features
    feature_repo = SQLiteFeatureRepository(get_database_url())
    features = feature_repo.find_by_artwork_id(UUID(artwork_id))
    
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
    from uuid import UUID
    from src.repositories.feature_repository import SQLiteFeatureRepository
    from src.services.similarity_service import SimilarityService
    
    # Convert string ID to UUID
    try:
        artwork_uuid = UUID(artwork_id)
    except ValueError:
        raise HTTPException(
            status_code=HttpConstants.STATUS_BAD_REQUEST,
            detail="Invalid artwork ID format"
        )
    
    # Verify artwork exists
    artwork = repository.find_by_id(artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=HttpConstants.STATUS_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Initialize services
    feature_repo = SQLiteFeatureRepository(get_database_url())
    similarity_service = SimilarityService(feature_repo, repository)
    
    # Find similar artworks based on method
    if method == "hash":
        results = similarity_service.find_similar_by_hash(
            artwork_id=artwork_uuid,
            threshold=15,
            limit=limit
        )
    elif method == "clip":
        results = similarity_service.find_similar_by_clip(
            artwork_id=artwork_uuid,
            threshold=0.75,
            limit=limit
        )
    else:  # hybrid
        results = similarity_service.find_similar_hybrid(
            artwork_id=artwork_uuid,
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
    feature_repo = SQLiteFeatureRepository(get_database_url())
    similarity_service = SimilarityService(feature_repo, repository)
    
    # Find duplicates
    duplicates = similarity_service.find_duplicates(threshold=threshold)
    
    return {
        "threshold": threshold,
        "duplicate_groups": len(duplicates),
        "groups": duplicates
    }


# Vision API tracking endpoints

@router.get("/vision/cost-summary")
async def get_vision_cost_summary():
    """Get Vision API cost summary."""
    from src.repositories.vision_repository import VisionAPIRepository
    from src.services.vision_tracking_service import VisionAPITrackingService
    
    repository = VisionAPIRepository(get_database_url())
    service = VisionAPITrackingService(repository)
    
    total_cost = service.get_total_api_cost()
    
    return {
        "total_api_units": total_cost,
        "estimated_cost_usd": round(total_cost * 0.0015, 2),
        "note": "Based on $1.50 per 1,000 requests after free tier"
    }


@router.get("/vision/findings")
async def get_vision_findings(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get interesting Vision API findings."""
    from src.repositories.vision_repository import VisionAPIRepository
    from src.services.vision_tracking_service import VisionAPITrackingService
    
    repository = VisionAPIRepository(get_database_url())
    service = VisionAPITrackingService(repository)
    
    findings = service.get_interesting_findings(limit=limit, offset=offset)
    
    return {
        "total": len(findings),
        "limit": limit,
        "offset": offset,
        "findings": [
            {
                "id": str(finding.id),
                "artwork_id": str(finding.artwork_id),
                "request_timestamp": finding.request_timestamp.isoformat(),
                "total_full_matches": finding.total_full_matches,
                "total_partial_matches": finding.total_partial_matches,
                "total_similar_images": finding.total_similar_images,
                "total_pages_with_image": finding.total_pages_with_image,
                "best_match_score": finding.best_match_score,
                "processing_time_ms": finding.processing_time_ms,
                "matches": [
                    {
                        "match_type": m.match_type,
                        "image_url": m.image_url,
                        "page_url": m.page_url,
                        "page_title": m.page_title,
                        "domain": m.domain,
                        "domain_category": m.domain_category,
                        "confidence_score": m.confidence_score
                    }
                    for m in finding.matches
                ],
                "web_entities": [
                    {
                        "entity_description": e.entity_description,
                        "entity_score": e.entity_score
                    }
                    for e in finding.entities
                ]
            }
            for finding in findings
        ]
    }


@router.get("/vision/request/{request_id}")
async def get_vision_request_details(request_id: str):
    """Get full details (matches, entities) for a single Vision API request."""
    from uuid import UUID
    from src.repositories.vision_repository import VisionAPIRepository
    from src.services.vision_tracking_service import VisionAPITrackingService

    try:
        rid = UUID(request_id)
    except ValueError:
        raise HTTPException(
            status_code=HttpConstants.STATUS_BAD_REQUEST,
            detail="Invalid request ID format"
        )

    repository = VisionAPIRepository(get_database_url())
    service = VisionAPITrackingService(repository)
    request_entity = service.get_request_by_id(rid)
    if not request_entity:
        raise HTTPException(status_code=404, detail="Vision API request not found")

    return {
        "id": str(request_entity.id),
        "artwork_id": str(request_entity.artwork_id),
        "request_timestamp": request_entity.request_timestamp.isoformat(),
        "total_full_matches": request_entity.total_full_matches,
        "total_partial_matches": request_entity.total_partial_matches,
        "total_similar_images": request_entity.total_similar_images,
        "total_pages_with_image": request_entity.total_pages_with_image,
        "best_match_score": request_entity.best_match_score,
        "processing_time_ms": request_entity.processing_time_ms,
        "matches": [
            {
                "match_type": m.match_type,
                "image_url": m.image_url,
                "page_url": m.page_url,
                "page_title": m.page_title,
                "domain": m.domain,
                "domain_category": m.domain_category,
                "confidence_score": m.confidence_score
            }
            for m in request_entity.matches
        ],
        "web_entities": [
            {
                "entity_description": e.entity_description,
                "entity_score": e.entity_score
            }
            for e in request_entity.entities
        ]
    }


@router.get("/vision/artwork/{artwork_id}/searches")
async def get_artwork_vision_searches(artwork_id: str):
    """Get Vision API search history for an artwork."""
    from uuid import UUID
    from src.repositories.vision_repository import VisionAPIRepository
    from src.services.vision_tracking_service import VisionAPITrackingService

    repository = VisionAPIRepository(get_database_url())
    service = VisionAPITrackingService(repository)

    try:
        searches = service.get_artwork_search_history(UUID(artwork_id), limit=10)
    except ValueError:
        raise HTTPException(
            status_code=HttpConstants.STATUS_BAD_REQUEST,
            detail="Invalid artwork ID format"
        )

    return {
        "artwork_id": artwork_id,
        "total_searches": len(searches),
        "searches": [
            {
                "id": str(search.id),
                "request_timestamp": search.request_timestamp.isoformat(),
                "has_interesting_results": search.has_interesting_results,
                "total_full_matches": search.total_full_matches,
                "total_partial_matches": search.total_partial_matches,
                "total_similar_images": search.total_similar_images,
                "total_pages_with_image": search.total_pages_with_image,
                "best_match_score": search.best_match_score,
                "api_cost_units": search.api_cost_units
            }
            for search in searches
        ]
    }


@router.get("/vision/domains/suspicious")
async def get_suspicious_domains():
    """Get domains flagged as suspicious."""
    from src.repositories.vision_repository import VisionAPIRepository
    from src.services.vision_tracking_service import VisionAPITrackingService
    
    repository = VisionAPIRepository(get_database_url())
    service = VisionAPITrackingService(repository)
    
    domains = service.get_suspicious_domains()
    
    return {
        "total": len(domains),
        "domains": [
            {
                "domain": d.domain,
                "category": d.category,
                "total_appearances": d.total_appearances,
                "artworks_found": d.artworks_found,
                "first_seen": d.first_seen.isoformat(),
                "last_seen": d.last_seen.isoformat()
            }
            for d in domains
        ]
    }


@router.get("/vision/domains/{category}")
async def get_domains_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get domain statistics by category."""
    from src.repositories.vision_repository import VisionAPIRepository
    from src.services.vision_tracking_service import VisionAPITrackingService
    
    valid_categories = ['auction', 'marketplace', 'museum', 'social', 'academic', 'other']
    if category not in valid_categories:
        raise HTTPException(
            status_code=HttpConstants.STATUS_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    repository = VisionAPIRepository(get_database_url())
    service = VisionAPITrackingService(repository)
    
    domains = service.get_domain_stats_by_category(category, limit=limit)
    
    return {
        "category": category,
        "total": len(domains),
        "domains": [
            {
                "domain": d.domain,
                "total_appearances": d.total_appearances,
                "artworks_found": len(d.artworks_found),
                "first_seen": d.first_seen.isoformat(),
                "last_seen": d.last_seen.isoformat(),
                "flagged_suspicious": d.flagged_suspicious
            }
            for d in domains
        ]
    }


@router.get("/vision/artwork-status")
async def get_artwork_vision_status():
    """Get Vision API status for all artworks."""
    from src.repositories.vision_repository import VisionAPIRepository
    from sqlalchemy import create_engine, text
    from src.utils.uuid_utils import format_uuid_with_hyphens
    
    # Use raw SQL to get all unique artwork IDs with their status
    engine = create_engine(get_database_url())
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                artwork_id,
                MAX(CASE WHEN has_interesting_results = 1 THEN 1 ELSE 0 END) as has_interesting
            FROM vision_api_requests
            GROUP BY artwork_id
        """))
        
        status_list = []
        for row in result:
            # Convert the artwork_id to UUID format with hyphens
            artwork_id = format_uuid_with_hyphens(str(row[0]))
            
            status_list.append({
                "artwork_id": artwork_id,
                "has_searches": True,
                "has_interesting_results": bool(row[1])
            })
        
        return status_list


@router.get("/vision/stats")
async def get_vision_stats():
    """Get Vision API usage statistics."""
    from sqlalchemy import create_engine, text
    
    engine = create_engine(get_database_url())
    
    with engine.connect() as conn:
        # Get total API units used
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(api_cost_units) as total_units,
                COUNT(DISTINCT artwork_id) as unique_artworks,
                COUNT(DISTINCT CASE WHEN has_interesting_results = 1 THEN artwork_id END) as interesting_count
            FROM vision_api_requests
        """))
        
        row = result.fetchone()
        
        return {
            "total_requests": row[0] or 0,
            "total_units": row[1] or 0,
            "unique_artworks": row[2] or 0,
            "interesting_count": row[3] or 0
        }

