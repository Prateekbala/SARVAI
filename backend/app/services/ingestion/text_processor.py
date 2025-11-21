from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
import tiktoken
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=self._token_length,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _token_length(self, text: str) -> int:
        """Calculate token length of text"""
        return len(self.tokenizer.encode(text))
    
    async def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided")
            
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            raise
    
    async def process_text(
        self, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process text: validate, clean, and chunk
        
        Args:
            text: Input text
            metadata: Optional metadata
            
        Returns:
            Processed text data with chunks
        """
        try:
            # Clean text
            cleaned_text = text.strip()
            
            # Chunk text
            chunks = await self.chunk_text(cleaned_text)
            
            # Calculate stats
            token_count = self._token_length(cleaned_text)
            
            result = {
                "original_text": cleaned_text,
                "chunks": chunks,
                "num_chunks": len(chunks),
                "token_count": token_count,
                "metadata": metadata or {}
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise

# Global instance
text_processor = TextProcessor()