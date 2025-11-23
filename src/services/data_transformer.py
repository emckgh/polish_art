"""ETL service to transform scraped data into domain entities."""
from datetime import datetime
from typing import Optional

from src.domain.entities import Artwork, Artist, ArtworkStatus


class ArtworkDataTransformer:
    """Transform raw scraped data into domain entities."""
    
    def transform_scraped_artwork(
        self, 
        raw_data: dict
    ) -> Optional[Artwork]:
        """Transform scraped data dict to Artwork entity."""
        title = raw_data.get("title", "").strip()
        
        if not title:
            return None
        
        description = raw_data.get("description", "")
        
        # Parse structured description from lootedart.gov.pl
        parsed_data = self._parse_structured_description(description)
        
        artist = self._extract_artist(parsed_data)
        creation_year = self._extract_year(parsed_data.get("date_of_creation", ""))
        clean_description = parsed_data.get("object_type", "")
        image_url = self._fix_image_url(raw_data.get("image_url"))
        
        return Artwork(
            title=title,
            artist=artist,
            creation_year=creation_year,
            description=clean_description,
            status=ArtworkStatus.KNOWN_LOOTED,
            image_url=image_url,
            last_known_location="Poland",
            last_known_date=datetime(1939, 9, 1)
        )
    
    def _parse_structured_description(self, description: str) -> dict:
        """Parse structured description from lootedart.gov.pl format.
        
        Example format:
        "After the Waters Have RecededCard number:36371Author / School / Workshop:Unknown German painter, 19th cent.Date of creation:4th. quarter of 19th cent.Object type:Painting"
        """
        result = {}
        
        # Extract fields using common patterns
        fields = {
            "card_number": ["Card number:", "Numer karty:"],
            "author": ["Author / School / Workshop:", "Autor / Szkoła / Pracownia:"],
            "date_of_creation": ["Date of creation:", "Data powstania:"],
            "object_type": ["Object type:", "Typ obiektu:"],
        }
        
        for key, patterns in fields.items():
            for pattern in patterns:
                if pattern in description:
                    # Find start of value
                    start = description.index(pattern) + len(pattern)
                    # Find end (next field or end of string)
                    remaining = description[start:]
                    
                    # Look for next field marker
                    end_pos = len(remaining)
                    for next_pattern in ["Card number:", "Author", "Date of creation:", "Object type:", "Numer karty:", "Autor", "Data powstania:", "Typ obiektu:"]:
                        pos = remaining.find(next_pattern)
                        if pos > 0 and pos < end_pos:
                            end_pos = pos
                    
                    value = remaining[:end_pos].strip()
                    result[key] = value
                    break
        
        return result
    
    def _extract_artist(
        self, 
        parsed_data: dict
    ) -> Optional[Artist]:
        """Extract artist from parsed data."""
        author_text = parsed_data.get("author", "").strip()
        
        # Skip if no author or invalid markers
        if not author_text or author_text.lower() in ["unknown", "nieznany", "", "date of creation:"]:
            return None
        
        # Skip if it's actually another field that leaked through
        if any(marker in author_text.lower() for marker in ["date of creation", "object type", "card number"]):
            return None
        
        # Clean up the artist name
        artist_name = author_text
        
        # Extract nationality if present (e.g., "German painter")
        nationality = None
        for nat in ["German", "Polish", "Italian", "French", "Dutch", "Spanish", "English", "Russian", "Austrian"]:
            if nat in artist_name:
                nationality = nat
                break
        
        return Artist(
            name=artist_name,
            nationality=nationality
        )
    
    def _extract_year(self, date_text: str) -> Optional[int]:
        """Extract year from date text.
        
        Examples:
        - "4th. quarter of 19th cent." -> 1875
        - "1820-1830" -> 1825
        - "ca. 1850" -> 1850
        """
        import re
        
        if not date_text:
            return None
        
        # Look for 4-digit years
        years = re.findall(r'\b(1[0-9]{3}|20[0-2][0-9])\b', date_text)
        if years:
            # If range, take middle
            if len(years) >= 2:
                return (int(years[0]) + int(years[1])) // 2
            return int(years[0])
        
        # Handle century notation (e.g., "19th cent.")
        century_match = re.search(r'(\d+)(?:th|st|nd|rd)\.?\s*(?:century|cent\.?)', date_text.lower())
        if century_match:
            century = int(century_match.group(1))
            year = (century - 1) * 100 + 50  # Middle of century
            
            # Adjust for quarter
            if "1st" in date_text or "first" in date_text.lower():
                year = (century - 1) * 100 + 12
            elif "2nd" in date_text or "second" in date_text.lower():
                year = (century - 1) * 100 + 37
            elif "3rd" in date_text or "third" in date_text.lower():
                year = (century - 1) * 100 + 62
            elif "4th" in date_text or "fourth" in date_text.lower():
                year = (century - 1) * 100 + 87
            
            return year
        
        return None
    
    def transform_batch(
        self, 
        raw_artworks: list[dict]
    ) -> list[Artwork]:
        """Transform batch of scraped artworks."""
        transformed = []
        
        for raw in raw_artworks:
            artwork = self.transform_scraped_artwork(raw)
            if artwork:
                transformed.append(artwork)
        
        return transformed
    
    def _fix_image_url(self, url: Optional[str]) -> Optional[str]:
        """Fix image URL to use Polish site instead of English site.
        
        The English site (lootedart.gov.pl) returns HTML for image endpoints,
        but the Polish site (dzielautracone.gov.pl) returns actual images.
        """
        if not url:
            return url
        
        # Replace English domain with Polish domain
        if 'lootedart.gov.pl' in url:
            url = url.replace('lootedart.gov.pl', 'dzielautracone.gov.pl')
        
        return url
