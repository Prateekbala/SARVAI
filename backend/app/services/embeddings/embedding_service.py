from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import numpy as np
from app.config import settings, MODELS_DIR
import logging
from .embedding_cache import (
    embedding_cache,
    batch_processor,
    semantic_deduplicator,
    quality_analyzer
)

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Enhanced embedding service with:
    - LRU caching for repeated queries
    - Batch optimization for throughput
    - Deduplication to reduce computation
    - Quality analysis and monitoring
    """
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
        self.cache_enabled = True
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_texts_embedded": 0
        }
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                cache_folder=str(MODELS_DIR)
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def embed_text(
        self,
        text: str,
        target_dim: int = 512,
        use_cache: bool = True
    ) -> List[float]:
        """
        Generate embedding for a single text with caching
        
        Args:
            text: Input text string
            target_dim: Target dimension (will pad if needed)
            use_cache: Whether to use cache lookup
            
        Returns:
            List of floats representing the embedding vector
        """
        self.stats["total_requests"] += 1
        
        # Try cache first
        if use_cache and self.cache_enabled:
            cached = embedding_cache.get(text, settings.EMBEDDING_MODEL)
            if cached is not None:
                self.stats["cache_hits"] += 1
                logger.debug("Cache hit for text embedding")
                return cached
            self.stats["cache_misses"] += 1
        
        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            # Pad to target dimension if needed
            if len(embedding) < target_dim:
                padding = np.zeros(target_dim - len(embedding))
                embedding = np.concatenate([embedding, padding])
            
            embedding_list = embedding.tolist()
            
            # Cache the result
            if use_cache and self.cache_enabled:
                embedding_cache.set(text, embedding_list, settings.EMBEDDING_MODEL)
            
            # Quality check
            quality = quality_analyzer.analyze_embedding(embedding_list)
            if not quality["is_valid"]:
                logger.warning(f"Generated invalid embedding for text: {text[:100]}")
            
            self.stats["total_texts_embedded"] += 1
            return embedding_list
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def embed_batch(
        self,
        texts: List[str],
        target_dim: int = 512,
        use_cache: bool = True,
        deduplicate: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with optimizations
        
        Args:
            texts: List of text strings
            target_dim: Target dimension (will pad if needed)
            use_cache: Whether to use cache lookup
            deduplicate: Whether to deduplicate before embedding
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        self.stats["total_requests"] += 1
        
        # Step 1: Check cache for all texts
        uncached_texts = []
        uncached_indices = []
        results = [None] * len(texts)
        
        if use_cache and self.cache_enabled:
            for i, text in enumerate(texts):
                cached = embedding_cache.get(text, settings.EMBEDDING_MODEL)
                if cached is not None:
                    results[i] = cached
                    self.stats["cache_hits"] += 1
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            if uncached_texts:
                self.stats["cache_misses"] += len(uncached_texts)
                logger.info(f"Cache: {len(texts) - len(uncached_texts)}/{len(texts)} hits")
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))
        
        if not uncached_texts:
            return results
        
        # Step 2: Deduplicate if enabled
        texts_to_embed = uncached_texts
        dedup_mapping = None
        
        if deduplicate and len(uncached_texts) > 1:
            unique_texts, dedup_mapping = semantic_deduplicator.find_duplicates(uncached_texts)
            texts_to_embed = unique_texts
        
        # Step 3: Batch processing
        try:
            batches = batch_processor.create_batches(texts_to_embed)
            all_embeddings = []
            
            for batch in batches:
                batch_embeddings = self._model.encode(batch, convert_to_numpy=True)
                
                # Pad if needed
                if batch_embeddings.shape[1] < target_dim:
                    padding = np.zeros((len(batch_embeddings), target_dim - batch_embeddings.shape[1]))
                    batch_embeddings = np.concatenate([batch_embeddings, padding], axis=1)
                
                all_embeddings.extend(batch_embeddings.tolist())
            
            # Step 4: Restore deduplication if applied
            if dedup_mapping is not None:
                all_embeddings = semantic_deduplicator.restore_order(all_embeddings, dedup_mapping)
            
            # Step 5: Cache new embeddings
            if use_cache and self.cache_enabled:
                for text, embedding in zip(uncached_texts, all_embeddings):
                    embedding_cache.set(text, embedding, settings.EMBEDDING_MODEL)
            
            # Step 6: Merge with cached results
            for idx, embedding in zip(uncached_indices, all_embeddings):
                results[idx] = embedding
            
            # Quality analysis
            quality = quality_analyzer.analyze_batch(results)
            logger.debug(f"Batch embedding quality: diversity={quality.get('diversity', 0):.3f}")
            
            self.stats["total_texts_embedded"] += len(uncached_texts)
            return results
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get the embedding dimension"""
        return self._model.get_sentence_embedding_dimension()
    
    def get_stats(self) -> dict:
        """Get embedding service statistics"""
        cache_hit_rate = 0.0
        if self.stats["total_requests"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_requests"]
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_stats": embedding_cache.get_stats()
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def enable_cache(self, enabled: bool = True):
        """Enable or disable caching"""
        self.cache_enabled = enabled
        logger.info(f"Embedding cache {'enabled' if enabled else 'disabled'}")

embedding_service = EmbeddingService()