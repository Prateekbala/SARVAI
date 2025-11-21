from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.personalization.preferences_service import preferences_service
import logging

logger = logging.getLogger(__name__)

class ReRankingService:
    def __init__(self):
        self.boost_multiplier = 1.3
        self.suppress_multiplier = 0.7
    
    async def rerank_results(
        self,
        results: List[Dict[str, Any]],
        user_id: UUID,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        preferences = await preferences_service.get_preferences(db, user_id)
        
        if not preferences or (not preferences.boost_topics and not preferences.suppress_topics):
            return results
        
        boost_topics = [topic.lower() for topic in preferences.boost_topics]
        suppress_topics = [topic.lower() for topic in preferences.suppress_topics]
        
        reranked_results = []
        
        for result in results:
            score = result.get("similarity_score", 0.0)
            content = result.get("chunk_text", "").lower()
            metadata = result.get("metadata", {})
            
            content_lower = f"{content} {str(metadata)}".lower()
            
            boost_applied = False
            for topic in boost_topics:
                if topic in content_lower:
                    score *= self.boost_multiplier
                    boost_applied = True
                    break
            
            suppress_applied = False
            for topic in suppress_topics:
                if topic in content_lower:
                    score *= self.suppress_multiplier
                    suppress_applied = True
                    break
            
            result_copy = result.copy()
            result_copy["similarity_score"] = score
            result_copy["rerank_applied"] = boost_applied or suppress_applied
            
            reranked_results.append(result_copy)
        
        reranked_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"Re-ranked {len(reranked_results)} results for user {user_id}")
        
        return reranked_results
    
    def apply_preferences_to_query(
        self,
        query: str,
        boost_topics: List[str],
        suppress_topics: List[str]
    ) -> str:
        enhanced_query = query
        
        if boost_topics:
            enhanced_query += f" {' '.join(boost_topics)}"
        
        return enhanced_query

reranking_service = ReRankingService()
