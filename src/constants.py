"""Application-wide constants following .cursorrules principles."""
from typing import Final


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
