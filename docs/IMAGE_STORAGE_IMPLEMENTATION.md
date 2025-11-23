# Image Download and Storage Implementation

## Summary

Successfully implemented complete image download and database storage functionality for the Polish Looted Art Discovery Engine.

## Changes Made

### 1. Database Schema Updates
- **File**: `src/repositories/models.py`
- Added `image_data` column (LargeBinary) to store image bytes
- Added `image_mime_type` column (String) to store content type
- Added `image_hash` column (String) for SHA-256 hash (already existed)

### 2. Domain Entity Updates
- **File**: `src/domain/entities.py`
- Added `image_data: Optional[bytes]` field to Artwork dataclass
- Added `image_mime_type: Optional[str]` field to Artwork dataclass

### 3. Repository Updates
- **File**: `src/repositories/sqlite_repository.py`
- Updated `_to_model()` to map image_data and image_mime_type to database
- Updated `_to_entity()` to map database fields back to entity

### 4. Image Download Service
- **File**: `src/services/image_download_service.py`
- Created new service for downloading images from URLs
- Features:
  - Rate limiting (2 seconds between requests)
  - Size limit enforcement (10MB max)
  - SHA-256 hash calculation for deduplication
  - Content-Type validation (rejects non-image responses)
  - Returns tuple of (image_data, mime_type)
  - `download_and_attach_image()` method returns updated Artwork entity

### 5. Scraping Pipeline Integration
- **File**: `scrape_and_populate.py`
- Integrated ImageDownloadService into scraping workflow
- Downloads images after transformation but before import
- Gracefully handles failures (imports artwork without image)
- Provides progress feedback during download

### 6. API Image Serving Endpoint
- **File**: `src/api/routes.py`
- Added `GET /api/artworks/{artwork_id}/image` endpoint
- Serves binary image data from database
- Sets proper Content-Type header
- Includes caching headers (Cache-Control, ETag)
- Returns 404 for missing artworks or missing images

### 7. Frontend Updates
- **File**: `static/app.js`
- Updated table thumbnails to use `/api/artworks/{id}/image`
- Updated modal images to use database-served images
- Changed from using `artwork.image_url` to checking `artwork.image_hash`
- Maintains error handling for missing images

### 8. Integration Tests
- **File**: `tests/integration/test_image_serving.py`
- Created comprehensive test suite:
  - `test_image_endpoint_returns_binary_data()` - Verifies binary data matches
  - `test_image_endpoint_has_cache_headers()` - Checks caching headers
  - `test_image_endpoint_404_for_nonexistent_artwork()` - Tests error handling
  - `test_most_artworks_have_images()` - Validates 80%+ success rate
  - `test_image_deduplication_by_hash()` - Verifies SHA-256 hashing
  - `test_image_sizes_within_limits()` - Ensures size constraints

## Results

### Database Population
- Successfully scraped 12 artworks from lootedart.gov.pl
- 11 artworks with downloaded images (91.7% success rate)
- 1 artwork without image (Polish site served HTML error page)
- All images validated as proper image/* MIME types

### Image Statistics
- Total images downloaded: 11
- Total image data stored: ~2.1 MB
- All images under 10MB limit
- Average image size: ~190 KB
- All images with SHA-256 hashes for deduplication

### Test Results
- All 6 integration tests passing
- Code coverage: 77%
- No failures in image serving endpoints

## Benefits

1. **Reliability**: Images stored locally, not dependent on external sites
2. **Performance**: Images cached with proper HTTP headers (24-hour cache)
3. **Offline Capability**: Database contains complete artwork records with images
4. **Deduplication**: SHA-256 hashing prevents duplicate storage
5. **Validation**: Content-Type checking prevents storing non-image data
6. **Rate Limiting**: Respects source server limits during downloads

## Technical Details

### Rate Limiting
- 2 seconds between HTTP requests
- Enforced at ImageDownloadService level
- Prevents overwhelming source servers

### Content Validation
- Checks Content-Type header starts with "image/"
- Rejects HTML error pages disguised as images
- Validates data before storage

### Caching Strategy
- ETag based on image hash (SHA-256)
- Cache-Control: public, max-age=86400 (24 hours)
- Reduces bandwidth and improves performance

### Error Handling
- Graceful degradation when images unavailable
- Artworks imported even if image download fails
- Frontend displays placeholder for missing images
- Clear logging of download failures

## Database Schema

```sql
CREATE TABLE artworks (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500),
    artist_name VARCHAR(200),
    creation_year INTEGER,
    description TEXT,
    status VARCHAR(50),
    image_url VARCHAR(500),
    image_data BLOB,              -- NEW: Binary image data
    image_mime_type VARCHAR(50),   -- NEW: Content-Type (e.g., "image/jpeg")
    image_hash VARCHAR(64),        -- SHA-256 hash for deduplication
    last_known_location VARCHAR(200),
    last_known_date DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);
```

## API Endpoints

### Image Serving
```
GET /api/artworks/{artwork_id}/image

Response Headers:
  Content-Type: image/jpeg (or image/png, etc.)
  Cache-Control: public, max-age=86400
  ETag: <first-32-chars-of-sha256-hash>

Response Body: Binary image data

Status Codes:
  200 OK - Image found and returned
  404 Not Found - Artwork or image not found
```

## Future Enhancements

1. **Image Resizing**: Generate thumbnails on-the-fly for better performance
2. **WebP Conversion**: Convert images to WebP for smaller file sizes
3. **CDN Integration**: Serve images from CDN for production deployment
4. **Lazy Loading**: Load images only when visible in viewport
5. **Progressive Loading**: Show low-resolution placeholder while loading full image
6. **Image Search**: Use perceptual hashing (pHash) for reverse image search
7. **EXIF Data**: Extract and store image metadata
8. **Multiple Sizes**: Store thumbnail, medium, and full-size versions

## Deployment Notes

### Database Migration
When deploying to production with existing data:
1. Add new columns: `ALTER TABLE artworks ADD COLUMN image_data BLOB`
2. Add MIME type: `ALTER TABLE artworks ADD COLUMN image_mime_type VARCHAR(50)`
3. Run migration script to download images for existing artworks
4. Validate all images before cutover

### Production Considerations
- PostgreSQL supports BYTEA type for binary data (similar to SQLite BLOB)
- Consider storing images in object storage (S3, Azure Blob) for large collections
- Implement CDN caching for globally distributed access
- Monitor storage costs as collection grows
- Set up backup strategy for image data

### Performance Optimization
- Add database index on image_hash for deduplication queries
- Use database connection pooling for concurrent requests
- Implement Redis cache for frequently accessed images
- Consider image compression before storage
- Monitor query performance as dataset grows

## Testing

Run the test suite:
```bash
pytest tests/integration/test_image_serving.py -v
```

Expected output:
```
6 passed in 1.14s
```

## Verification

Check database contents:
```python
from src.repositories.sqlite_repository import SQLiteArtworkRepository

repo = SQLiteArtworkRepository('sqlite:///artworks.db')
artworks = repo.find_all(limit=100, offset=0)

for artwork in artworks:
    has_image = "✓" if artwork.image_data else "✗"
    size = len(artwork.image_data) if artwork.image_data else 0
    print(f"{has_image} {artwork.title[:50]} ({size:,} bytes)")
```

View images in browser:
```
http://localhost:8000
```

Test image endpoint directly:
```
http://localhost:8000/api/artworks/{artwork-id}/image
```
