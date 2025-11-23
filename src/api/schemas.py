"""Pydantic schemas for API responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ArtistSchema(BaseModel):
    """Artist response schema."""
    
    name: str
    nationality: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ArtworkSchema(BaseModel):
    """Artwork response schema."""
    
    id: str
    title: str
    artist: Optional[ArtistSchema] = None
    creation_year: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_hash: Optional[str] = None
    status: str
    last_known_location: Optional[str] = None
    last_known_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ArtworkListSchema(BaseModel):
    """Paginated artwork list response."""
    
    items: list[ArtworkSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchQuerySchema(BaseModel):
    """Search query parameters."""
    
    query: str
    page: int = 1
    page_size: int = 20
