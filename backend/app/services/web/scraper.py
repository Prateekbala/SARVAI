from typing import Optional, Dict
import httpx
import trafilatura
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.timeout = settings.WEB_SCRAPE_TIMEOUT
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def scrape_url(self, url: str) -> Dict[str, Optional[str]]:
        try:
            html = await self._fetch_html(url)
            
            if not html:
                logger.warning(f"Failed to fetch HTML from {url}")
                return {"url": url, "title": None, "content": None, "error": "Failed to fetch"}
            
            content = self._extract_content(html)
            title = self._extract_title(html)
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "domain": urlparse(url).netloc,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return {
                "url": url,
                "title": None,
                "content": None,
                "error": str(e)
            }
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} for {url}")
            return None
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            return None
    
    def _extract_content(self, html: str) -> Optional[str]:
        try:
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            
            if content and len(content.strip()) > 100:
                return content.strip()
            
            logger.warning("Trafilatura extraction failed or too short, trying BeautifulSoup fallback")
            return self._fallback_extract(html)
            
        except Exception as e:
            logger.warning(f"Content extraction error: {e}, trying fallback")
            return self._fallback_extract(html)
    
    def _fallback_extract(self, html: str) -> Optional[str]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            text_elements = []
            
            for tag in soup.find_all(['p', 'article', 'section', 'main']):
                text = tag.get_text(strip=True, separator=' ')
                if len(text) > 50:
                    text_elements.append(text)
            
            content = '\n\n'.join(text_elements)
            
            if len(content.strip()) > 100:
                return content.strip()
            
            return soup.get_text(strip=True, separator='\n')
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return None
    
    def _extract_title(self, html: str) -> Optional[str]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            title = soup.find('title')
            if title and title.string:
                return title.string.strip()
            
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                return og_title['content'].strip()
            
            h1 = soup.find('h1')
            if h1:
                return h1.get_text(strip=True)
            
            return None
            
        except Exception as e:
            logger.error(f"Title extraction failed: {e}")
            return None
    
    async def scrape_multiple(self, urls: list[str], max_concurrent: int = 3) -> list[Dict]:
        results = []
        
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *[self.scrape_url(url) for url in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch scraping error: {result}")
                    continue
                results.append(result)
        
        return results

import asyncio

web_scraper = WebScraper()
