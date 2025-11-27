from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
import tiktoken
import logging

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

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
    
    def _calculate_bm25_metadata(self, chunks: List[str]) -> Dict[str, List[float]]:
        """
        Calculate BM25 scores for chunks (for later use in retrieval)
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dict with BM25 metadata
        """
        if BM25Okapi is None or not chunks:
            return {"bm25_enabled": False}
        
        try:
            # Tokenize chunks
            tokenized_chunks = [chunk.split() for chunk in chunks]
            
            # Create BM25 model
            bm25 = BM25Okapi(tokenized_chunks)
            
            return {
                "bm25_enabled": True,
                "num_chunks": len(chunks),
                "avg_chunk_length": sum(len(c) for c in tokenized_chunks) / len(tokenized_chunks) if tokenized_chunks else 0
            }
        except Exception as e:
            logger.warning(f"BM25 metadata calculation failed: {e}")
            return {"bm25_enabled": False, "error": str(e)}

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
        Process text: validate, clean, chunk, and calculate BM25 metadata
        
        Args:
            text: Input text
            metadata: Optional metadata
            
        Returns:
            Processed text data with chunks and BM25 metadata
        """
        try:
            # Clean text
            cleaned_text = text.strip()
            
            # Chunk text
            chunks = await self.chunk_text(cleaned_text)
            
            # Calculate stats
            token_count = self._token_length(cleaned_text)
            
            # Calculate BM25 metadata
            bm25_metadata = self._calculate_bm25_metadata(chunks)
            
            enhanced_metadata = metadata or {}
            enhanced_metadata.update(bm25_metadata)
            
            result = {
                "original_text": cleaned_text,
                "chunks": chunks,
                "num_chunks": len(chunks),
                "token_count": token_count,
                "metadata": enhanced_metadata
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise

# Global instance
text_processor = TextProcessor()