"""
Hierarchical Memory Manager inspired by M³-Agent paper
Implements episodic and semantic memory layers with temporal importance scoring
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from uuid import UUID
from datetime import datetime, timedelta
import logging
import numpy as np

from app.models.models import Memory, Embedding, MemorySummary, MemoryAccess
from app.services.embeddings.embedding_service import embedding_service
from app.config import settings

logger = logging.getLogger(__name__)


class MemoryType:
    """Memory classification based on cognitive science"""
    EPISODIC = "episodic"  # Specific experiences/events
    SEMANTIC = "semantic"  # General facts/knowledge
    PROCEDURAL = "procedural"  # How-to knowledge
    WORKING = "working"  # Temporary/session memory


class MemoryImportance:
    """Calculate memory importance based on multiple factors"""
    
    @staticmethod
    def calculate_score(
        memory: Memory,
        access_count: int = 0,
        last_accessed: Optional[datetime] = None,
        embedding_variance: float = 0.0
    ) -> float:
        """
        Calculate importance score combining:
        - Recency (temporal decay)
        - Access frequency (popularity)
        - Semantic richness (embedding variance)
        - Content type weight
        """
        now = datetime.utcnow()
        
        # Temporal decay (exponential)
        age_days = (now - memory.created_at).days
        recency_score = np.exp(-age_days / 30.0)  # Half-life of 30 days
        
        # Access frequency (logarithmic to prevent dominance)
        frequency_score = np.log1p(access_count) / 10.0
        
        # Recency of access (if accessed recently, boost)
        access_recency = 0.0
        if last_accessed:
            days_since_access = (now - last_accessed).days
            access_recency = np.exp(-days_since_access / 7.0)  # Half-life of 7 days
        
        # Content type weights
        type_weights = {
            "text": 1.0,
            "pdf": 1.2,  # PDFs often contain important documents
            "image": 0.9,
            "audio": 1.1,
            "web": 0.7  # Web content is more ephemeral
        }
        content_weight = type_weights.get(memory.content_type, 1.0)
        
        # Semantic richness (higher variance = more information)
        richness_score = min(embedding_variance, 1.0)
        
        # Combined weighted score
        importance = (
            0.35 * recency_score +
            0.25 * frequency_score +
            0.20 * access_recency +
            0.15 * content_weight +
            0.05 * richness_score
        )
        
        return importance


class MemoryManager:
    """
    Hierarchical memory management system with:
    - Episodic memory (recent, specific experiences)
    - Semantic memory (consolidated, general knowledge)
    - Automatic consolidation and forgetting
    """
    
    def __init__(self):
        self.episodic_threshold_days = 7  # Recent memories
        self.consolidation_threshold_days = 30  # When to consolidate
        self.min_importance_threshold = 0.1  # Minimum to keep
        
    async def classify_memory(
        self,
        db: AsyncSession,
        memory: Memory
    ) -> str:
        """
        Classify memory into episodic or semantic based on:
        - Temporal markers (dates, "yesterday", etc.)
        - Content specificity
        - Metadata indicators
        """
        content = memory.content or ""
        metadata = memory.meta_data or {}
        
        # Check metadata for explicit classification
        if metadata.get("memory_type"):
            return metadata["memory_type"]
        
        # Temporal markers indicate episodic memory
        temporal_markers = [
            "yesterday", "today", "last week", "on monday",
            "this morning", "last night", datetime.now().year
        ]
        
        content_lower = content.lower()
        has_temporal = any(marker in content_lower for marker in temporal_markers)
        
        # Personal pronouns indicate episodic (personal experience)
        personal_markers = ["i ", "my ", "me ", "we ", "our "]
        has_personal = any(marker in content_lower for marker in personal_markers)
        
        # Short, specific content is likely episodic
        is_short = len(content.split()) < 100
        
        # Classification logic
        if (has_temporal and has_personal) or (is_short and has_personal):
            return MemoryType.EPISODIC
        elif memory.content_type == "pdf" or len(content.split()) > 500:
            return MemoryType.SEMANTIC
        else:
            return MemoryType.EPISODIC  # Default to episodic
    
    async def get_memory_importance(
        self,
        db: AsyncSession,
        memory_id: UUID
    ) -> float:
        """Calculate current importance score for a memory"""
        
        # Get memory
        result = await db.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        
        if not memory:
            return 0.0
        
        # Get access statistics
        access_result = await db.execute(
            select(
                func.count(MemoryAccess.id).label("access_count"),
                func.max(MemoryAccess.accessed_at).label("last_accessed")
            ).where(MemoryAccess.memory_id == memory_id)
        )
        stats = access_result.first()
        
        access_count = stats.access_count if stats else 0
        last_accessed = stats.last_accessed if stats else None
        
        # Get embedding variance (semantic richness)
        embedding_result = await db.execute(
            select(Embedding.embedding).where(Embedding.memory_id == memory_id)
        )
        embeddings = [row[0] for row in embedding_result.all()]
        
        embedding_variance = 0.0
        if embeddings and len(embeddings) > 1:
            embedding_array = np.array(embeddings)
            embedding_variance = float(np.var(embedding_array))
        
        # Calculate importance
        importance = MemoryImportance.calculate_score(
            memory=memory,
            access_count=access_count,
            last_accessed=last_accessed,
            embedding_variance=embedding_variance
        )
        
        logger.debug(f"Memory {memory_id} importance: {importance:.3f}")
        return importance
    
    async def record_memory_access(
        self,
        db: AsyncSession,
        memory_id: UUID,
        access_type: str = "retrieval"
    ):
        """Track memory access for importance calculation"""
        access = MemoryAccess(
            memory_id=memory_id,
            access_type=access_type,
            accessed_at=datetime.utcnow()
        )
        db.add(access)
        await db.commit()
    
    async def consolidate_memories(
        self,
        db: AsyncSession,
        user_id: UUID,
        force: bool = False
    ) -> Dict:
        """
        Consolidate old episodic memories into semantic summaries
        Similar to M³-Agent's memory consolidation mechanism
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.consolidation_threshold_days)
        
        # Find old episodic memories not yet consolidated
        result = await db.execute(
            select(Memory).where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at < cutoff_date,
                    ~Memory.id.in_(
                        select(MemorySummary.source_memory_ids).
                        where(MemorySummary.user_id == user_id)
                    )
                )
            ).limit(50)  # Process in batches
        )
        
        memories_to_consolidate = result.scalars().all()
        
        if not memories_to_consolidate:
            logger.info(f"No memories to consolidate for user {user_id}")
            return {"consolidated": 0, "summaries_created": 0}
        
        # Group by topic/similarity
        memory_groups = await self._cluster_memories(db, memories_to_consolidate)
        
        summaries_created = 0
        memories_consolidated = 0
        
        for group in memory_groups:
            # Create consolidated summary
            summary = await self._create_memory_summary(db, user_id, group)
            
            if summary:
                summaries_created += 1
                memories_consolidated += len(group)
                logger.info(f"Consolidated {len(group)} memories into summary {summary.id}")
        
        await db.commit()
        
        return {
            "consolidated": memories_consolidated,
            "summaries_created": summaries_created
        }
    
    async def _cluster_memories(
        self,
        db: AsyncSession,
        memories: List[Memory],
        similarity_threshold: float = 0.7
    ) -> List[List[Memory]]:
        """Group similar memories together for consolidation"""
        if not memories:
            return []
        
        # Get embeddings for all memories
        memory_embeddings = []
        for memory in memories:
            result = await db.execute(
                select(Embedding.embedding).
                where(Embedding.memory_id == memory.id).
                limit(1)
            )
            emb = result.scalar_one_or_none()
            if emb:
                memory_embeddings.append((memory, np.array(emb)))
        
        if not memory_embeddings:
            return [[m] for m in memories]  # Each memory in own group
        
        # Simple clustering by similarity
        groups = []
        used = set()
        
        for i, (memory_i, emb_i) in enumerate(memory_embeddings):
            if i in used:
                continue
            
            group = [memory_i]
            used.add(i)
            
            for j, (memory_j, emb_j) in enumerate(memory_embeddings[i+1:], start=i+1):
                if j in used:
                    continue
                
                # Cosine similarity
                similarity = np.dot(emb_i, emb_j) / (
                    np.linalg.norm(emb_i) * np.linalg.norm(emb_j) + 1e-8
                )
                
                if similarity >= similarity_threshold:
                    group.append(memory_j)
                    used.add(j)
            
            groups.append(group)
        
        logger.info(f"Clustered {len(memories)} memories into {len(groups)} groups")
        return groups
    
    async def _create_memory_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        memories: List[Memory]
    ) -> Optional[MemorySummary]:
        """Create a consolidated summary from multiple memories"""
        if not memories:
            return None
        
        # Combine content
        combined_content = "\n\n".join(
            f"[{m.created_at.strftime('%Y-%m-%d')}] {m.content}"
            for m in memories if m.content
        )
        
        # Generate summary using LLM (simplified - you can enhance this)
        from app.services.rag.generator import llm_generator
        
        summary_prompt = [{
            "role": "system",
            "content": "Create a concise summary of the following related memories, capturing key facts and themes."
        }, {
            "role": "user",
            "content": combined_content[:4000]  # Limit to prevent token overflow
        }]
        
        try:
            summary_text = await llm_generator.generate(summary_prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            summary_text = f"Summary of {len(memories)} related memories about various topics"
        
        # Create embedding for summary
        summary_embedding = await embedding_service.embed_text(summary_text)
        
        # Create summary record
        summary = MemorySummary(
            user_id=user_id,
            summary_text=summary_text,
            summary_embedding=summary_embedding,
            source_memory_ids=[str(m.id) for m in memories],
            memory_count=len(memories),
            date_range_start=min(m.created_at for m in memories),
            date_range_end=max(m.created_at for m in memories),
            importance_score=np.mean([
                await self.get_memory_importance(db, m.id) for m in memories
            ])
        )
        
        db.add(summary)
        return summary
    
    async def forget_unimportant_memories(
        self,
        db: AsyncSession,
        user_id: UUID,
        threshold: Optional[float] = None
    ) -> int:
        """
        Remove memories below importance threshold
        Implements selective forgetting to manage memory size
        """
        threshold = threshold or self.min_importance_threshold
        
        # Get all memories older than consolidation period
        cutoff_date = datetime.utcnow() - timedelta(days=self.consolidation_threshold_days)
        
        result = await db.execute(
            select(Memory).where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at < cutoff_date
                )
            )
        )
        
        old_memories = result.scalars().all()
        
        forgotten_count = 0
        for memory in old_memories:
            importance = await self.get_memory_importance(db, memory.id)
            
            if importance < threshold:
                # Mark for deletion or archive
                await db.delete(memory)
                forgotten_count += 1
                logger.info(f"Forgetting low-importance memory {memory.id} (score: {importance:.3f})")
        
        await db.commit()
        logger.info(f"Forgot {forgotten_count} unimportant memories for user {user_id}")
        
        return forgotten_count
    
    async def retrieve_with_hierarchy(
        self,
        db: AsyncSession,
        user_id: UUID,
        query_embedding: List[float],
        top_k: int = 10,
        include_summaries: bool = True
    ) -> List[Dict]:
        """
        Retrieve from both episodic memories and semantic summaries
        Implements hierarchical memory retrieval
        """
        results = []
        
        # 1. Search recent episodic memories (high detail)
        recent_cutoff = datetime.utcnow() - timedelta(days=self.episodic_threshold_days)
        
        episodic_result = await db.execute(
            select(
                Memory,
                Embedding,
                func.cosine_distance(Embedding.embedding, query_embedding).label("distance")
            ).join(Embedding, Memory.id == Embedding.memory_id).
            where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at >= recent_cutoff
                )
            ).order_by(desc("distance")).limit(top_k // 2)
        )
        
        for memory, embedding, distance in episodic_result.all():
            results.append({
                "memory_id": memory.id,
                "content_type": memory.content_type,
                "chunk_text": embedding.chunk_text,
                "similarity": 1 - distance,
                "memory_type": "episodic",
                "created_at": memory.created_at,
                "metadata": memory.meta_data
            })
        
        # 2. Search semantic summaries (consolidated knowledge)
        if include_summaries:
            summary_result = await db.execute(
                select(
                    MemorySummary,
                    func.cosine_distance(
                        MemorySummary.summary_embedding,
                        query_embedding
                    ).label("distance")
                ).where(
                    MemorySummary.user_id == user_id
                ).order_by(desc("distance")).limit(top_k // 2)
            )
            
            for summary, distance in summary_result.all():
                results.append({
                    "memory_id": summary.id,
                    "content_type": "summary",
                    "chunk_text": summary.summary_text,
                    "similarity": 1 - distance,
                    "memory_type": "semantic",
                    "created_at": summary.created_at,
                    "metadata": {
                        "memory_count": summary.memory_count,
                        "date_range": f"{summary.date_range_start} to {summary.date_range_end}"
                    }
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]


memory_manager = MemoryManager()
