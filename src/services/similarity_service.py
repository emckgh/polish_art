"""Service for finding similar artworks using CV features."""
import json
from typing import Optional
from uuid import UUID

import numpy as np

from src.repositories.feature_repository import SQLiteFeatureRepository
from src.repositories.interfaces import ArtworkRepository


class SimilarityService:
    """Service for computing artwork similarity."""
    
    def __init__(
        self,
        feature_repository: SQLiteFeatureRepository,
        artwork_repository: ArtworkRepository
    ):
        """Initialize similarity service.
        
        Args:
            feature_repository: Repository for CV features
            artwork_repository: Repository for artwork metadata
        """
        self.feature_repo = feature_repository
        self.artwork_repo = artwork_repository
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hex hash strings.
        
        Args:
            hash1: First hash (hex string)
            hash2: Second hash (hex string)
            
        Returns:
            Number of differing bits
        """
        if not hash1 or not hash2:
            return 999  # Return large distance for missing hashes
        
        if len(hash1) != len(hash2):
            return 999
        
        # Convert hex to binary and count differing bits
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        xor = int1 ^ int2
        return bin(xor).count('1')
    
    def cosine_similarity(
        self, 
        embedding1: list[float], 
        embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1, higher is more similar)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute cosine similarity
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(similarity)
    
    def find_similar_by_hash(
        self,
        artwork_id: UUID,
        threshold: int = 10,
        limit: int = 10
    ) -> list[dict]:
        """Find similar artworks using perceptual hashes.
        
        Args:
            artwork_id: ID of source artwork
            threshold: Maximum Hamming distance (lower = more similar)
            limit: Maximum number of results
            
        Returns:
            List of similar artworks with similarity scores
        """
        # Get features for source artwork
        source_features = self.feature_repo.find_by_artwork_id(artwork_id)
        if not source_features or not source_features.phash:
            return []
        
        # Get all features
        all_features = self.feature_repo.find_all(limit=1000)
        
        # Calculate distances
        similarities = []
        for features in all_features:
            # Skip self
            if features.artwork_id == artwork_id:
                continue
            
            if not features.phash:
                continue
            
            # Calculate Hamming distance
            distance = self.hamming_distance(
                source_features.phash,
                features.phash
            )
            
            if distance <= threshold:
                # Get artwork metadata
                artwork = self.artwork_repo.find_by_id(
                    str(features.artwork_id)
                )
                
                if artwork:
                    similarities.append({
                        "artwork_id": str(features.artwork_id),
                        "title": artwork.title,
                        "artist": artwork.artist.name if artwork.artist else None,
                        "creation_year": artwork.creation_year,
                        "image_hash": artwork.image_hash,
                        "distance": distance,
                        "similarity_score": 1.0 - (distance / 64.0),  # Normalize to 0-1
                        "method": "perceptual_hash"
                    })
        
        # Sort by distance (lowest first) and limit
        similarities.sort(key=lambda x: x["distance"])
        return similarities[:limit]
    
    def find_similar_by_clip(
        self,
        artwork_id: UUID,
        threshold: float = 0.8,
        limit: int = 10
    ) -> list[dict]:
        """Find similar artworks using CLIP embeddings.
        
        Args:
            artwork_id: ID of source artwork
            threshold: Minimum cosine similarity (0-1, higher = more similar)
            limit: Maximum number of results
            
        Returns:
            List of similar artworks with similarity scores
        """
        # Get features for source artwork
        source_features = self.feature_repo.find_by_artwork_id(artwork_id)
        if not source_features or not source_features.clip_embedding:
            return []
        
        # Get all features
        all_features = self.feature_repo.find_all(limit=1000)
        
        # Calculate similarities
        similarities = []
        for features in all_features:
            # Skip self
            if features.artwork_id == artwork_id:
                continue
            
            if not features.clip_embedding:
                continue
            
            # Calculate cosine similarity
            similarity = self.cosine_similarity(
                source_features.clip_embedding,
                features.clip_embedding
            )
            
            if similarity >= threshold:
                # Get artwork metadata
                artwork = self.artwork_repo.find_by_id(
                    str(features.artwork_id)
                )
                
                if artwork:
                    similarities.append({
                        "artwork_id": str(features.artwork_id),
                        "title": artwork.title,
                        "artist": artwork.artist.name if artwork.artist else None,
                        "creation_year": artwork.creation_year,
                        "image_hash": artwork.image_hash,
                        "similarity_score": similarity,
                        "method": "clip_embedding"
                    })
        
        # Sort by similarity (highest first) and limit
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities[:limit]
    
    def find_similar_hybrid(
        self,
        artwork_id: UUID,
        hash_threshold: int = 15,
        clip_threshold: float = 0.75,
        limit: int = 10
    ) -> list[dict]:
        """Find similar artworks using both hash and CLIP methods.
        
        Combines results from both methods and deduplicates.
        
        Args:
            artwork_id: ID of source artwork
            hash_threshold: Maximum Hamming distance for hash matching
            clip_threshold: Minimum cosine similarity for CLIP matching
            limit: Maximum number of results
            
        Returns:
            List of similar artworks with combined scores
        """
        # Get both types of matches
        hash_matches = self.find_similar_by_hash(
            artwork_id,
            threshold=hash_threshold,
            limit=limit * 2  # Get more to allow for deduplication
        )
        
        clip_matches = self.find_similar_by_clip(
            artwork_id,
            threshold=clip_threshold,
            limit=limit * 2
        )
        
        # Combine and deduplicate
        combined = {}
        
        for match in hash_matches:
            aid = match["artwork_id"]
            combined[aid] = {
                **match,
                "hash_score": match["similarity_score"],
                "methods": ["perceptual_hash"]
            }
        
        for match in clip_matches:
            aid = match["artwork_id"]
            if aid in combined:
                # Already found by hash - add CLIP score
                combined[aid]["clip_score"] = match["similarity_score"]
                combined[aid]["methods"].append("clip_embedding")
                # Combined score (average)
                combined[aid]["similarity_score"] = (
                    combined[aid]["hash_score"] + match["similarity_score"]
                ) / 2
            else:
                # New match from CLIP
                combined[aid] = {
                    **match,
                    "clip_score": match["similarity_score"],
                    "methods": ["clip_embedding"]
                }
        
        # Convert to list and sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return results[:limit]
    
    def find_duplicates(
        self,
        threshold: int = 5
    ) -> list[dict]:
        """Find potential duplicate artworks using perceptual hashes.
        
        Args:
            threshold: Maximum Hamming distance to consider duplicates
            
        Returns:
            List of duplicate groups
        """
        all_features = self.feature_repo.find_all(limit=1000)
        
        # Filter features with valid phash
        valid_features = [
            f for f in all_features 
            if f.phash
        ]
        
        # Find duplicates
        duplicates = []
        checked = set()
        
        for i, features1 in enumerate(valid_features):
            if str(features1.artwork_id) in checked:
                continue
            
            group = []
            for features2 in valid_features[i+1:]:
                if str(features2.artwork_id) in checked:
                    continue
                
                distance = self.hamming_distance(
                    features1.phash,
                    features2.phash
                )
                
                if distance <= threshold:
                    if not group:
                        # Add first artwork to group
                        artwork1 = self.artwork_repo.find_by_id(
                            str(features1.artwork_id)
                        )
                        if artwork1:
                            group.append({
                                "artwork_id": str(features1.artwork_id),
                                "title": artwork1.title,
                                "artist": artwork1.artist.name if artwork1.artist else None,
                                "image_hash": artwork1.image_hash
                            })
                            checked.add(str(features1.artwork_id))
                    
                    # Add matching artwork
                    artwork2 = self.artwork_repo.find_by_id(
                        str(features2.artwork_id)
                    )
                    if artwork2:
                        group.append({
                            "artwork_id": str(features2.artwork_id),
                            "title": artwork2.title,
                            "artist": artwork2.artist.name if artwork2.artist else None,
                            "image_hash": artwork2.image_hash,
                            "distance": distance
                        })
                        checked.add(str(features2.artwork_id))
            
            if len(group) > 1:
                duplicates.append({
                    "group_size": len(group),
                    "artworks": group
                })
        
        return duplicates
