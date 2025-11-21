from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from app.models.models import Memory, Embedding, Conversation, Message
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    async def get_user_stats(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        total_memories = await self._get_total_memories(db, user_id)
        
        memories_by_type = await self._get_memories_by_type(db, user_id)
        
        total_conversations = await self._get_total_conversations(db, user_id)
        
        total_messages = await self._get_total_messages(db, user_id)
        
        recent_activity = await self._get_recent_activity(db, user_id, days=30)
        
        storage_info = await self._get_storage_info(db, user_id)
        
        return {
            "total_memories": total_memories,
            "memories_by_type": memories_by_type,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "recent_activity": recent_activity,
            "storage_info": storage_info
        }
    
    async def _get_total_memories(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(Memory.id)).where(Memory.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _get_memories_by_type(self, db: AsyncSession, user_id: UUID) -> Dict[str, int]:
        result = await db.execute(
            select(
                Memory.content_type,
                func.count(Memory.id)
            )
            .where(Memory.user_id == user_id)
            .group_by(Memory.content_type)
        )
        
        return {row[0]: row[1] for row in result.all()}
    
    async def _get_total_conversations(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _get_total_messages(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _get_recent_activity(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int
    ) -> Dict[str, int]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        memories_result = await db.execute(
            select(func.count(Memory.id))
            .where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at >= cutoff_date
                )
            )
        )
        memories_count = memories_result.scalar() or 0
        
        conversations_result = await db.execute(
            select(func.count(Conversation.id))
            .where(
                and_(
                    Conversation.user_id == user_id,
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
    
    async def _get_storage_info(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        embeddings_result = await db.execute(
            select(func.count(Embedding.id))
            .join(Memory)
            .where(Memory.user_id == user_id)
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
        user_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
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
        user_id: UUID,
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
                    Conversation.user_id == user_id,
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
