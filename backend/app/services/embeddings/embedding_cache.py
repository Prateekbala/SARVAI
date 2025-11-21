"""
Advanced embedding service with caching and batch optimization
Inspired by M³-Agent's efficient memory encoding
"""

from typing import List, Dict, Optional, Tuple
import hashlib
import json
import logging
from functools import lru_cache
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    In-memory LRU cache for embeddings
    For production, consider Redis or similar distributed cache
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: Dict[str, List[float]] = {}
        self._access_order: List[str] = []
    
    def _make_key(self, text: str, model: str = "default") -> str:
        """Create cache key from text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"{model}:{text_hash}"
    
    def get(self, text: str, model: str = "default") -> Optional[List[float]]:
        """Retrieve embedding from cache"""
        key = self._make_key(text, model)
        
        if key in self._cache:
            # Move to end (most recently used)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            logger.debug(f"Cache hit for text: {text[:50]}...")
            return self._cache[key]
        
        return None
    
    def set(self, text: str, embedding: List[float], model: str = "default"):
        """Store embedding in cache"""
        key = self._make_key(text, model)
        
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")
        
        self._cache[key] = embedding
        
        if key not in self._access_order:
            self._access_order.append(key)
    
    def clear(self):
        """Clear all cached embeddings"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Embedding cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "utilization": len(self._cache) / self.max_size
        }


class BatchProcessor:
    """
    Intelligent batch processing for embeddings
    Optimizes throughput while maintaining responsiveness
    """
    
    def __init__(
        self,
        max_batch_size: int = 32,
        max_wait_time: float = 0.1
    ):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
    
    def optimize_batch_size(
        self,
        texts: List[str],
        avg_text_length: Optional[int] = None
    ) -> int:
        """
        Determine optimal batch size based on text characteristics
        Longer texts -> smaller batches to prevent memory issues
        """
        if not texts:
            return self.max_batch_size
        
        if avg_text_length is None:
            avg_text_length = sum(len(t) for t in texts) // len(texts)
        
        # Adaptive batch sizing
        if avg_text_length > 2000:
            return min(8, len(texts))
        elif avg_text_length > 1000:
            return min(16, len(texts))
        else:
            return min(self.max_batch_size, len(texts))
    
    def create_batches(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[str]]:
        """Split texts into optimally sized batches"""
        if batch_size is None:
            batch_size = self.optimize_batch_size(texts)
        
        batches = []
        for i in range(0, len(texts), batch_size):
            batches.append(texts[i:i + batch_size])
        
        logger.debug(f"Created {len(batches)} batches from {len(texts)} texts")
        return batches


class SemanticDeduplicator:
    """
    Detect and handle semantically duplicate texts before embedding
    Reduces redundant computation
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold
    
    @staticmethod
    def _simple_hash(text: str) -> str:
        """Fast hash for exact duplicate detection"""
        # Normalize: lowercase, remove extra whitespace
        normalized = " ".join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def find_duplicates(
        self,
        texts: List[str]
    ) -> Tuple[List[str], Dict[int, int]]:
        """
        Find duplicate texts
        Returns: (unique_texts, mapping from original index to unique index)
        """
        seen_hashes = {}
        unique_texts = []
        index_mapping = {}
        
        for i, text in enumerate(texts):
            text_hash = self._simple_hash(text)
            
            if text_hash in seen_hashes:
                # Duplicate found
                index_mapping[i] = seen_hashes[text_hash]
            else:
                # New unique text
                unique_idx = len(unique_texts)
                seen_hashes[text_hash] = unique_idx
                index_mapping[i] = unique_idx
                unique_texts.append(text)
        
        duplicates_found = len(texts) - len(unique_texts)
        if duplicates_found > 0:
            logger.info(f"Found {duplicates_found} duplicate texts, reduced to {len(unique_texts)}")
        
        return unique_texts, index_mapping
    
    def restore_order(
        self,
        unique_embeddings: List[List[float]],
        index_mapping: Dict[int, int]
    ) -> List[List[float]]:
        """Restore original order after deduplication"""
        result = []
        for i in range(len(index_mapping)):
            unique_idx = index_mapping[i]
            result.append(unique_embeddings[unique_idx])
        return result


class EmbeddingQualityAnalyzer:
    """
    Analyze embedding quality and detect potential issues
    """
    
    @staticmethod
    def analyze_embedding(embedding: List[float]) -> Dict:
        """Analyze a single embedding vector"""
        emb_array = np.array(embedding)
        
        return {
            "dimension": len(embedding),
            "norm": float(np.linalg.norm(emb_array)),
            "mean": float(np.mean(emb_array)),
            "std": float(np.std(emb_array)),
            "non_zero_ratio": float(np.count_nonzero(emb_array) / len(emb_array)),
            "is_valid": len(embedding) > 0 and not np.isnan(emb_array).any()
        }
    
    @staticmethod
    def analyze_batch(embeddings: List[List[float]]) -> Dict:
        """Analyze a batch of embeddings"""
        if not embeddings:
            return {"error": "Empty batch"}
        
        emb_array = np.array(embeddings)
        
        # Calculate diversity (average pairwise distance)
        diversity = 0.0
        if len(embeddings) > 1:
            from scipy.spatial.distance import pdist
            distances = pdist(emb_array, metric='cosine')
            diversity = float(np.mean(distances))
        
        return {
            "count": len(embeddings),
            "dimension": len(embeddings[0]),
            "avg_norm": float(np.mean([np.linalg.norm(e) for e in embeddings])),
            "diversity": diversity,
            "all_valid": not np.isnan(emb_array).any()
        }


# Global instances
embedding_cache = EmbeddingCache(max_size=10000)
batch_processor = BatchProcessor(max_batch_size=32)
semantic_deduplicator = SemanticDeduplicator()
quality_analyzer = EmbeddingQualityAnalyzer()
