from PIL import Image
import io
import logging
from typing import Dict, Any, BinaryIO, Optional
from pathlib import Path
import open_clip
import torch
import easyocr
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Service for processing images: OCR + CLIP embeddings"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"ImageProcessor using device: {self.device}")
        
        # Initialize CLIP model
        self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
            'ViT-B-32',
            pretrained='laion2b_s34b_b79k'
        )
        self.clip_model = self.clip_model.to(self.device)
        self.clip_model.eval()
        
        # Initialize OCR (lazy loading)
        self._ocr_reader = None
    
    @property
    def ocr_reader(self):
        """Lazy load OCR reader"""
        if self._ocr_reader is None:
            logger.info("Initializing EasyOCR reader...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=self.device == 'cuda')
        return self._ocr_reader
    
    async def process_image(
        self,
        image_data: BinaryIO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process image: extract text via OCR and generate CLIP embedding
        
        Args:
            image_data: Binary image data
            metadata: Optional metadata
            
        Returns:
            Dict with:
                - ocr_text: Extracted text from image
                - clip_embedding: Image embedding vector
                - image_info: Image dimensions, format, etc.
                - metadata: Enhanced metadata
        """
        try:
            # Load image
            image_data.seek(0)
            image = Image.open(image_data)
            
            # Convert RGBA to RGB if needed
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Get image info
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode
            }
            
            # Extract text using OCR
            logger.info("Running OCR on image...")
            image_array = np.array(image)
            ocr_results = self.ocr_reader.readtext(image_array)
            ocr_text = " ".join([text for (_, text, _) in ocr_results])
            
            if not ocr_text.strip():
                ocr_text = "[No text detected in image]"
            
            logger.info(f"OCR extracted {len(ocr_text)} characters")
            
            # Generate CLIP embedding
            logger.info("Generating CLIP embedding...")
            clip_embedding = self._generate_clip_embedding(image)
            
            # Enhance metadata
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "image_info": image_info,
                "ocr_length": len(ocr_text),
                "has_text": bool(ocr_text.strip() != "[No text detected in image]")
            })
            
            return {
                "ocr_text": ocr_text,
                "clip_embedding": clip_embedding,
                "image_info": image_info,
                "metadata": enhanced_metadata
            }
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise Exception(f"Failed to process image: {str(e)}")
    
    def _generate_clip_embedding(self, image: Image.Image) -> list:
        """Generate CLIP embedding for image"""
        try:
            # Preprocess image
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensor)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to list
            embedding = image_features.cpu().numpy()[0].tolist()
            
            return embedding
            
        except Exception as e:
            logger.error(f"CLIP embedding generation failed: {e}")
            raise Exception(f"Failed to generate image embedding: {str(e)}")
    
    def validate_image(self, image_data: BinaryIO, max_size_mb: int = 10) -> bool:
        """
        Validate image file
        
        Args:
            image_data: Binary image data
            max_size_mb: Maximum file size in MB
            
        Returns:
            True if valid
        """
        try:
            # Check file size
            image_data.seek(0, 2)  # Seek to end
            file_size = image_data.tell()
            image_data.seek(0)  # Reset
            
            if file_size > max_size_mb * 1024 * 1024:
                raise ValueError(f"Image too large. Max size: {max_size_mb}MB")
            
            # Try to open with PIL
            image = Image.open(image_data)
            image.verify()
            image_data.seek(0)  # Reset after verify
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            raise ValueError(f"Invalid image file: {str(e)}")

# Global instance
image_processor = ImageProcessor()
