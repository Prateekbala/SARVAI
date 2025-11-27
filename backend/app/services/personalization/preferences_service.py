from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.models.models import UserPreference
import logging

logger = logging.getLogger(__name__)

class PreferencesService:
    async def get_preferences(self, db: AsyncSession, namespace: str) -> Optional[UserPreference]:
        result = await db.execute(
            select(UserPreference).where(UserPreference.namespace == namespace)
        )
        return result.scalar_one_or_none()
    
    async def create_preferences(
        self,
        db: AsyncSession,
        namespace: str,
        boost_topics: List[str] = None,
        suppress_topics: List[str] = None,
        search_preferences: Dict[str, Any] = None
    ) -> UserPreference:
        preferences = UserPreference(
            namespace=namespace,
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
        namespace: str,
        boost_topics: Optional[List[str]] = None,
        suppress_topics: Optional[List[str]] = None,
        search_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[UserPreference]:
        preferences = await self.get_preferences(db, namespace)
        
        if not preferences:
            return await self.create_preferences(
                db, namespace, boost_topics, suppress_topics, search_preferences
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
    
    async def add_boost_topic(self, db: AsyncSession, namespace: str, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, namespace)
        
        if not preferences:
            return await self.create_preferences(db, namespace, boost_topics=[topic])
        
        if topic not in preferences.boost_topics:
            preferences.boost_topics.append(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def remove_boost_topic(self, db: AsyncSession, namespace: str, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, namespace)
        
        if preferences and topic in preferences.boost_topics:
            preferences.boost_topics.remove(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def add_suppress_topic(self, db: AsyncSession, namespace: str, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, namespace)
        
        if not preferences:
            return await self.create_preferences(db, namespace, suppress_topics=[topic])
        
        if topic not in preferences.suppress_topics:
            preferences.suppress_topics.append(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def remove_suppress_topic(self, db: AsyncSession, namespace: str, topic: str) -> UserPreference:
        preferences = await self.get_preferences(db, namespace)
        
        if preferences and topic in preferences.suppress_topics:
            preferences.suppress_topics.remove(topic)
            preferences.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(preferences)
        
        return preferences

preferences_service = PreferencesService()
