"""CLI tool to extract visual features from artwork images."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cv_pipeline.feature_extractor import FeatureExtractionService
from src.repositories.sqlite_repository import SQLiteArtworkRepository
from src.repositories.feature_repository import SQLiteFeatureRepository


def main():
    """Extract features from all artworks in database."""
    print("=" * 60)
    print("Artwork Feature Extraction Tool")
    print("=" * 60)
    
    # Initialize repositories
    print("\nInitializing repositories...")
    artwork_repo = SQLiteArtworkRepository("sqlite:///artworks.db")
    feature_repo = SQLiteFeatureRepository("sqlite:///artworks.db")
    
    # Create extraction service
    print("Loading CV models (this may take a moment)...")
    service = FeatureExtractionService(
        artwork_repo=artwork_repo,
        feature_repo=feature_repo
    )
    
    # Extract features for all artworks
    print("\nStarting feature extraction...\n")
    results = service.extract_all_artworks(force=False)
    
    # Display summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    
    successful = [aid for aid, feat in results.items() if feat is not None]
    failed = [aid for aid, feat in results.items() if feat is None]
    
    print(f"\nTotal artworks processed: {len(results)}")
    print(f"✓ Successful: {len(successful)}")
    print(f"✗ Failed: {len(failed)}")
    
    if successful:
        print("\nSuccessfully extracted features:")
        for artwork_id in successful:
            artwork = artwork_repo.find_by_id(artwork_id)
            if artwork:
                print(f"  - {artwork.title[:50]}")
    
    if failed:
        print("\nFailed extractions:")
        for artwork_id in failed:
            artwork = artwork_repo.find_by_id(artwork_id)
            if artwork:
                print(f"  - {artwork.title[:50]}")
    
    # Display sample features
    if successful:
        print("\n" + "=" * 60)
        print("SAMPLE FEATURES")
        print("=" * 60)
        
        first_id = successful[0]
        features = feature_repo.find_by_artwork_id(first_id)
        artwork = artwork_repo.find_by_id(first_id)
        
        if features and artwork:
            print(f"\nArtwork: {artwork.title}")
            print(f"\nPerceptual Hashes:")
            print(f"  pHash: {features.phash}")
            print(f"  dHash: {features.dhash}")
            print(f"  aHash: {features.ahash}")
            print(f"\nImage Properties:")
            print(f"  Dimensions: {features.width_pixels}x{features.height_pixels}")
            print(f"  Aspect Ratio: {features.aspect_ratio:.2f}")
            print(f"  Format: {features.format}")
            print(f"  File Size: {features.file_size_bytes:,} bytes")
            print(f"  Grayscale: {features.is_grayscale}")
            print(f"\nQuality Metrics:")
            print(f"  Sharpness: {features.sharpness_score:.3f}")
            print(f"  Contrast: {features.contrast_score:.3f}")
            print(f"  Brightness: {features.brightness_avg:.1f}")
            
            if features.clip_embedding:
                print(f"\nCLIP Embedding:")
                print(f"  Dimension: {len(features.clip_embedding)}")
                print(f"  First 5 values: {features.clip_embedding[:5]}")
            
            if features.dominant_colors:
                print(f"\nDominant Colors (RGB):")
                for i, (r, g, b) in enumerate(features.dominant_colors, 1):
                    print(f"  {i}. ({r:3d}, {g:3d}, {b:3d})")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
