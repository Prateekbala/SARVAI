from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.hybrid_search import hybrid_search_engine
from app.services.web.search_service import web_search_service
from app.services.web.scraper import web_scraper
from app.models.models import WebSource
from app.config import settings

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.min_similarity = settings.RAG_MIN_SIMILARITY
        
    async def retrieve(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        top_k: Optional[int] = None,
        content_type: Optional[str] = None,
        enable_web: bool = False
    ) -> Dict:
        top_k = top_k or self.top_k
        
        query_embedding = await embedding_service.embed_text(query)
        
        local_results = await hybrid_search_engine.search(
            db=db,
            user_id=user_id,
            query_embedding=query_embedding,
            query_text=query,
            top_k=top_k,
            content_type=content_type
        )
        
        filtered_results = [
            r for r in local_results 
            if r.get("similarity", 0) >= self.min_similarity or r.get("hybrid_score", 0) > 0
        ]
        
        logger.info(f"Local retrieval: {len(filtered_results)}/{len(local_results)} results above threshold")
        
        web_results = []
        if enable_web:
            try:
                web_results = await self._search_web(db, query, top_k=3)
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
        
        return {
            "local_results": filtered_results,
            "web_results": web_results,
            "total_results": len(filtered_results) + len(web_results)
        }
    
    async def _search_web(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        search_results = await web_search_service.search(query, num_results=top_k)
        
        if not search_results:
            logger.info("No web search results found")
            return []
        
        web_results = []
        
        for result in search_results:
            url = result.get("url", "")
            
            if not url:
                continue
            
            existing = await self._get_cached_web_source(db, url)
            
            if existing:
                web_results.append({
                    "chunk_text": existing.content,
                    "content_type": "web",
                    "metadata": {
                        "url": existing.url,
                        "title": existing.title,
                        "source": "web_cache"
                    },
                    "similarity": 0.0
                })
            else:
                scraped = await web_scraper.scrape_url(url)
                
                if scraped.get("content") and len(scraped["content"]) > 100:
                    try:
                        embedding = await embedding_service.embed_text(scraped["content"][:2000])
                        
                        await self._cache_web_source(
                            db=db,
                            url=url,
                            title=scraped.get("title"),
                            content=scraped["content"],
                            embedding=embedding
                        )
                        
                        web_results.append({
                            "chunk_text": scraped["content"][:1000],
                            "content_type": "web",
                            "metadata": {
                                "url": url,
                                "title": scraped.get("title"),
                                "source": "web_scraped"
                            },
                            "similarity": 0.0
                        })
                    except Exception as e:
                        logger.error(f"Failed to embed/cache web source: {e}")
        
        logger.info(f"Web retrieval: {len(web_results)} results")
        return web_results
    
    async def _get_cached_web_source(self, db: AsyncSession, url: str) -> Optional[WebSource]:
        from sqlalchemy import select
        
        result = await db.execute(
            select(WebSource).where(WebSource.url == url)
        )
        return result.scalar_one_or_none()
    
    async def _cache_web_source(
        self,
        db: AsyncSession,
        url: str,
        title: Optional[str],
        content: str,
        embedding: List[float]
    ):
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(WebSource).values(
            url=url,
            title=title,
            content=content,
            embedding=embedding,
            meta_data={"cached": True}
        ).on_conflict_do_nothing(index_elements=["url"])
        
        await db.execute(stmt)
        await db.commit()
        logger.debug(f"Cached web source: {url}")

retriever = Retriever()
