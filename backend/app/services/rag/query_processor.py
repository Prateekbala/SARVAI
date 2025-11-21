from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

class QueryProcessor:
    
    INTENT_PATTERNS = {
        "factual": [
            r"^(what|when|where|who|which|how many|how much)",
            r"(definition|meaning|explain|describe)",
            r"(is|are|was|were|does|did|can|will)"
        ],
        "search": [
            r"(find|search|look for|show me)",
            r"(about|regarding|related to)",
            r"(tell me|give me information)"
        ],
        "conversational": [
            r"(hi|hello|hey|thanks|thank you)",
            r"(how are you|what can you do)",
            r"(help|assist)"
        ]
    }
    
    def classify_intent(self, query: str) -> str:
        query_lower = query.lower().strip()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    logger.debug(f"Classified intent: {intent}")
                    return intent
        
        return "factual"
    
    def should_search_web(self, query: str, local_results_count: int = 0) -> bool:
        intent = self.classify_intent(query)
        
        if intent == "conversational":
            return False
        
        if local_results_count < 2:
            return True
        
        recency_keywords = [
            "latest", "recent", "current", "today", "now", "2024", "2025",
            "news", "update", "breaking"
        ]
        
        query_lower = query.lower()
        for keyword in recency_keywords:
            if keyword in query_lower:
                logger.info(f"Web search triggered by recency keyword: {keyword}")
                return True
        
        return False
    
    def rewrite_query(self, query: str, conversation_history: Optional[List[Dict]] = None) -> List[str]:
        queries = [query]
        
        if conversation_history and len(conversation_history) > 0:
            last_message = conversation_history[-1]
            if last_message.get("role") == "user":
                context = last_message.get("content", "")
                if len(context) > 0 and context.lower() not in query.lower():
                    expanded = f"{context} {query}"
                    queries.append(expanded)
        
        synonyms = self._generate_synonyms(query)
        queries.extend(synonyms)
        
        return queries[:3]
    
    def _generate_synonyms(self, query: str) -> List[str]:
        synonym_map = {
            "find": "search",
            "look for": "find",
            "information": "details",
            "explain": "describe",
            "how to": "instructions for",
            "document": "file",
            "image": "picture",
            "audio": "recording"
        }
        
        query_lower = query.lower()
        synonyms = []
        
        for original, replacement in synonym_map.items():
            if original in query_lower:
                new_query = query_lower.replace(original, replacement)
                if new_query != query_lower:
                    synonyms.append(new_query)
        
        return synonyms[:2]
    
    def extract_keywords(self, query: str) -> List[str]:
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "can", "could", "may", "might", "must", "shall", "to", "of", "in",
            "for", "on", "at", "by", "with", "from", "about", "as", "into",
            "through", "during", "before", "after", "above", "below", "between",
            "under", "i", "me", "my", "you", "your", "it", "its", "what", "which"
        }
        
        words = re.findall(r'\w+', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def process(self, query: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        return {
            "original_query": query,
            "intent": self.classify_intent(query),
            "rewritten_queries": self.rewrite_query(query, conversation_history),
            "keywords": self.extract_keywords(query),
            "should_search_web": self.should_search_web(query, 0)
        }

query_processor = QueryProcessor()
