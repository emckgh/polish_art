"""Value objects for domain layer."""
from dataclasses import dataclass
from typing import Final


# Constants defined here to avoid circular imports
HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.90
LOW_CONFIDENCE_THRESHOLD: Final[float] = 0.60


@dataclass(frozen=True)
class SimilarityScore:
    """Value object representing similarity between artworks."""
    
    value: float
    
    def __post_init__(self) -> None:
        """Validate similarity score."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                f"Score must be 0.0-1.0, got {self.value}"
            )
    
    def is_high_confidence(self) -> bool:
        """Check if score indicates high confidence match."""
        return self.value >= HIGH_CONFIDENCE_THRESHOLD
    
    def is_low_confidence(self) -> bool:
        """Check if score indicates low confidence match."""
        return self.value < LOW_CONFIDENCE_THRESHOLD
    
    def meets_threshold(self, threshold: float) -> bool:
        """Check if score meets given threshold."""
        return self.value >= threshold


@dataclass(frozen=True)
class DateRange:
    """Value object representing a date range."""
    
    start_year: int
    end_year: int
    
    def __post_init__(self) -> None:
        """Validate date range."""
        min_year: Final[int] = 1000
        max_year: Final[int] = 3000
        
        if self.start_year < min_year or self.start_year > max_year:
            raise ValueError(f"Invalid start year: {self.start_year}")
        
        if self.end_year < min_year or self.end_year > max_year:
            raise ValueError(f"Invalid end year: {self.end_year}")
        
        if self.start_year > self.end_year:
            raise ValueError("Start year must be <= end year")
    
    def contains_year(self, year: int) -> bool:
        """Check if year falls within range."""
        return self.start_year <= year <= self.end_year
