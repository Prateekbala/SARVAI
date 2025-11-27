import fitz  # PyMuPDF
from PIL import Image
import io
import logging
from typing import Dict, Any, BinaryIO, List, Optional
import easyocr
import numpy as np

from app.config import settings
from app.services.ingestion.text_processor import text_processor
from app.services.ingestion.paddle_ocr_service import paddle_ocr_service

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Service for processing PDF files: text extraction + OCR with layout parsing"""
    
    def __init__(self, use_paddle_ocr: bool = True):
        # Lazy load OCR readers
        self._easyocr_reader = None
        self.use_paddle_ocr = use_paddle_ocr
    
    @property
    def ocr_reader(self):
        """Lazy load EasyOCR reader"""
        if self._easyocr_reader is None:
            logger.info("Initializing EasyOCR reader for PDF processing...")
            self._easyocr_reader = easyocr.Reader(['en'])
        return self._easyocr_reader
    
    async def process_pdf(
        self,
        pdf_data: BinaryIO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process PDF: extract text from all pages, use OCR with layout parsing as option
        
        Args:
            pdf_data: Binary PDF data
            metadata: Optional metadata
            
        Returns:
            Dict with:
                - full_text: Complete extracted text
                - pages: List of page texts with OCR/layout info
                - chunks: Text chunks ready for embedding
                - metadata: Enhanced metadata with extraction methods
                - num_chunks: Number of chunks
                - token_count: Total tokens
                - layout_data: Layout structure per page
                - ocr_results: OCR results per page (if used)
        """
        try:
            pdf_data.seek(0)
            doc = fitz.open(stream=pdf_data.read(), filetype="pdf")
            
            pages_text = []
            total_text = []
            extraction_methods = []
            layout_data_pages = []
            ocr_results_pages = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try text extraction first
                text = page.get_text()
                
                # If text extraction yields little content, use PaddleOCR with layout
                if len(text.strip()) < 50:
                    logger.info(f"Using PaddleOCR with layout parsing for page {page_num + 1}")
                    
                    if self.use_paddle_ocr:
                        # Use PaddleOCR with layout
                        ocr_result = await paddle_ocr_service.extract_from_pdf_page(page, page_num + 1)
                        text = ocr_result.get("text", "")
                        layout_data_pages.append(ocr_result.get("layout", {}))
                        ocr_results_pages.append({
                            "page": page_num + 1,
                            "paragraphs": ocr_result.get("paragraphs", []),
                            "confidence": ocr_result.get("confidence", 0.0),
                            "bboxes": ocr_result.get("bboxes", [])
                        })
                        extraction_methods.append("paddle_ocr")
                    else:
                        # Fallback to EasyOCR
                        text = await self._ocr_page(page)
                        extraction_methods.append("easyocr")
                else:
                    extraction_methods.append("text_extraction")
                    layout_data_pages.append({})
                
                pages_text.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "method": extraction_methods[-1]
                })
                total_text.append(text)
            
            doc.close()
            
            # Combine all text
            full_text = "\n\n".join(total_text)
            
            if not full_text.strip():
                full_text = "[No text could be extracted from PDF]"
            
            logger.info(f"Extracted {len(full_text)} characters from {len(pages_text)} pages")
            
            # Chunk the text using existing text processor
            processed = await text_processor.process_text(
                full_text,
                metadata or {}
            )
            
            # Enhance metadata
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "page_count": len(pages_text),
                "extraction_methods": extraction_methods,
                "has_images": any(m in ["paddle_ocr", "easyocr"] for m in extraction_methods),
                "total_chars": len(full_text),
                "paddle_ocr_used": self.use_paddle_ocr and any(m == "paddle_ocr" for m in extraction_methods)
            })
            
            return {
                "full_text": full_text,
                "pages": pages_text,
                "chunks": processed["chunks"],
                "metadata": enhanced_metadata,
                "num_chunks": processed["num_chunks"],
                "token_count": processed["token_count"],
                "layout_data": layout_data_pages,
                "ocr_results": ocr_results_pages
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    async def _ocr_page(self, page: fitz.Page) -> str:
        """Extract text from PDF page using OCR"""
        try:
            # Render page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            image_array = np.array(image)
            
            # Run OCR
            ocr_results = self.ocr_reader.readtext(image_array)
            text = " ".join([text for (_, text, _) in ocr_results])
            
            return text
            
        except Exception as e:
            logger.error(f"OCR failed for page: {e}")
            return ""
    
    def validate_pdf(self, pdf_data: BinaryIO, max_size_mb: int = 50) -> Dict[str, Any]:
        """
        Validate PDF file
        
        Args:
            pdf_data: Binary PDF data
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dict with validation info and basic metadata
        """
        try:
            # Check file size
            pdf_data.seek(0, 2)
            file_size = pdf_data.tell()
            pdf_data.seek(0)
            
            if file_size > max_size_mb * 1024 * 1024:
                raise ValueError(f"PDF too large. Max size: {max_size_mb}MB")
            
            # Try to open PDF
            doc = fitz.open(stream=pdf_data.read(), filetype="pdf")
            pdf_data.seek(0)  # Reset
            
            # Get basic info
            info = {
                "valid": True,
                "page_count": len(doc),
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "is_encrypted": doc.is_encrypted,
                "metadata": doc.metadata
            }
            
            doc.close()
            
            if info["is_encrypted"]:
                raise ValueError("Encrypted PDFs are not supported")
            
            return info
            
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            raise ValueError(f"Invalid PDF file: {str(e)}")

# Global instance
pdf_processor = PDFProcessor()
