"""Hybrid search: Vector + BM25 + Re-ranking"""
from typing import List, Dict, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import numpy as np
import logging

from app.models.models import Embedding, Memory
from app.services.retrieval.bm25_ranker import BM25Ranker
from app.services.retrieval.cross_encoder_reranker import reranker

logger = logging.getLogger(__name__)

class AdvancedHybridSearchEngine:
    
    def __init__(
        self,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.3,
        use_reranking: bool = True,
        rerank_top_k: int = 20
    ):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.use_reranking = use_reranking
        self.rerank_top_k = rerank_top_k
        self.bm25_ranker = BM25Ranker()
        
        total_weight = vector_weight + bm25_weight
        self.vector_weight /= total_weight
        self.bm25_weight /= total_weight
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range"""
        if not scores or max(scores) == min(scores):
            return [1.0] * len(scores)
        
        min_score = min(scores)
        max_score = max(scores)
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def reciprocal_rank_fusion(
        self,
        vector_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        k: int = 60
    ) -> List[Tuple[str, float]]:
        """Reciprocal Rank Fusion for combining rankings"""
        rrf_scores = {}
        
        for rank, (doc_id, _) in enumerate(vector_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
        for rank, (doc_id, _) in enumerate(bm25_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    def weighted_fusion(
        self,
        vector_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        vector_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """Weighted fusion of vector and BM25 results"""
        if vector_weight is None:
            vector_weight = self.vector_weight
        if bm25_weight is None:
            bm25_weight = self.bm25_weight
        
        vector_dict = dict(vector_results)
        bm25_dict = dict(bm25_results)
        
        all_doc_ids = set(vector_dict.keys()) | set(bm25_dict.keys())
        
        vector_scores = [vector_dict.get(doc_id, 0.0) for doc_id in all_doc_ids]
        bm25_scores = [bm25_dict.get(doc_id, 0.0) for doc_id in all_doc_ids]
        
        norm_vector = self.normalize_scores(vector_scores)
        norm_bm25 = self.normalize_scores(bm25_scores)
        
        combined_scores = {}
        for i, doc_id in enumerate(all_doc_ids):
            combined_scores[doc_id] = (
                vector_weight * norm_vector[i] + 
                bm25_weight * norm_bm25[i]
            )
        
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    async def search(
        self,
        db: AsyncSession,
        namespace: str,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        content_type: Optional[str] = None,
        fusion_method: str = "weighted",
        use_reranking: Optional[bool] = None
    ) -> List[Dict]:
        """
        Advanced hybrid search with optional re-ranking
        
        Args:
            db: Database session
            namespace: User namespace
            query_embedding: Query embedding vector
            query_text: Query text for BM25
            top_k: Number of results to return
            content_type: Filter by content type
            fusion_method: 'weighted' or 'rrf'
            use_reranking: Override default re-ranking setting
            
        Returns:
            List of results with rankings and scores
        """
        try:
            # Step 1: Vector search
            vector_results = await self._vector_search(
                db, namespace, query_embedding, top_k * 2, content_type
            )
            
            if not vector_results:
                logger.warning("Advanced hybrid search: No vector results found")
                return []
            
            logger.info(f"Vector search returned {len(vector_results)} results")
            
            # Step 2: BM25 search
            documents = [
                {"id": str(r["embedding_id"]), "text": r["chunk_text"]}
                for r in vector_results
            ]
            
            self.bm25_ranker.fit(documents)
            bm25_results = self.bm25_ranker.search(query_text, top_k * 2)
            
            logger.info(f"BM25 search returned {len(bm25_results)} results")
            
            # Step 3: Fusion
            vector_tuples = [
                (str(r["embedding_id"]), r["similarity"]) for r in vector_results
            ]
            
            if fusion_method == "rrf":
                fused_results = self.reciprocal_rank_fusion(vector_tuples, bm25_results)
            else:
                fused_results = self.weighted_fusion(vector_tuples, bm25_results)
            
            logger.info(f"Fused results: {len(fused_results)} documents")
            
            # Step 4: Re-ranking (optional)
            use_rerank = use_reranking if use_reranking is not None else self.use_reranking
            
            if use_rerank and len(fused_results) > 0:
                fused_results = await self._rerank_results(
                    query_text, fused_results, min(self.rerank_top_k, top_k * 2)
                )
                logger.info(f"Re-ranked results: {len(fused_results)} documents")
            
            # Step 5: Map back to original results
            embedding_id_map = {str(r["embedding_id"]): r for r in vector_results}
            
            final_results = []
            for rank, (embedding_id, score) in enumerate(fused_results[:top_k]):
                if embedding_id in embedding_id_map:
                    result = embedding_id_map[embedding_id].copy()
                    result["hybrid_score"] = float(score)
                    result["rank"] = rank + 1
                    final_results.append(result)
            
            logger.info(f"Advanced hybrid search: Returned {len(final_results)} final results")
            return final_results
            
        except Exception as e:
            logger.error(f"Advanced hybrid search failed: {e}")
            raise
    
    async def _rerank_results(
        self,
        query: str,
        fused_results: List[Tuple[str, float]],
        top_k: int
    ) -> List[Tuple[str, float]]:
        """
        Re-rank fused results using Cross-Encoder
        
        Args:
            query: Query text
            fused_results: List of (doc_id, score) tuples
            top_k: Number to re-rank
            
        Returns:
            Re-ranked results
        """
        try:
            # Take top results to re-rank
            results_to_rerank = fused_results[:top_k]
            
            if not results_to_rerank:
                return fused_results
            
            # Get doc_ids and prepare for re-ranking
            doc_ids_to_rerank = [r[0] for r in results_to_rerank]
            
            # Re-rank using Cross-Encoder
            reranked = reranker.rerank_with_ids(
                query=query,
                passages_with_ids=[(doc_id, doc_id) for doc_id in doc_ids_to_rerank],
                top_k=len(results_to_rerank)
            )
            
            # Convert back to tuple format
            reranked_tuples = [(r["id"], r["score"]) for r in reranked]
            
            # Combine with remaining results
            return reranked_tuples + fused_results[top_k:]
            
        except Exception as e:
            logger.warning(f"Re-ranking failed, returning fused results: {e}")
            return fused_results
    
    async def _vector_search(
        self,
        db: AsyncSession,
        namespace: str,
        query_embedding: List[float],
        top_k: int,
        content_type: Optional[str] = None
    ) -> List[Dict]:
        """Vector search using pgvector"""
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        if content_type:
            query = text("""
                SELECT 
                    e.id as embedding_id,
                    e.chunk_text,
                    e.chunk_index,
                    m.id as memory_id,
                    m.content_type,
                    m.file_path,
                    m.meta_data,
                    m.created_at,
                    1 - (e.embedding <=> :query_embedding) as similarity
                FROM embeddings e
                JOIN memories m ON e.memory_id = m.id
                WHERE m.namespace = :namespace AND m.content_type = :content_type
                ORDER BY e.embedding <=> :query_embedding
                LIMIT :top_k
            """)
            result = await db.execute(
                query,
                {
                    "query_embedding": embedding_str,
                    "namespace": namespace,
                    "content_type": content_type,
                    "top_k": top_k
                }
            )
        else:
            query = text("""
                SELECT 
                    e.id as embedding_id,
                    e.chunk_text,
                    e.chunk_index,
                    m.id as memory_id,
                    m.content_type,
                    m.file_path,
                    m.meta_data,
                    m.created_at,
                    1 - (e.embedding <=> :query_embedding) as similarity
                FROM embeddings e
                JOIN memories m ON e.memory_id = m.id
                WHERE m.namespace = :namespace
                ORDER BY e.embedding <=> :query_embedding
                LIMIT :top_k
            """)
            result = await db.execute(
                query,
                {
                    "query_embedding": embedding_str,
                    "namespace": namespace,
                    "top_k": top_k
                }
            )
        
        rows = result.fetchall()
        
        return [
            {
                "embedding_id": row.embedding_id,
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "memory_id": row.memory_id,
                "content_type": row.content_type,
                "file_path": row.file_path,
                "metadata": row.meta_data,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "similarity": float(row.similarity)
            }
            for row in rows
        ]


# Global instance
advanced_hybrid_search = AdvancedHybridSearchEngine(
    vector_weight=0.5,
    bm25_weight=0.3,
    use_reranking=True,
    rerank_top_k=20
)
