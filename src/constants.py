"""Application-wide constants following .cursorrules principles."""
import os
from typing import Final


def get_database_url() -> str:
    """Database URL from env (DATABASE_URL, READ_ONLY); used for VPS read-only deployment."""
    url = os.environ.get("DATABASE_URL", "").strip() or DatabaseConstants.DEFAULT_DB_PATH
    read_only = os.environ.get("READ_ONLY", "").strip().lower() in ("1", "true", "yes")
    if read_only and url.startswith("sqlite"):
        sep = "&" if "?" in url else "?"
        url = url.rstrip("/") + sep + "mode=ro"
    return url


class HttpConstants:
    """HTTP-related constants."""
    STATUS_OK: Final[int] = 200
    STATUS_NOT_FOUND: Final[int] = 404
    
    # Cache durations in seconds
    CACHE_DURATION_ONE_DAY: Final[int] = 86400


class ImageDownloadConstants:
    """Image download configuration."""
    DEFAULT_DELAY_SECONDS: Final[float] = 2.0
    DEFAULT_TIMEOUT_SECONDS: Final[int] = 30
    DEFAULT_MAX_SIZE_MB: Final[int] = 10
    DOWNLOAD_CHUNK_SIZE_BYTES: Final[int] = 8192
    BYTES_PER_MB: Final[int] = 1024 * 1024
    
    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )


class PaginationConstants:
    """Pagination defaults and limits."""
    DEFAULT_PAGE: Final[int] = 1
    DEFAULT_PAGE_SIZE: Final[int] = 10
    MAX_PAGE_SIZE: Final[int] = 100
    MIN_SEARCH_QUERY_LENGTH: Final[int] = 1
    
    # For counting total records (should be refactored to use COUNT query)
    MAX_RECORDS_FOR_COUNT: Final[int] = 10000


class ReportFormattingConstants:
    """Report formatting characters."""
    SEPARATOR_DOUBLE: Final[str] = "=" * 60
    SEPARATOR_SINGLE: Final[str] = "-" * 60
    PERCENTAGE_MULTIPLIER: Final[int] = 100


class SearchConstants:
    """Search and matching constants."""
    # Multiplier for initial fetch to improve search results
    SEARCH_FETCH_MULTIPLIER: Final[int] = 2
    DEFAULT_SEARCH_LIMIT: Final[int] = 50


class CacheConstants:
    """Caching and response headers."""
    ETAG_HASH_LENGTH: Final[int] = 32


class SimilarityConstants:
    """Constants for similarity calculations."""
    
    # Hash-based similarity thresholds
    DEFAULT_HASH_THRESHOLD: Final[float] = 0.85
    DUPLICATE_DETECTION_THRESHOLD: Final[float] = 0.90
    
    # CLIP embedding similarity thresholds
    DEFAULT_CLIP_THRESHOLD: Final[float] = 0.75
    HIGH_SIMILARITY_THRESHOLD: Final[float] = 0.90
    
    # Feature comparison limits
    MAX_FEATURES_FOR_COMPARISON: Final[int] = 1000
    
    # Invalid distance marker
    INVALID_DISTANCE: Final[int] = 999
    
    # Duplicate detection multiplier
    DEDUP_FETCH_MULTIPLIER: Final[int] = 2


class HashConstants:
    """Constants for hash operations."""
    PHASH_BIT_LENGTH: Final[float] = 64.0


class VisionAPIConstants:
    """Constants for Google Vision API operations."""
    
    # API limits and defaults
    DEFAULT_MAX_RESULTS: Final[int] = 10
    MAX_RESULTS_PER_REQUEST: Final[int] = 20
    
    # Pricing
    COST_PER_1000_REQUESTS: Final[float] = 1.50
    
    # Image requirements
    MIN_WIDTH_PIXELS: Final[int] = 640


class VisionInterestScoreConstants:
    """Constants for Vision API interest scoring."""
    
    # Domain-based scoring
    DOMAIN_MUSEUM_SCORE: Final[int] = 10
    DOMAIN_AUCTION_SCORE: Final[int] = 5
    DOMAIN_GALLERY_SCORE: Final[int] = 2
    
    # Title keyword scoring
    TITLE_KEYWORD_ARTWORK_SCORE: Final[int] = 20
    TITLE_KEYWORD_ARTIST_SCORE: Final[int] = 15
    TITLE_KEYWORD_PAINTING_SCORE: Final[int] = 5
    TITLE_KEYWORD_SCULPTURE_SCORE: Final[int] = 2
    TITLE_KEYWORD_ARCHIVE_SCORE: Final[int] = 10
    
    # Interest threshold
    INTERESTING_THRESHOLD: Final[int] = 10


class DatabaseConstants:
    """Constants for database operations."""
    
    # Connection strings
    DEFAULT_DB_PATH: Final[str] = "sqlite:///data/artworks.db"
    
    # Column lengths
    TITLE_MAX_LENGTH: Final[int] = 500
    DESCRIPTION_MAX_LENGTH: Final[int] = 1000
    URL_MAX_LENGTH: Final[int] = 500
    NAME_MAX_LENGTH: Final[int] = 200
    SHORT_TEXT_LENGTH: Final[int] = 100
    TINY_TEXT_LENGTH: Final[int] = 50
    
    # Query limits
    DEFAULT_QUERY_LIMIT: Final[int] = 20
    MAX_QUERY_RESULTS: Final[int] = 100


class UUIDConstants:
    """Constants for UUID operations."""
    
    UUID_LENGTH_WITHOUT_HYPHENS: Final[int] = 32
    UUID_LENGTH_WITH_HYPHENS: Final[int] = 36
    
    # UUID format indices for inserting hyphens
    HYPHEN_POSITION_1: Final[int] = 8
    HYPHEN_POSITION_2: Final[int] = 12
    HYPHEN_POSITION_3: Final[int] = 16
    HYPHEN_POSITION_4: Final[int] = 20


class TimeConstants:
    """Time conversion constants."""
    MS_PER_SECOND: Final[int] = 1000
    SECONDS_PER_MINUTE: Final[int] = 60
    MINUTES_PER_HOUR: Final[int] = 60


class CurrencyConstants:
    """Currency conversion constants."""
    CENTS_PER_DOLLAR: Final[int] = 100


class CompressionConstants:
    """Compression related constants."""
    MAX_COMPRESSION_LEVEL: Final[int] = 9
    DEFAULT_COMPRESSION_LEVEL: Final[int] = 6
