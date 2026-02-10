"""Service for analyzing Vision API results and tracking usage."""
from typing import Tuple, List, Optional
from urllib.parse import urlparse
from uuid import UUID
from datetime import datetime
import time

from src.domain.vision_entities import (
    VisionAPIRequest,
    VisionAPIMatch,
    VisionAPIEntity,
    VisionAPIDomainStats
)
from src.repositories.vision_repository import VisionAPIRepository


class VisionAPITrackingService:
    """Service for tracking and analyzing Vision API usage."""
    
    # Domain categorization patterns
    AUCTION_PATTERNS = ['auction', 'christie', 'sotheby', 'bonhams', 'phillips', 'artnet', 'invaluable']
    MARKETPLACE_PATTERNS = ['ebay', 'etsy', 'amazon', 'allegro', 'olx', 'marketplace', 'shop', 'store']
    MUSEUM_PATTERNS = ['museum', 'muzeum', 'gallery', 'galeria', 'mnw', 'mnk', 'polona', 'archive', 'archiwum']
    SOCIAL_PATTERNS = ['facebook', 'instagram', 'pinterest', 'twitter', 'reddit', 'tumblr']
    ACADEMIC_PATTERNS = ['edu', 'jstor', 'academia', 'researchgate', 'scholar', 'university', 'uniwersytet']
    
    # Suspicious domain indicators
    SUSPICIOUS_INDICATORS = [
        'auction', 'marketplace', 'private-collection', 'estate-sale',
        'anonymous', 'untitled', 'provenance-unknown'
    ]
    
    def __init__(self, repository: VisionAPIRepository):
        """Initialize service with repository."""
        self.repository = repository
    
    def analyze_and_track_results(
        self,
        artwork_id: UUID,
        full_matches: List[dict],
        partial_matches: List[dict],
        visually_similar: List[dict],
        pages_with_image: List[dict],
        web_entities: List[dict],
        image_source: str = 'database',
        processing_time_ms: Optional[int] = None
    ) -> VisionAPIRequest:
        """
        Analyze Vision API results, determine if interesting, and save to database.
        
        Returns:
            VisionAPIRequest entity with analysis results
        """
        start_time = time.time()
        
        # Create request object
        request = VisionAPIRequest(
            artwork_id=artwork_id,
            image_source=image_source,
            total_full_matches=len(full_matches),
            total_partial_matches=len(partial_matches),
            total_similar_images=len(visually_similar),
            total_pages_with_image=len(pages_with_image),
            processing_time_ms=processing_time_ms
        )
        
        # Analyze all matches
        all_matches = []
        best_score = 0.0
        interest_score = 0
        
        # Create a map of image URLs to their page URLs
        image_to_page_map = {}
        for page in pages_with_image:
            page_url = page.get('url', '')
            page_title = page.get('page_title', '')
            
            # Map full matching images on this page
            for img_url in page.get('full_matching_images', []):
                if img_url not in image_to_page_map:
                    image_to_page_map[img_url] = []
                image_to_page_map[img_url].append({
                    'page_url': page_url,
                    'page_title': page_title,
                    'match_type': 'full'
                })
            
            # Map partial matching images on this page
            for img_url in page.get('partial_matching_images', []):
                if img_url not in image_to_page_map:
                    image_to_page_map[img_url] = []
                image_to_page_map[img_url].append({
                    'page_url': page_url,
                    'page_title': page_title,
                    'match_type': 'partial'
                })
        
        # Process full matches
        for match in full_matches:
            image_url = match.get('url', '')
            domain = self._extract_domain(image_url)
            category = self._categorize_domain(domain)
            
            # Get page info if available
            page_infos = image_to_page_map.get(image_url, [])
            page_info = page_infos[0] if page_infos else {}
            
            page_url = page_info.get('page_url')
            page_title = page_info.get('page_title')
            
            vision_match = VisionAPIMatch(
                match_type='full',
                image_url=image_url,
                page_url=page_url,
                page_title=page_title,
                confidence_score=match.get('score'),
                domain=domain,
                domain_category=category
            )
            all_matches.append(vision_match)
            
            # Update best score
            if match.get('score', 0) > best_score:
                best_score = match.get('score', 0)
            
            # Calculate interest score
            interest_score += self._calculate_match_interest(vision_match, 'full')
        
        # Process partial matches
        for match in partial_matches:
            image_url = match.get('url', '')
            domain = self._extract_domain(image_url)
            category = self._categorize_domain(domain)
            
            # Get page info if available
            page_infos = image_to_page_map.get(image_url, [])
            page_info = page_infos[0] if page_infos else {}
            
            page_url = page_info.get('page_url')
            page_title = page_info.get('page_title')
            
            vision_match = VisionAPIMatch(
                match_type='partial',
                image_url=image_url,
                page_url=page_url,
                page_title=page_title,
                confidence_score=match.get('score'),
                domain=domain,
                domain_category=category
            )
            all_matches.append(vision_match)
            
            if match.get('score', 0) > best_score:
                best_score = match.get('score', 0)
            
            interest_score += self._calculate_match_interest(vision_match, 'partial')
        
        # Process visually similar (store all)
        for match in visually_similar:
            domain = self._extract_domain(match.get('url', ''))
            category = self._categorize_domain(domain)
            
            vision_match = VisionAPIMatch(
                match_type='similar',
                image_url=match.get('url', ''),
                confidence_score=match.get('score'),
                domain=domain,
                domain_category=category
            )
            all_matches.append(vision_match)
            
            # Add interest score for commercial domains
            if category in ['auction', 'marketplace']:
                interest_score += self._calculate_match_interest(vision_match, 'similar')
        
        # Process pages with image (store all interesting ones)
        for page in pages_with_image:
            domain = self._extract_domain(page.get('url', ''))
            category = self._categorize_domain(domain)
            
            vision_match = VisionAPIMatch(
                match_type='page',
                image_url='',
                page_url=page.get('url', ''),
                page_title=page.get('page_title'),
                domain=domain,
                domain_category=category
            )
            all_matches.append(vision_match)
            
            # Add interest score for commercial/suspicious domains
            if category in ['auction', 'marketplace'] or self._is_suspicious_domain(domain):
                interest_score += 10
        
        # Process web entities (store all)
        entities = []
        for entity in web_entities:
            entities.append(VisionAPIEntity(
                entity_description=entity.get('description', ''),
                entity_score=entity.get('score')
            ))
        
        # Determine if results are interesting
        request.has_interesting_results = interest_score >= 15
        request.best_match_score = best_score
        
        # Only store matches/entities if interesting
        if request.has_interesting_results:
            request.matches = all_matches
            request.entities = entities
        
        # Save request to database
        self.repository.save_request(request)
        
        # Update domain statistics for interesting results
        if request.has_interesting_results:
            self._update_domain_stats(artwork_id, all_matches)
        
        return request
    
    def _calculate_match_interest(self, match: VisionAPIMatch, match_type: str) -> int:
        """Calculate interest score for a match."""
        score = 0
        
        # Base score by match type
        if match_type == 'full':
            score += 10
        elif match_type == 'partial':
            score += 5
        elif match_type == 'similar':
            score += 2
        
        # Domain category bonus
        if match.domain_category == 'auction':
            score += 20  # Very interesting
        elif match.domain_category == 'marketplace':
            score += 15  # Highly interesting
        elif match.domain_category == 'social':
            score += 5   # Moderately interesting
        elif match.domain_category == 'museum':
            score += 2   # Slightly interesting
        
        # Suspicious domain bonus
        if match.domain and self._is_suspicious_domain(match.domain):
            score += 10
        
        return score
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ''
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ''
    
    def _categorize_domain(self, domain: str) -> str:
        """Categorize a domain based on patterns."""
        if not domain:
            return 'other'
        
        domain_lower = domain.lower()
        
        # Check patterns in priority order
        if any(pattern in domain_lower for pattern in self.AUCTION_PATTERNS):
            return 'auction'
        elif any(pattern in domain_lower for pattern in self.MARKETPLACE_PATTERNS):
            return 'marketplace'
        elif any(pattern in domain_lower for pattern in self.MUSEUM_PATTERNS):
            return 'museum'
        elif any(pattern in domain_lower for pattern in self.SOCIAL_PATTERNS):
            return 'social'
        elif any(pattern in domain_lower for pattern in self.ACADEMIC_PATTERNS):
            return 'academic'
        
        return 'other'
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        """Check if domain has suspicious indicators."""
        if not domain:
            return False
        
        domain_lower = domain.lower()
        return any(indicator in domain_lower for indicator in self.SUSPICIOUS_INDICATORS)
    
    def _update_domain_stats(self, artwork_id: UUID, matches: List[VisionAPIMatch]):
        """Update aggregate domain statistics."""
        domain_counts = {}
        
        # Count appearances by domain
        for match in matches:
            if match.domain:
                if match.domain not in domain_counts:
                    domain_counts[match.domain] = {
                        'category': match.domain_category,
                        'count': 0,
                        'artworks': set()
                    }
                domain_counts[match.domain]['count'] += 1
                domain_counts[match.domain]['artworks'].add(str(artwork_id))
        
        # Update stats for each domain
        for domain, data in domain_counts.items():
            existing = self.repository.find_domain_stats(domain)
            
            if existing:
                # Update existing
                existing.total_appearances += data['count']
                existing.artworks_found = list(set(existing.artworks_found + list(data['artworks'])))
                existing.last_seen = datetime.utcnow()
                
                # Flag suspicious if auction/marketplace
                if data['category'] in ['auction', 'marketplace']:
                    existing.flagged_suspicious = True
                
                self.repository.save_domain_stats(existing)
            else:
                # Create new
                stats = VisionAPIDomainStats(
                    domain=domain,
                    category=data['category'],
                    total_appearances=data['count'],
                    artworks_found=list(data['artworks']),
                    flagged_suspicious=data['category'] in ['auction', 'marketplace']
                )
                self.repository.save_domain_stats(stats)
    
    def get_artwork_search_history(self, artwork_id: UUID, limit: int = 10) -> List[VisionAPIRequest]:
        """Get search history for an artwork."""
        return self.repository.find_requests_by_artwork(artwork_id, limit)

    def get_request_by_id(self, request_id: UUID) -> Optional[VisionAPIRequest]:
        """Get a single Vision API request with matches and entities."""
        return self.repository.find_request_by_id(request_id)

    def get_interesting_findings(self, limit: int = 100, offset: int = 0) -> List[VisionAPIRequest]:
        """Get all requests with interesting results."""
        return self.repository.find_interesting_requests(limit, offset)
    
    def get_total_api_cost(self) -> int:
        """Get total API cost units used."""
        return self.repository.get_total_api_cost()
    
    def get_suspicious_domains(self) -> List[VisionAPIDomainStats]:
        """Get all flagged suspicious domains."""
        return self.repository.find_all_domain_stats(suspicious_only=True)
    
    def get_domain_stats_by_category(self, category: str, limit: int = 50) -> List[VisionAPIDomainStats]:
        """Get domain statistics by category."""
        return self.repository.find_all_domain_stats(category=category, limit=limit)
