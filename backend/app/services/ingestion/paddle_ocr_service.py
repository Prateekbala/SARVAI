"""PaddleOCR service for advanced text extraction with layout parsing"""
import logging
from typing import Dict, Any, BinaryIO, Optional, List
from PIL import Image
import io
import numpy as np

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

try:
    from paddlelayout import PaddleLayoutModel
except ImportError:
    PaddleLayoutModel = None

logger = logging.getLogger(__name__)

class PaddleOCRService:
    
    def __init__(self, use_layout: bool = True, lang: str = 'en'):
        self.use_layout = use_layout
        self.lang = lang
        self._ocr = None
        self._layout_model = None
    
    @property
    def ocr(self):
        """Lazy load OCR model"""
        if self._ocr is None:
            if PaddleOCR is None:
                raise ImportError("PaddleOCR not installed. Install with: pip install paddleocr paddlepaddle")
            logger.info("Initializing PaddleOCR model...")
            self._ocr = PaddleOCR(use_angle_cls=True, lang=self.lang)
        return self._ocr
    
    @property
    def layout_model(self):
        """Lazy load layout model"""
        if self._layout_model is None and self.use_layout:
            if PaddleLayoutModel is None:
                logger.warning("PaddleLayout not available. Layout parsing will be skipped.")
                return None
            logger.info("Initializing PaddleLayout model...")
            try:
                self._layout_model = PaddleLayoutModel()
            except Exception as e:
                logger.warning(f"Failed to load PaddleLayout: {e}. Continuing without layout parsing.")
        return self._layout_model
    
    async def extract_text_with_layout(
        self,
        image_data: np.ndarray,
        return_layout: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text and layout from image using PaddleOCR
        
        Args:
            image_data: Image as numpy array (BGR format)
            return_layout: Whether to return layout information
            
        Returns:
            Dict with:
                - text: Extracted full text
                - paragraphs: List of paragraphs with positions
                - layout: Layout structure if available
                - confidence: Average confidence score
                - bboxes: Bounding boxes for each text element
        """
        try:
            # Run OCR
            result = self.ocr.ocr(image_data, cls=True)
            
            if not result or not result[0]:
                return {
                    "text": "",
                    "paragraphs": [],
                    "layout": {},
                    "confidence": 0.0,
                    "bboxes": []
                }
            
            # Extract text and bounding boxes
            texts = []
            confidences = []
            bboxes = []
            
            for line in result[0]:
                bbox, text_conf = line
                text, conf = text_conf
                texts.append(text)
                confidences.append(conf)
                
                # Convert bbox to dict
                bbox_dict = {
                    "points": [[float(p[0]), float(p[1])] for p in bbox],
                    "text": text,
                    "confidence": float(conf)
                }
                bboxes.append(bbox_dict)
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Get layout if available
            layout_data = {}
            if return_layout and self.layout_model:
                try:
                    layout_data = await self._extract_layout(image_data)
                except Exception as e:
                    logger.warning(f"Layout extraction failed: {e}")
            
            # Group into paragraphs based on spatial proximity
            paragraphs = self._group_text_into_paragraphs(bboxes)
            
            return {
                "text": full_text,
                "paragraphs": paragraphs,
                "layout": layout_data,
                "confidence": float(avg_confidence),
                "bboxes": bboxes
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            raise
    
    async def extract_from_pdf_page(
        self,
        pdf_page,
        page_num: int
    ) -> Dict[str, Any]:
        """
        Extract text and layout from PDF page
        
        Args:
            pdf_page: PyMuPDF page object
            page_num: Page number (1-indexed)
            
        Returns:
            Extraction result dict
        """
        try:
            # Render page to high-quality image
            matrix = pdf_page.get_matrix(1.5, 1.5)  # 1.5x scale for better OCR
            pix = pdf_page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convert to numpy array
            img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            
            # Convert RGB to BGR for OpenCV/PaddleOCR compatibility
            if pix.n == 3:
                img_data = img_data[:, :, ::-1]
            
            # Extract text and layout
            result = await self.extract_text_with_layout(img_data, return_layout=True)
            result["page_number"] = page_num
            result["image_size"] = {"height": pix.height, "width": pix.width}
            
            return result
            
        except Exception as e:
            logger.error(f"PDF page extraction failed for page {page_num}: {e}")
            return {
                "text": "",
                "paragraphs": [],
                "layout": {},
                "confidence": 0.0,
                "bboxes": [],
                "page_number": page_num,
                "error": str(e)
            }
    
    def _group_text_into_paragraphs(self, bboxes: List[Dict]) -> List[Dict]:
        """
        Group bounding boxes into paragraphs based on spatial proximity
        
        Args:
            bboxes: List of bbox dicts with points
            
        Returns:
            List of paragraph dicts with grouped text
        """
        if not bboxes:
            return []
        
        paragraphs = []
        current_paragraph = []
        
        for bbox in bboxes:
            if current_paragraph:
                # Check if bbox is close to previous (same line or next line)
                prev_y = current_paragraph[-1]["points"][0][1]
                curr_y = bbox["points"][0][1]
                
                # If Y coordinate differs significantly, start new paragraph
                if abs(curr_y - prev_y) > 20:  # 20 pixels threshold
                    if current_paragraph:
                        paragraphs.append({
                            "text": " ".join([b["text"] for b in current_paragraph]),
                            "confidence": sum([b["confidence"] for b in current_paragraph]) / len(current_paragraph),
                            "bboxes": current_paragraph
                        })
                    current_paragraph = [bbox]
                else:
                    current_paragraph.append(bbox)
            else:
                current_paragraph.append(bbox)
        
        # Add last paragraph
        if current_paragraph:
            paragraphs.append({
                "text": " ".join([b["text"] for b in current_paragraph]),
                "confidence": sum([b["confidence"] for b in current_paragraph]) / len(current_paragraph),
                "bboxes": current_paragraph
            })
        
        return paragraphs
    
    async def _extract_layout(self, image_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract layout structure from image
        
        Args:
            image_data: Image as numpy array
            
        Returns:
            Layout structure dict
        """
        if not self.layout_model:
            return {}
        
        try:
            # This is a placeholder - actual implementation depends on PaddleLayout API
            # In production, use PaddleLayout to detect document structure (tables, figures, etc.)
            layout_result = self.layout_model.predict(image_data)
            
            return {
                "detected": True,
                "elements": layout_result  # Structure varies by actual PaddleLayout output
            }
        except Exception as e:
            logger.warning(f"Layout extraction failed: {e}")
            return {"detected": False, "error": str(e)}


# Global instance
paddle_ocr_service = PaddleOCRService(use_layout=True)
