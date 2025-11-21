from typing import List, Dict, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
import numpy as np
import logging

from app.models.models import Embedding, Memory
from app.services.retrieval.bm25_ranker import BM25Ranker

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    def __init__(self, alpha: float = 0.7):
        self.alpha = alpha
        self.bm25_ranker = BM25Ranker()
        
    def normalize_scores(self, scores: List[float]) -> List[float]:
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
        alpha: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        if alpha is None:
            alpha = self.alpha
        
        vector_dict = dict(vector_results)
        bm25_dict = dict(bm25_results)
        
        all_doc_ids = set(vector_dict.keys()) | set(bm25_dict.keys())
        
        vector_scores = [vector_dict.get(doc_id, 0.0) for doc_id in all_doc_ids]
        bm25_scores = [bm25_dict.get(doc_id, 0.0) for doc_id in all_doc_ids]
        
        norm_vector = self.normalize_scores(vector_scores)
        norm_bm25 = self.normalize_scores(bm25_scores)
        
        combined_scores = {}
        for i, doc_id in enumerate(all_doc_ids):
            combined_scores[doc_id] = alpha * norm_vector[i] + (1 - alpha) * norm_bm25[i]
        
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    async def search(
        self,
        db: AsyncSession,
        user_id: UUID,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        content_type: Optional[str] = None,
        fusion_method: str = "weighted"
    ) -> List[Dict]:
        vector_results = await self._vector_search(
            db, user_id, query_embedding, top_k * 2, content_type
        )
        
        if not vector_results:
            logger.warning("Hybrid search: No vector results found")
            return []
        
        documents = []
        for result in vector_results:
            documents.append({
                "id": str(result["embedding_id"]),
                "text": result["chunk_text"]
            })
        
        self.bm25_ranker.fit(documents)
        bm25_results = self.bm25_ranker.search(query_text, top_k * 2)
        
        vector_tuples = [(str(r["embedding_id"]), r["similarity"]) for r in vector_results]
        
        if fusion_method == "rrf":
            fused_results = self.reciprocal_rank_fusion(vector_tuples, bm25_results)
        else:
            fused_results = self.weighted_fusion(vector_tuples, bm25_results)
        
        embedding_id_map = {str(r["embedding_id"]): r for r in vector_results}
        
        final_results = []
        for embedding_id, score in fused_results[:top_k]:
            if embedding_id in embedding_id_map:
                result = embedding_id_map[embedding_id].copy()
                result["hybrid_score"] = float(score)
                final_results.append(result)
        
        logger.info(f"Hybrid search: Returned {len(final_results)} results")
        return final_results
    
    async def _vector_search(
        self,
        db: AsyncSession,
        user_id: UUID,
        query_embedding: List[float],
        top_k: int,
        content_type: Optional[str] = None
    ) -> List[Dict]:
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
                WHERE m.user_id = :user_id AND m.content_type = :content_type
                ORDER BY e.embedding <=> :query_embedding
                LIMIT :top_k
            """)
            result = await db.execute(
                query,
                {
                    "query_embedding": embedding_str,
                    "user_id": user_id,
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
                WHERE m.user_id = :user_id
                ORDER BY e.embedding <=> :query_embedding
                LIMIT :top_k
            """)
            result = await db.execute(
                query,
                {
                    "query_embedding": embedding_str,
                    "user_id": user_id,
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

hybrid_search_engine = HybridSearchEngine()
