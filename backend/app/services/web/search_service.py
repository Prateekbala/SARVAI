from typing import List, Dict, Optional
import httpx
import logging
from bs4 import BeautifulSoup
import json

from app.config import settings

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.brave_api_key = settings.BRAVE_API_KEY
        self.serp_api_key = settings.SERP_API_KEY
        self.timeout = settings.WEB_SCRAPE_TIMEOUT
        self.max_results = settings.WEB_SEARCH_RESULTS
        
    async def search(
        self,
        query: str,
        num_results: Optional[int] = None,
        search_type: str = "web"
    ) -> List[Dict]:
        num_results = num_results or self.max_results
        
        if self.brave_api_key:
            try:
                return await self._search_brave(query, num_results, search_type)
            except Exception as e:
                logger.warning(f"Brave Search failed: {e}, trying fallback")
        
        if self.serp_api_key:
            try:
                return await self._search_serpapi(query, num_results)
            except Exception as e:
                logger.warning(f"SerpAPI failed: {e}, trying fallback")
        
        try:
            return await self._search_duckduckgo(query, num_results)
        except Exception as e:
            logger.error(f"All search methods failed: {e}")
            return []
    
    async def _search_brave(
        self,
        query: str,
        num_results: int,
        search_type: str = "web"
    ) -> List[Dict]:
        url = "https://api.search.brave.com/res/v1/web/search"
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }
        
        params = {
            "q": query,
            "count": num_results,
            "text_decorations": False,
            "search_lang": "en"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("web", {}).get("results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
                "source": "brave"
            })
        
        logger.info(f"Brave Search: Found {len(results)} results")
        return results
    
    async def _search_serpapi(self, query: str, num_results: int) -> List[Dict]:
        url = "https://serpapi.com/search"
        
        params = {
            "q": query,
            "api_key": self.serp_api_key,
            "num": num_results,
            "engine": "google"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "serpapi"
            })
        
        logger.info(f"SerpAPI: Found {len(results)} results")
        return results
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        url = "https://html.duckduckgo.com/html/"
        
        params = {"q": query}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, data=params, headers=headers)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for result_div in soup.find_all('div', class_='result')[:num_results]:
            title_tag = result_div.find('a', class_='result__a')
            snippet_tag = result_div.find('a', class_='result__snippet')
            
            if title_tag and snippet_tag:
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": title_tag.get('href', ''),
                    "snippet": snippet_tag.get_text(strip=True),
                    "source": "duckduckgo"
                })
        
        logger.info(f"DuckDuckGo: Found {len(results)} results")
        return results
    
    async def search_and_rank(
        self,
        query: str,
        num_results: Optional[int] = None,
        filter_domains: Optional[List[str]] = None
    ) -> List[Dict]:
        results = await self.search(query, num_results)
        
        if filter_domains:
            results = [
                r for r in results 
                if not any(domain in r["url"] for domain in filter_domains)
            ]
        
        for i, result in enumerate(results):
            result["rank"] = i + 1
            result["query"] = query
        
        return results

web_search_service = WebSearchService()
