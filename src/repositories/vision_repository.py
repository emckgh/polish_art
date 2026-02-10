"""Repository for Google Vision API tracking data."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import Session, sessionmaker

from src.repositories.models import (
    Base,
    VisionAPIRequestModel,
    VisionAPIMatchModel,
    VisionAPIEntityModel,
    VisionAPIDomainStatsModel
)
from src.domain.vision_entities import (
    VisionAPIRequest,
    VisionAPIMatch,
    VisionAPIEntity,
    VisionAPIDomainStats
)


class VisionAPIRepository:
    """SQLite repository for Vision API tracking."""
    
    def __init__(self, connection_string: str):
        """Initialize repository with database connection."""
        self._engine = create_engine(connection_string)
        if "mode=ro" not in connection_string:
            Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)
    
    def save_request(self, request: VisionAPIRequest) -> VisionAPIRequest:
        """Save a Vision API request with all matches and entities."""
        session: Session = self._session_factory()
        try:
            # Convert to model
            request_model = VisionAPIRequestModel(
                id=request.id,
                artwork_id=request.artwork_id,
                request_timestamp=request.request_timestamp,
                image_source=request.image_source,
                api_cost_units=request.api_cost_units,
                total_full_matches=request.total_full_matches,
                total_partial_matches=request.total_partial_matches,
                total_similar_images=request.total_similar_images,
                total_pages_with_image=request.total_pages_with_image,
                best_match_score=request.best_match_score,
                has_interesting_results=request.has_interesting_results,
                processing_time_ms=request.processing_time_ms
            )
            
            # Add matches (only if interesting results)
            if request.has_interesting_results:
                for match in request.matches:
                    match_model = VisionAPIMatchModel(
                        request_id=request.id,
                        match_type=match.match_type,
                        image_url=match.image_url,
                        confidence_score=match.confidence_score,
                        page_url=match.page_url,
                        page_title=match.page_title,
                        domain=match.domain,
                        domain_category=match.domain_category
                    )
                    request_model.matches.append(match_model)
                
                # Add entities
                for entity in request.entities:
                    entity_model = VisionAPIEntityModel(
                        request_id=request.id,
                        entity_description=entity.entity_description,
                        entity_score=entity.entity_score
                    )
                    request_model.entities.append(entity_model)
            
            session.add(request_model)
            session.commit()
            
            return request
        finally:
            session.close()
    
    def find_request_by_id(self, request_id: UUID) -> Optional[VisionAPIRequest]:
        """Find a request by ID. Tries primary-key get first, then filter by string for SQLite UUID compatibility."""
        session: Session = self._session_factory()
        try:
            model = session.get(VisionAPIRequestModel, request_id)
            if model:
                return self._request_to_entity(model)
            # SQLite may store UUID as string; try string comparison
            model = session.query(VisionAPIRequestModel).filter(
                VisionAPIRequestModel.id == str(request_id)
            ).first()
            if model:
                return self._request_to_entity(model)
            return None
        finally:
            session.close()
    
    def find_requests_by_artwork(
        self,
        artwork_id: UUID,
        limit: int = 10
    ) -> List[VisionAPIRequest]:
        """Find all requests for a specific artwork."""
        session: Session = self._session_factory()
        try:
            models = session.query(VisionAPIRequestModel)\
                .filter_by(artwork_id=artwork_id)\
                .order_by(desc(VisionAPIRequestModel.request_timestamp))\
                .limit(limit)\
                .all()
            
            return [self._request_to_entity(m) for m in models]
        finally:
            session.close()
    
    def find_interesting_requests(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[VisionAPIRequest]:
        """Find all requests with interesting results."""
        session: Session = self._session_factory()
        try:
            models = session.query(VisionAPIRequestModel)\
                .filter_by(has_interesting_results=True)\
                .order_by(desc(VisionAPIRequestModel.request_timestamp))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return [self._request_to_entity(m) for m in models]
        finally:
            session.close()
    
    def get_total_api_cost(self) -> int:
        """Get total API cost units used."""
        session: Session = self._session_factory()
        try:
            result = session.query(func.sum(VisionAPIRequestModel.api_cost_units)).scalar()
            return result or 0
        finally:
            session.close()
    
    def save_domain_stats(self, stats: VisionAPIDomainStats) -> VisionAPIDomainStats:
        """Save or update domain statistics."""
        session: Session = self._session_factory()
        try:
            existing = session.query(VisionAPIDomainStatsModel).filter_by(domain=stats.domain).first()
            
            if existing:
                # Update existing
                existing.total_appearances = stats.total_appearances
                existing.artworks_found = json.dumps(stats.artworks_found)
                existing.last_seen = stats.last_seen
                existing.flagged_suspicious = stats.flagged_suspicious
                if stats.category:
                    existing.category = stats.category
            else:
                # Create new
                model = VisionAPIDomainStatsModel(
                    domain=stats.domain,
                    category=stats.category,
                    total_appearances=stats.total_appearances,
                    artworks_found=json.dumps(stats.artworks_found),
                    first_seen=stats.first_seen,
                    last_seen=stats.last_seen,
                    flagged_suspicious=stats.flagged_suspicious
                )
                session.add(model)
            
            session.commit()
            return stats
        finally:
            session.close()
    
    def find_domain_stats(self, domain: str) -> Optional[VisionAPIDomainStats]:
        """Find statistics for a specific domain."""
        session: Session = self._session_factory()
        try:
            model = session.query(VisionAPIDomainStatsModel).filter_by(domain=domain).first()
            if not model:
                return None
            
            return VisionAPIDomainStats(
                domain=model.domain,
                category=model.category,
                total_appearances=model.total_appearances,
                artworks_found=json.loads(model.artworks_found) if model.artworks_found else [],
                first_seen=model.first_seen,
                last_seen=model.last_seen,
                flagged_suspicious=model.flagged_suspicious
            )
        finally:
            session.close()
    
    def find_all_domain_stats(
        self,
        category: Optional[str] = None,
        suspicious_only: bool = False,
        limit: int = 100
    ) -> List[VisionAPIDomainStats]:
        """Find all domain statistics with optional filters."""
        session: Session = self._session_factory()
        try:
            query = session.query(VisionAPIDomainStatsModel)
            
            if category:
                query = query.filter_by(category=category)
            
            if suspicious_only:
                query = query.filter_by(flagged_suspicious=True)
            
            models = query.order_by(desc(VisionAPIDomainStatsModel.total_appearances))\
                .limit(limit)\
                .all()
            
            return [
                VisionAPIDomainStats(
                    domain=m.domain,
                    category=m.category,
                    total_appearances=m.total_appearances,
                    artworks_found=json.loads(m.artworks_found) if m.artworks_found else [],
                    first_seen=m.first_seen,
                    last_seen=m.last_seen,
                    flagged_suspicious=m.flagged_suspicious
                )
                for m in models
            ]
        finally:
            session.close()
    
    def _request_to_entity(self, model: VisionAPIRequestModel) -> VisionAPIRequest:
        """Convert database model to domain entity."""
        matches = [
            VisionAPIMatch(
                match_type=m.match_type,
                image_url=m.image_url,
                confidence_score=m.confidence_score,
                page_url=m.page_url,
                page_title=m.page_title,
                domain=m.domain,
                domain_category=m.domain_category
            )
            for m in model.matches
        ]
        
        entities = [
            VisionAPIEntity(
                entity_description=e.entity_description,
                entity_score=e.entity_score
            )
            for e in model.entities
        ]
        
        return VisionAPIRequest(
            id=model.id,
            artwork_id=model.artwork_id,
            request_timestamp=model.request_timestamp,
            image_source=model.image_source,
            api_cost_units=model.api_cost_units,
            total_full_matches=model.total_full_matches,
            total_partial_matches=model.total_partial_matches,
            total_similar_images=model.total_similar_images,
            total_pages_with_image=model.total_pages_with_image,
            best_match_score=model.best_match_score,
            has_interesting_results=model.has_interesting_results,
            processing_time_ms=model.processing_time_ms,
            matches=matches,
            entities=entities
        )
