"""Constants for web scraping configuration."""
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class PolishMinistryScraperConfig:
    """Configuration for Polish Ministry looted art scraper."""
    
    BASE_URL: Final[str] = "http://lootedart.gov.pl"
    CATEGORY_URL_TEMPLATE: Final[str] = (
        "http://lootedart.gov.pl/en/product-war-losses/?ID={category_id}"
    )
    
    # Rate limiting (respect the server)
    REQUESTS_PER_MINUTE: Final[int] = 30
    DELAY_BETWEEN_REQUESTS_SECONDS: Final[float] = 2.0
    
    # Retry configuration
    MAX_RETRIES: Final[int] = 3
    RETRY_BACKOFF_SECONDS: Final[float] = 5.0
    
    # Timeout
    REQUEST_TIMEOUT_SECONDS: Final[int] = 30
    
    # User agent identification
    USER_AGENT: Final[str] = (
        "PolishArtEngine/1.0 (Cultural Heritage Research Bot; "
        "+https://github.com/yourproject) Python-Requests"
    )
    
    # Categories from the website
    CATEGORY_POLISH_PAINTING: Final[int] = 9
    CATEGORY_FOREIGN_PAINTING: Final[int] = 13
    CATEGORY_SCULPTURE: Final[int] = 8
    CATEGORY_GRAPHICS_DRAWING: Final[int] = 14
    CATEGORY_ARCHAEOLOGY: Final[int] = 15
    CATEGORY_WOODWORK_FURNITURE: Final[int] = 18
    CATEGORY_CERAMICS: Final[int] = 22
    CATEGORY_GLASS: Final[int] = 23
    CATEGORY_METALWORK_MILITARIA: Final[int] = 24
    CATEGORY_TEXTILES: Final[int] = 28
    CATEGORY_LIBRARY: Final[int] = 32
    CATEGORY_PAINTING_GENERAL: Final[int] = 33
    
    ALL_CATEGORIES: Final[tuple[int, ...]] = (
        CATEGORY_POLISH_PAINTING,
        CATEGORY_FOREIGN_PAINTING,
        CATEGORY_SCULPTURE,
        CATEGORY_GRAPHICS_DRAWING,
        CATEGORY_ARCHAEOLOGY,
        CATEGORY_WOODWORK_FURNITURE,
        CATEGORY_CERAMICS,
        CATEGORY_GLASS,
        CATEGORY_METALWORK_MILITARIA,
        CATEGORY_TEXTILES,
        CATEGORY_LIBRARY,
        CATEGORY_PAINTING_GENERAL
    )


@dataclass(frozen=True)
class RobotsTxtRules:
    """Robots.txt compliance for lootedart.gov.pl."""
    
    # Allowed paths (not in disallow list)
    ALLOWED_PATHS: Final[tuple[str, ...]] = (
        "/product-war-losses",
        "/en/product-war-losses",
        "/artworks-recovered",
        "/news"
    )
    
    # Disallowed paths from robots.txt
    DISALLOWED_PATHS: Final[tuple[str, ...]] = (
        "/administrator/",
        "/cache/",
        "/cli/",
        "/components/",
        "/images/",
        "/includes/",
        "/installation/",
        "/language/",
        "/libraries/",
        "/logs/",
        "/media/",
        "/modules/",
        "/plugins/",
        "/templates/",
        "/tmp/"
    )
