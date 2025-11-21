from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.models.models import UserPreference
import logging

logger = logging.getLogger(__name__)

class PreferencesService:
    async def get_preferences(self, db: AsyncSession, user_id: UUID) -> Optional[UserPreference]:
        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        boost_topics: List[str] = None,
        suppress_topics: List[str] = None,
        search_preferences: Dict[str, Any] = None
    ) -> UserPreference:
        preferences = UserPreference(
            user_id=user_id,
            boost_topics=boost_topics or [],
            suppress_topics=suppress_topics or [],
            search_preferences=search_preferences or {}
        )
        
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
        
        return preferences
    
    async def update_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        boost_topics: Optional[List[str]] = None,
        suppress_topics: Optional[List[str]] = None,
        search_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[UserPreference]:
        preferences = await self.get_preferences(db, user_id)
        
        if not preferences:
            return await self.create_preferences(
                db, user_id, boost_topics, suppress_topics, search_preferences
            )
        
        if boost_topics is not None:
            preferences.boost_topics = boost_topics
        
        if suppress_topics is not None:
            preferences.suppress_topics = suppress_topics
        
        if search_preferences is not None:
            preferences.search_preferences = search_preferences
        
        preferences.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(preferences)
        
        return preferences
    
    async def add_boost_topic(self, db: AsyncSession, user_id: UUID, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, user_id)
        
        if not preferences:
            return await self.create_preferences(db, user_id, boost_topics=[topic])
        
        if topic not in preferences.boost_topics:
            preferences.boost_topics.append(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def remove_boost_topic(self, db: AsyncSession, user_id: UUID, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, user_id)
        
        if preferences and topic in preferences.boost_topics:
            preferences.boost_topics.remove(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def add_suppress_topic(self, db: AsyncSession, user_id: UUID, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, user_id)
        
        if not preferences:
            return await self.create_preferences(db, user_id, suppress_topics=[topic])
        
        if topic not in preferences.suppress_topics:
            preferences.suppress_topics.append(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def remove_suppress_topic(self, db: AsyncSession, user_id: UUID, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, user_id)
        
        if preferences and topic in preferences.suppress_topics:
            preferences.suppress_topics.remove(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences

preferences_service = PreferencesService()
