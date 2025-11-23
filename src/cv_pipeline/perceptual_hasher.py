"""Perceptual hashing for image similarity detection."""
import io
from typing import Optional

import imagehash
from PIL import Image

from config.cv_config import PerceptualHashConfig


class PerceptualHasher:
    """Compute perceptual hashes for images."""
    
    def __init__(self, hash_size: int = PerceptualHashConfig.HASH_SIZE):
        """Initialize with configurable hash size.
        
        Args:
            hash_size: Size of hash (default 8 = 64-bit hash)
        """
        self._hash_size = hash_size
    
    def compute_phash(self, image_bytes: bytes) -> str:
        """Compute perceptual hash (DCT-based).
        
        Best for: General similarity, rotation-invariant
        Algorithm:
        1. Resize to 32x32 grayscale
        2. Apply DCT (Discrete Cosine Transform)
        3. Extract low-frequency 8x8 block
        4. Compare to median → 64-bit hash
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Hexadecimal string representation of hash
        """
        img = Image.open(io.BytesIO(image_bytes))
        hash_obj = imagehash.phash(img, hash_size=self._hash_size)
        return str(hash_obj)
    
    def compute_dhash(self, image_bytes: bytes) -> str:
        """Compute difference hash (gradient-based).
        
        Best for: Detecting transformations
        Algorithm:
        1. Resize to 9x8 grayscale
        2. Compare adjacent pixels (horizontal)
        3. Generate 64-bit hash from comparisons
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Hexadecimal string representation of hash
        """
        img = Image.open(io.BytesIO(image_bytes))
        hash_obj = imagehash.dhash(img, hash_size=self._hash_size)
        return str(hash_obj)
    
    def compute_ahash(self, image_bytes: bytes) -> str:
        """Compute average hash (simplest).
        
        Best for: Fast exact/near duplicates
        Algorithm:
        1. Resize to 8x8 grayscale
        2. Compute average pixel value
        3. Compare each pixel to average
        4. Generate 64-bit hash
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Hexadecimal string representation of hash
        """
        img = Image.open(io.BytesIO(image_bytes))
        hash_obj = imagehash.average_hash(img, hash_size=self._hash_size)
        return str(hash_obj)
    
    def compute_all(
        self, 
        image_bytes: bytes
    ) -> dict[str, str]:
        """Compute all three hash types.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dictionary with keys 'phash', 'dhash', 'ahash'
        """
        img = Image.open(io.BytesIO(image_bytes))
        
        return {
            "phash": str(imagehash.phash(img, hash_size=self._hash_size)),
            "dhash": str(imagehash.dhash(img, hash_size=self._hash_size)),
            "ahash": str(imagehash.average_hash(img, hash_size=self._hash_size))
        }
    
    def hamming_distance(
        self, 
        hash1: str, 
        hash2: str
    ) -> int:
        """Calculate Hamming distance between two hashes.
        
        The Hamming distance is the number of differing bits.
        
        Args:
            hash1: First hash (hex string)
            hash2: Second hash (hex string)
            
        Returns:
            Number of differing bits (0-64 for 8x8 hash)
            
        Interpretation:
            - 0-5: Nearly identical
            - 6-10: Very similar
            - 11-15: Similar
            - 16-20: Somewhat similar
            - 21+: Different
        """
        # Convert hex strings back to imagehash objects for comparison
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return h1 - h2  # imagehash overloads subtraction for Hamming distance
    
    def is_similar(
        self,
        hash1: str,
        hash2: str,
        threshold: int = PerceptualHashConfig.THRESHOLD_SIMILAR
    ) -> bool:
        """Check if two hashes are similar within threshold.
        
        Args:
            hash1: First hash
            hash2: Second hash
            threshold: Maximum Hamming distance to consider similar
            
        Returns:
            True if hashes are similar
        """
        distance = self.hamming_distance(hash1, hash2)
        return distance <= threshold
    
    def get_similarity_level(
        self,
        hash1: str,
        hash2: str
    ) -> str:
        """Get human-readable similarity level.
        
        Args:
            hash1: First hash
            hash2: Second hash
            
        Returns:
            One of: "identical", "very_similar", "similar", 
                    "somewhat_similar", "different"
        """
        distance = self.hamming_distance(hash1, hash2)
        
        if distance <= PerceptualHashConfig.THRESHOLD_IDENTICAL:
            return "identical"
        elif distance <= PerceptualHashConfig.THRESHOLD_VERY_SIMILAR:
            return "very_similar"
        elif distance <= PerceptualHashConfig.THRESHOLD_SIMILAR:
            return "similar"
        elif distance <= PerceptualHashConfig.THRESHOLD_SOMEWHAT_SIMILAR:
            return "somewhat_similar"
        else:
            return "different"
