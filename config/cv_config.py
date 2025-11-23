"""Computer vision pipeline configuration."""
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class PerceptualHashConfig:
    """Perceptual hashing configuration."""
    
    HASH_SIZE: Final[int] = 8  # 8x8 = 64-bit hash
    
    # Hamming distance thresholds (number of different bits)
    THRESHOLD_IDENTICAL: Final[int] = 5  # 0-5 bits: nearly identical
    THRESHOLD_VERY_SIMILAR: Final[int] = 10  # 6-10 bits: very similar
    THRESHOLD_SIMILAR: Final[int] = 15  # 11-15 bits: similar
    THRESHOLD_SOMEWHAT_SIMILAR: Final[int] = 20  # 16-20 bits: somewhat similar


@dataclass(frozen=True)
class CLIPConfig:
    """CLIP embedding configuration."""
    
    MODEL_NAME: Final[str] = "openai/clip-vit-base-patch32"
    EMBEDDING_DIM: Final[int] = 512
    BATCH_SIZE: Final[int] = 16
    DEVICE: Final[str] = "cpu"  # or "cuda" if GPU available
    
    # Cosine similarity thresholds
    THRESHOLD_HIGH: Final[float] = 0.90  # Very similar
    THRESHOLD_MEDIUM: Final[float] = 0.80  # Similar
    THRESHOLD_LOW: Final[float] = 0.70  # Somewhat similar


@dataclass(frozen=True)
class ImageProcessingConfig:
    """Image processing configuration."""
    
    MAX_IMAGE_SIZE_MB: Final[int] = 10
    SUPPORTED_FORMATS: Final[tuple[str, ...]] = ("jpg", "jpeg", "png", "tiff", "webp")
    
    # Quality thresholds
    MIN_SHARPNESS: Final[float] = 0.3
    MIN_CONTRAST: Final[float] = 0.2
    MIN_RESOLUTION: Final[int] = 200  # pixels (width or height)
    
    # Processing
    BATCH_SIZE: Final[int] = 10
    MAX_WORKERS: Final[int] = 4  # parallel threads


@dataclass(frozen=True)
class FeatureExtractionConfig:
    """Feature extraction pipeline configuration."""
    
    EXTRACT_HASHES: Final[bool] = True
    EXTRACT_EMBEDDINGS: Final[bool] = True
    EXTRACT_COLORS: Final[bool] = True
    NUM_DOMINANT_COLORS: Final[int] = 5
    
    MODEL_VERSION: Final[str] = "v1.0.0"
