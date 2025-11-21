from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import re
from collections import defaultdict
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
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]
    
    def fit(self, documents: List[Dict[str, str]]):
        if not documents:
            logger.warning("BM25: No documents to fit")
            self.is_fitted = False
            return
            
        self.corpus_texts = []
        self.corpus_ids = []
        
        for doc in documents:
            doc_id = doc.get("id", "")
            text = doc.get("text", "")
            
            if text:
                self.corpus_texts.append(text)
                self.corpus_ids.append(doc_id)
        
        if not self.corpus_texts:
            logger.warning("BM25: No valid texts found")
            self.is_fitted = False
            return
            
        tokenized_corpus = [self.tokenize(doc) for doc in self.corpus_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.is_fitted = True
        logger.info(f"BM25: Fitted on {len(self.corpus_texts)} documents")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self.is_fitted or self.bm25 is None:
            logger.warning("BM25: Not fitted, returning empty results")
            return []
        
        tokenized_query = self.tokenize(query)
        
        if not tokenized_query:
            logger.warning("BM25: Empty query after tokenization")
            return []
        
        scores = self.bm25.get_scores(tokenized_query)
        
        doc_scores = list(zip(self.corpus_ids, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = [(doc_id, float(score)) for doc_id, score in doc_scores[:top_k] if score > 0]
        
        logger.debug(f"BM25: Found {len(results)} results for query")
        return results
    
    def batch_search(self, queries: List[str], top_k: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        results = {}
        for query in queries:
            results[query] = self.search(query, top_k)
        return results

bm25_ranker = BM25Ranker()
