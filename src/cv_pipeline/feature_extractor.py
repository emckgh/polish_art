"""Feature extraction service coordinating all CV operations."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from uuid import UUID

from config.cv_config import FeatureExtractionConfig, ImageProcessingConfig
from src.cv_pipeline.clip_embedder import CLIPEmbedder
from src.cv_pipeline.image_analyzer import ImageAnalyzer
from src.cv_pipeline.perceptual_hasher import PerceptualHasher
from src.domain.entities import ImageFeatures
from src.infrastructure.errors import ScrapingError
from src.repositories.feature_repository import FeatureRepository
from src.repositories.interfaces import ArtworkRepository


class FeatureExtractionService:
    """Extract visual features from artwork images."""
    
    def __init__(
        self,
        artwork_repo: ArtworkRepository,
        feature_repo: FeatureRepository,
        hasher: Optional[PerceptualHasher] = None,
        embedder: Optional[CLIPEmbedder] = None,
        analyzer: Optional[ImageAnalyzer] = None
    ):
        """Initialize service with dependencies.
        
        Args:
            artwork_repo: Repository for artwork data
            feature_repo: Repository for feature storage
            hasher: Perceptual hash generator (optional)
            embedder: CLIP embedding generator (optional)
            analyzer: Image analyzer (optional)
        """
        self._artwork_repo = artwork_repo
        self._feature_repo = feature_repo
        self._hasher = hasher or PerceptualHasher()
        self._embedder = embedder or CLIPEmbedder()
        self._analyzer = analyzer or ImageAnalyzer()
    
    def extract_features(
        self, 
        artwork_id: UUID,
        force: bool = False
    ) -> ImageFeatures:
        """Extract all features from artwork image.
        
        Process:
        1. Load image data from repository
        2. Validate image (format, size, quality)
        3. Compute perceptual hashes
        4. Generate CLIP embedding
        5. Extract metadata & quality metrics
        6. Store features in repository
        
        Args:
            artwork_id: Artwork UUID
            force: Recompute even if features exist
            
        Returns:
            ImageFeatures with all computed data
            
        Raises:
            ValueError: If artwork has no image data
            ScrapingError: If feature extraction fails
        """
        # Check if features already exist
        if not force:
            existing = self._feature_repo.find_by_artwork_id(artwork_id)
            if existing:
                print(f"Features already exist for {artwork_id}, skipping")
                return existing
        
        # Load artwork
        artwork = self._artwork_repo.find_by_id(artwork_id)
        if not artwork:
            raise ValueError(f"Artwork not found: {artwork_id}")
        
        if not artwork.image_data:
            raise ValueError(
                f"Artwork {artwork_id} has no image data"
            )
        
        print(f"Extracting features for: {artwork.title[:50]}")
        
        try:
            # Extract all features
            features = ImageFeatures(artwork_id=artwork_id)
            
            # 1. Perceptual hashes
            if FeatureExtractionConfig.EXTRACT_HASHES:
                print("  Computing perceptual hashes...")
                hashes = self._hasher.compute_all(artwork.image_data)
                features.phash = hashes["phash"]
                features.dhash = hashes["dhash"]
                features.ahash = hashes["ahash"]
            
            # 2. CLIP embedding
            if FeatureExtractionConfig.EXTRACT_EMBEDDINGS:
                print("  Generating CLIP embedding...")
                features.clip_embedding = self._embedder.generate_embedding(
                    artwork.image_data
                )
            
            # 3. Image analysis
            print("  Analyzing image metadata and quality...")
            analysis = self._analyzer.extract_all(
                artwork.image_data,
                extract_colors=FeatureExtractionConfig.EXTRACT_COLORS,
                num_colors=FeatureExtractionConfig.NUM_DOMINANT_COLORS
            )
            
            # Map analysis results to features
            features.width_pixels = analysis["width"]
            features.height_pixels = analysis["height"]
            features.aspect_ratio = analysis["aspect_ratio"]
            features.format = analysis["format"]
            features.file_size_bytes = analysis["file_size"]
            features.color_space = analysis["mode"]
            features.is_grayscale = analysis["is_grayscale"]
            features.sharpness_score = analysis["sharpness_score"]
            features.contrast_score = analysis["contrast_score"]
            features.brightness_avg = analysis["brightness_avg"]
            features.dominant_colors = analysis["dominant_colors"]
            features.model_version = FeatureExtractionConfig.MODEL_VERSION
            
            # Store features
            print("  Saving features to database...")
            self._feature_repo.save(features)
            
            print(f"✓ Features extracted successfully for {artwork.title[:50]}")
            return features
            
        except Exception as e:
            raise ScrapingError(
                f"Failed to extract features for {artwork_id}: {e}"
            ) from e
    
    def extract_batch(
        self, 
        artwork_ids: list[UUID],
        batch_size: int = ImageProcessingConfig.BATCH_SIZE,
        parallel: bool = False,
        force: bool = False
    ) -> dict[UUID, Optional[ImageFeatures]]:
        """Extract features for multiple artworks.
        
        Args:
            artwork_ids: List of artwork UUIDs
            batch_size: Batch size for processing
            parallel: Use parallel processing
            force: Recompute even if features exist
            
        Returns:
            Dictionary mapping artwork_id to features (or None if failed)
        """
        print(f"\nExtracting features for {len(artwork_ids)} artworks...")
        print(f"Parallel: {parallel}, Force: {force}\n")
        
        results = {}
        
        if parallel:
            # Parallel processing with thread pool
            max_workers = ImageProcessingConfig.MAX_WORKERS
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_id = {
                    executor.submit(
                        self.extract_features, 
                        artwork_id,
                        force
                    ): artwork_id
                    for artwork_id in artwork_ids
                }
                
                # Collect results
                for future in as_completed(future_to_id):
                    artwork_id = future_to_id[future]
                    try:
                        features = future.result()
                        results[artwork_id] = features
                    except Exception as e:
                        print(f"✗ Failed for {artwork_id}: {e}")
                        results[artwork_id] = None
        else:
            # Sequential processing
            for artwork_id in artwork_ids:
                try:
                    features = self.extract_features(artwork_id, force)
                    results[artwork_id] = features
                except Exception as e:
                    print(f"✗ Failed for {artwork_id}: {e}")
                    results[artwork_id] = None
        
        # Summary
        successful = sum(1 for v in results.values() if v is not None)
        print(f"\n✓ Extraction complete: {successful}/{len(artwork_ids)} successful")
        
        return results
    
    def extract_all_artworks(
        self,
        limit: int = 1000,
        force: bool = False
    ) -> dict[UUID, Optional[ImageFeatures]]:
        """Extract features for all artworks in database.
        
        Args:
            limit: Maximum number of artworks to process
            force: Recompute even if features exist
            
        Returns:
            Dictionary mapping artwork_id to features
        """
        # Get all artworks
        artworks = self._artwork_repo.find_all(limit=limit, offset=0)
        artwork_ids = [a.id for a in artworks if a.image_data]
        
        print(f"Found {len(artwork_ids)} artworks with images")
        
        return self.extract_batch(
            artwork_ids,
            parallel=True,
            force=force
        )
