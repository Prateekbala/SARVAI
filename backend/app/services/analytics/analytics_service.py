from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.models.models import Memory, Embedding, Conversation, Message
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    async def get_user_stats(self, db: AsyncSession, namespace: str) -> Dict[str, Any]:
        total_memories = await self._get_total_memories(db, namespace)
        
        memories_by_type = await self._get_memories_by_type(db, namespace)
        
        total_conversations = await self._get_total_conversations(db, namespace)
        
        total_messages = await self._get_total_messages(db, namespace)
        
        recent_activity = await self._get_recent_activity(db, namespace, days=30)
        
        storage_info = await self._get_storage_info(db, namespace)
        
        return {
            "total_memories": total_memories,
            "memories_by_type": memories_by_type,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "recent_activity": recent_activity,
            "storage_info": storage_info
        }
    
    async def _get_total_memories(self, db: AsyncSession, namespace: str) -> int:
        result = await db.execute(
            select(func.count(Memory.id)).where(Memory.namespace == namespace)
        )
        return result.scalar() or 0
    
    async def _get_memories_by_type(self, db: AsyncSession, namespace: str) -> Dict[str, int]:
        result = await db.execute(
            select(
                Memory.content_type,
                func.count(Memory.id)
            )
            .where(Memory.namespace == namespace)
            .group_by(Memory.content_type)
        )
        
        return {row[0]: row[1] for row in result.all()}
    
    async def _get_total_conversations(self, db: AsyncSession, namespace: str) -> int:
        result = await db.execute(
            select(func.count(Conversation.id)).where(Conversation.namespace == namespace)
        )
        return result.scalar() or 0
    
    async def _get_total_messages(self, db: AsyncSession, namespace: str) -> int:
        result = await db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.namespace == namespace)
        )
        return result.scalar() or 0
    
    async def _get_recent_activity(
        self,
        db: AsyncSession,
        namespace: str,
        days: int
    ) -> Dict[str, int]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        memories_result = await db.execute(
            select(func.count(Memory.id))
            .where(
                and_(
                    Memory.namespace == namespace,
                    Memory.created_at >= cutoff_date
                )
            )
        )
        memories_count = memories_result.scalar() or 0
        
        conversations_result = await db.execute(
            select(func.count(Conversation.id))
            .where(
                and_(
                    Conversation.namespace == namespace,
                    Conversation.created_at >= cutoff_date
                )
            )
        )
        conversations_count = conversations_result.scalar() or 0
        
        return {
            "memories_added": memories_count,
            "conversations_started": conversations_count,
            "period_days": days
        }
    
    async def _get_storage_info(self, db: AsyncSession, namespace: str) -> Dict[str, Any]:
        embeddings_result = await db.execute(
            select(func.count(Embedding.id))
            .join(Memory)
            .where(Memory.namespace == namespace)
        )
        embeddings_count = embeddings_result.scalar() or 0
        
        estimated_size_mb = embeddings_count * 0.002
        
        return {
            "total_embeddings": embeddings_count,
            "estimated_size_mb": round(estimated_size_mb, 2)
        }
    
    async def get_timeline_grouped(
        self,
        db: AsyncSession,
        namespace: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(Memory)
            .where(Memory.namespace == namespace)
            .order_by(desc(Memory.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        memories = result.scalars().all()
        
        grouped = {}
        
        for memory in memories:
            date_key = memory.created_at.date().isoformat()
            
            if date_key not in grouped:
                grouped[date_key] = []
            
            grouped[date_key].append({
                "id": str(memory.id),
                "content_type": memory.content_type,
                "content_preview": memory.content[:200] if memory.content else None,
                "file_path": memory.file_path,
                "metadata": memory.meta_data,
                "created_at": memory.created_at.isoformat()
            })
        
        timeline = [
            {"date": date, "memories": items}
            for date, items in grouped.items()
        ]
        
        return timeline
    
    async def get_popular_searches(
        self,
        db: AsyncSession,
        namespace: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(
                Message.content,
                func.count(Message.id).label("count")
            )
            .join(Conversation)
            .where(
                and_(
                    Conversation.namespace == namespace,
                    Message.role == "user"
                )
            )
            .group_by(Message.content)
            .order_by(desc("count"))
            .limit(limit)
        )
        
        searches = result.all()
        
        return [
            {"query": search[0], "count": search[1]}
            for search in searches
        ]

analytics_service = AnalyticsService()
