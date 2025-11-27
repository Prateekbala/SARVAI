"""Cross-Encoder semantic re-ranking for search results"""
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np

try:
    from cross_encoder import CrossEncoder
except ImportError:
    CrossEncoder = None

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size: int = 32
    ):
        if CrossEncoder is None:
            raise ImportError("cross-encoder not installed. Install with: pip install cross-encoder")
        
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        logger.info(f"Initializing Cross-Encoder: {model_name}")
    
    @property
    def model(self):
        """Lazy load Cross-Encoder model"""
        if self._model is None:
            logger.info(f"Loading Cross-Encoder model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
        return self._model
    
    def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
        return_scores: bool = True
    ) -> List[Dict[str, any]]:
        """
        Re-rank passages by relevance to query
        
        Args:
            query: Search query
            passages: List of passages/documents to re-rank
            top_k: Number of top results to return (None = all)
            return_scores: Whether to include relevance scores
            
        Returns:
            List of dicts with 'passage_id', 'text', 'score' (if return_scores=True)
        """
        if not passages:
            return []
        
        try:
            # Create query-passage pairs
            pairs = [[query, passage] for passage in passages]
            
            # Get scores
            scores = self.model.predict(pairs, batch_size=self.batch_size)
            
            # Convert scores to probabilities (sigmoid)
            if len(scores.shape) > 1:
                # Multi-label output
                scores = scores[:, 0]
            
            # Create result list with scores
            results = []
            for idx, (passage, score) in enumerate(zip(passages, scores)):
                results.append({
                    "passage_id": idx,
                    "text": passage,
                    "score": float(score),
                    "rank": idx
                })
            
            # Sort by score descending
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Assign new ranks
            for rank, result in enumerate(results):
                result["rank"] = rank + 1
            
            # Return top_k if specified
            if top_k is not None:
                results = results[:top_k]
            
            return results
            
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            # Return passages in original order if reranking fails
            return [
                {
                    "passage_id": idx,
                    "text": passage,
                    "score": 0.5,
                    "rank": idx + 1
                }
                for idx, passage in enumerate(passages)
            ]
    
    def rerank_with_ids(
        self,
        query: str,
        passages_with_ids: List[Tuple[str, str]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """
        Re-rank passages with persistent IDs
        
        Args:
            query: Search query
            passages_with_ids: List of (id, text) tuples
            top_k: Number of top results to return
            
        Returns:
            List of dicts with 'id', 'text', 'score', 'rank'
        """
        if not passages_with_ids:
            return []
        
        try:
            ids = [p[0] for p in passages_with_ids]
            texts = [p[1] for p in passages_with_ids]
            
            # Create pairs
            pairs = [[query, text] for text in texts]
            
            # Get scores
            scores = self.model.predict(pairs, batch_size=self.batch_size)
            
            if len(scores.shape) > 1:
                scores = scores[:, 0]
            
            # Create results
            results = []
            for idx, (doc_id, text, score) in enumerate(zip(ids, texts, scores)):
                results.append({
                    "id": doc_id,
                    "text": text,
                    "score": float(score),
                    "rank": idx
                })
            
            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Assign ranks
            for rank, result in enumerate(results):
                result["rank"] = rank + 1
            
            if top_k is not None:
                results = results[:top_k]
            
            return results
            
        except Exception as e:
            logger.error(f"Re-ranking with IDs failed: {e}")
            return [
                {
                    "id": doc_id,
                    "text": text,
                    "score": 0.5,
                    "rank": idx + 1
                }
                for idx, (doc_id, text) in enumerate(passages_with_ids)
            ]
    
    def batch_rerank(
        self,
        query_passages: List[Tuple[str, List[str]]],
        top_k: Optional[int] = None
    ) -> List[List[Dict[str, any]]]:
        """
        Re-rank multiple queries with their passages
        
        Args:
            query_passages: List of (query, [passages]) tuples
            top_k: Top results per query
            
        Returns:
            List of reranked results per query
        """
        results = []
        for query, passages in query_passages:
            ranked = self.rerank(query, passages, top_k=top_k)
            results.append(ranked)
        return results


# Global instance
reranker = CrossEncoderReranker(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
)
