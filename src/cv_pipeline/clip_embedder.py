"""CLIP embeddings for semantic image similarity."""
import io
from typing import Optional

import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

from config.cv_config import CLIPConfig


class CLIPEmbedder:
    """Generate CLIP embeddings for semantic similarity."""
    
    def __init__(
        self,
        model_name: str = CLIPConfig.MODEL_NAME,
        device: Optional[str] = None
    ):
        """Load CLIP model and processor.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to run on ("cpu", "cuda", or None for auto)
        """
        self._model_name = model_name
        self._device = device or CLIPConfig.DEVICE
        
        # Check if CUDA is available
        if self._device == "cuda" and not torch.cuda.is_available():
            print("CUDA not available, falling back to CPU")
            self._device = "cpu"
        
        print(f"Loading CLIP model: {model_name} on {self._device}")
        self._processor = CLIPProcessor.from_pretrained(model_name)
        self._model = CLIPModel.from_pretrained(model_name)
        self._model.to(self._device)
        self._model.eval()  # Set to evaluation mode
        print("CLIP model loaded successfully")
    
    def generate_embedding(
        self, 
        image_bytes: bytes
    ) -> list[float]:
        """Generate 512-dimensional embedding vector.
        
        Process:
        1. Load image from bytes
        2. Preprocess (resize, normalize)
        3. Pass through CLIP vision encoder
        4. Extract feature vector
        5. Normalize to unit length
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            512-dimensional embedding vector
        """
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Preprocess
        inputs = self._processor(
            images=img,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        
        # Generate embedding
        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
        
        # Normalize to unit length
        image_features = image_features / image_features.norm(
            dim=-1, 
            keepdim=True
        )
        
        # Convert to list
        embedding = image_features.cpu().numpy().flatten().tolist()
        
        return embedding
    
    def generate_batch(
        self,
        image_bytes_list: list[bytes],
        batch_size: int = CLIPConfig.BATCH_SIZE
    ) -> list[list[float]]:
        """Generate embeddings for multiple images.
        
        More efficient than single-image processing.
        
        Args:
            image_bytes_list: List of raw image data
            batch_size: Number of images to process at once
            
        Returns:
            List of 512-dimensional embedding vectors
        """
        embeddings = []
        
        # Process in batches
        for i in range(0, len(image_bytes_list), batch_size):
            batch = image_bytes_list[i:i + batch_size]
            
            # Load images
            images = []
            for img_bytes in batch:
                img = Image.open(io.BytesIO(img_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)
            
            # Preprocess batch
            inputs = self._processor(
                images=images,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                image_features = self._model.get_image_features(**inputs)
            
            # Normalize
            image_features = image_features / image_features.norm(
                dim=-1,
                keepdim=True
            )
            
            # Convert to lists
            batch_embeddings = image_features.cpu().numpy().tolist()
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def cosine_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity between embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score 0.0-1.0
            - 1.0: Identical
            - 0.9-1.0: Very similar
            - 0.8-0.9: Similar
            - 0.7-0.8: Somewhat similar
            - <0.7: Different
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        # Since vectors are already normalized, this is just dot product
        similarity = np.dot(vec1, vec2)
        
        # Ensure in valid range [0, 1]
        similarity = float(np.clip(similarity, 0.0, 1.0))
        
        return similarity
    
    def get_similarity_level(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> str:
        """Get human-readable similarity level.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            One of: "high", "medium", "low", "none"
        """
        similarity = self.cosine_similarity(embedding1, embedding2)
        
        if similarity >= CLIPConfig.THRESHOLD_HIGH:
            return "high"
        elif similarity >= CLIPConfig.THRESHOLD_MEDIUM:
            return "medium"
        elif similarity >= CLIPConfig.THRESHOLD_LOW:
            return "low"
        else:
            return "none"
