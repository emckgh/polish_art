"""Custom exceptions for the application."""


class PolishArtError(Exception):
    """Base exception for the application."""
    pass


class RepositoryError(PolishArtError):
    """Error accessing the repository."""
    pass


class ValidationError(PolishArtError):
    """Data validation error."""
    pass


class ScrapingError(PolishArtError):
    """Error during web scraping."""
    pass


class TransformationError(PolishArtError):
    """Error during data transformation."""
    pass


class ImportError(PolishArtError):
    """Error during data import."""
    pass
