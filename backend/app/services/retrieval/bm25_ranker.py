from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import re
import logging

logger = logging.getLogger(__name__)

class BM25Ranker:
    def __init__(self):
        self.corpus_texts: List[str] = []
        self.corpus_ids: List[str] = []
        self.bm25: BM25Okapi = None
        self.is_fitted = False
        
    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return [t for t in text.split() if len(t) > 2]
    
    def fit(self, documents: List[Dict[str, str]]):
        if not documents:
            logger.warning("BM25: No documents")
            self.is_fitted = False
            return
            
        self.corpus_texts, self.corpus_ids = [], []
        for doc in documents:
            doc_id, text = doc.get("id", ""), doc.get("text", "")
            if text:
                self.corpus_texts.append(text)
                self.corpus_ids.append(doc_id)
        
        if not self.corpus_texts:
            logger.warning("BM25: No valid texts")
            self.is_fitted = False
            return
            
        tokenized = [self.tokenize(doc) for doc in self.corpus_texts]
        self.bm25 = BM25Okapi(tokenized)
        self.is_fitted = True
        logger.info(f"BM25: Fitted on {len(self.corpus_texts)} docs")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self.is_fitted or self.bm25 is None:
            return []
        
        tokenized = self.tokenize(query)
        if not tokenized:
            return []
        
        scores = self.bm25.get_scores(tokenized)
        doc_scores = sorted(zip(self.corpus_ids, scores), key=lambda x: x[1], reverse=True)
        
        return [(doc_id, float(score)) for doc_id, score in doc_scores[:top_k] if score > 0]
    
    def batch_search(self, queries: List[str], top_k: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        return {query: self.search(query, top_k) for query in queries}

bm25_ranker = BM25Ranker()
