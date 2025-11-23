"""Image metadata and quality analysis."""
import io
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


class ImageAnalyzer:
    """Analyze image quality and extract metadata."""
    
    def extract_metadata(
        self, 
        image_bytes: bytes
    ) -> dict:
        """Extract basic image metadata.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dictionary with metadata fields
        """
        img = Image.open(io.BytesIO(image_bytes))
        
        return {
            "width": img.width,
            "height": img.height,
            "aspect_ratio": round(img.width / img.height, 3),
            "format": img.format.lower() if img.format else "unknown",
            "mode": img.mode,
            "file_size": len(image_bytes),
            "is_grayscale": img.mode in ("L", "LA", "1")
        }
    
    def analyze_quality(
        self,
        image_bytes: bytes
    ) -> dict[str, float]:
        """Compute image quality metrics.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dictionary with quality scores:
            - sharpness_score: 0.0-1.0
            - contrast_score: 0.0-1.0
            - brightness_avg: 0-255
        """
        # Load image with OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {
                "sharpness_score": 0.0,
                "contrast_score": 0.0,
                "brightness_avg": 0.0
            }
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        # Normalize to 0-1 (empirical max ~1000)
        sharpness_score = min(sharpness / 1000.0, 1.0)
        
        # Contrast (standard deviation of pixel values)
        contrast = gray.std()
        # Normalize to 0-1 (max std is ~128 for 8-bit images)
        contrast_score = min(contrast / 128.0, 1.0)
        
        # Brightness (mean pixel value)
        brightness = gray.mean()
        
        return {
            "sharpness_score": round(float(sharpness_score), 3),
            "contrast_score": round(float(contrast_score), 3),
            "brightness_avg": round(float(brightness), 1)
        }
    
    def extract_dominant_colors(
        self,
        image_bytes: bytes,
        num_colors: int = 5
    ) -> list[tuple[int, int, int]]:
        """Extract dominant RGB colors using k-means clustering.
        
        Args:
            image_bytes: Raw image data
            num_colors: Number of dominant colors to extract
            
        Returns:
            List of RGB tuples, sorted by frequency
        """
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize for faster processing (max 300px)
        max_size = 300
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to numpy array and reshape
        pixels = np.array(img)
        pixels = pixels.reshape(-1, 3)
        
        # Perform k-means clustering
        kmeans = KMeans(
            n_clusters=num_colors,
            random_state=42,
            n_init=10
        )
        kmeans.fit(pixels)
        
        # Get cluster centers (dominant colors)
        colors = kmeans.cluster_centers_.astype(int)
        
        # Count pixels in each cluster
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        
        # Sort by frequency
        sorted_indices = np.argsort(-counts)
        sorted_colors = colors[sorted_indices]
        
        # Convert to list of tuples
        return [
            (int(r), int(g), int(b)) 
            for r, g, b in sorted_colors
        ]
    
    def extract_all(
        self,
        image_bytes: bytes,
        extract_colors: bool = True,
        num_colors: int = 5
    ) -> dict:
        """Extract all metadata and quality metrics.
        
        Args:
            image_bytes: Raw image data
            extract_colors: Whether to extract dominant colors
            num_colors: Number of colors if extracting
            
        Returns:
            Combined dictionary of all extracted features
        """
        result = {}
        
        # Metadata
        result.update(self.extract_metadata(image_bytes))
        
        # Quality metrics
        result.update(self.analyze_quality(image_bytes))
        
        # Dominant colors (optional, slower)
        if extract_colors:
            result["dominant_colors"] = self.extract_dominant_colors(
                image_bytes, 
                num_colors
            )
        else:
            result["dominant_colors"] = None
        
        return result
