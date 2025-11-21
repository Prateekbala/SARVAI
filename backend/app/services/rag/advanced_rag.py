"""
Advanced RAG with query decomposition and multi-hop reasoning
Inspired by M³-Agent's reasoning capabilities
"""

from typing import List, Dict, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import re

from app.services.embeddings.embedding_service import embedding_service
from app.services.memory.memory_manager import memory_manager
from app.services.rag.context_builder import context_builder
from app.services.rag.generator import llm_generator

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyze and decompose complex queries into sub-queries
    Determines query complexity and retrieval strategy
    """
    
    @staticmethod
    def analyze_query(query: str) -> Dict:
        """
        Analyze query characteristics:
        - Complexity (simple vs. multi-hop)
        - Temporal references
        - Question type
        - Required reasoning
        """
        query_lower = query.lower()
        
        # Detect temporal references
        temporal_markers = [
            "recent", "yesterday", "last week", "today",
            "when", "latest", "newest", "oldest", "first"
        ]
        has_temporal = any(marker in query_lower for marker in temporal_markers)
        
        # Detect multi-hop indicators
        multi_hop_indicators = [
            "and then", "after that", "compare", "difference between",
            "relationship", "connection", "how does", "why did",
            "explain the process", "step by step"
        ]
        is_complex = any(indicator in query_lower for indicator in multi_hop_indicators)
        
        # Detect question type
        question_words = {
            "what": "factual",
            "who": "entity",
            "where": "location",
            "when": "temporal",
            "why": "causal",
            "how": "procedural",
            "which": "choice"
        }
        
        question_type = "unknown"
        for word, qtype in question_words.items():
            if query_lower.startswith(word):
                question_type = qtype
                break
        
        # Detect comparison requests
        is_comparison = any(
            word in query_lower
            for word in ["compare", "difference", "versus", "vs", "better", "worse"]
        )
        
        return {
            "has_temporal": has_temporal,
            "is_complex": is_complex,
            "is_comparison": is_comparison,
            "question_type": question_type,
            "requires_multi_hop": is_complex or is_comparison,
            "tokens": len(query.split())
        }
    
    @staticmethod
    async def decompose_query(query: str) -> List[str]:
        """
        Decompose complex query into simpler sub-queries
        Uses LLM for intelligent decomposition
        """
        analysis = QueryAnalyzer.analyze_query(query)
        
        if not analysis["requires_multi_hop"]:
            return [query]
        
        # Use LLM to decompose
        decomposition_prompt = [{
            "role": "system",
            "content": """You are a query decomposition expert. Break down complex questions into 2-4 simpler sub-questions.
Each sub-question should be answerable independently.
Output only the sub-questions, one per line, numbered."""
        }, {
            "role": "user",
            "content": f"Decompose this question:\n{query}"
        }]
        
        try:
            response = await llm_generator.generate(
                decomposition_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse numbered sub-queries
            sub_queries = []
            for line in response.split('\n'):
                line = line.strip()
                # Remove numbers and bullets
                line = re.sub(r'^\d+[\.)]\s*', '', line)
                line = re.sub(r'^[-•]\s*', '', line)
                
                if line and len(line) > 10:
                    sub_queries.append(line)
            
            if sub_queries:
                logger.info(f"Decomposed query into {len(sub_queries)} sub-queries")
                return sub_queries
            else:
                return [query]
                
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return [query]


class TemporalRetriever:
    """
    Temporal-aware retrieval with recency bias
    Implements time-weighted scoring
    """
    
    @staticmethod
    def apply_temporal_boost(
        results: List[Dict],
        recency_weight: float = 0.3,
        temporal_query: bool = False
    ) -> List[Dict]:
        """
        Apply temporal boost to search results
        More recent memories get higher scores
        """
        from datetime import datetime
        import numpy as np
        
        now = datetime.utcnow()
        
        for result in results:
            created_at = result.get("created_at", now)
            
            # Calculate recency score (exponential decay)
            age_days = (now - created_at).days
            recency_score = np.exp(-age_days / 30.0)  # 30-day half-life
            
            # Boost for very recent memories if temporal query
            if temporal_query and age_days < 7:
                recency_score *= 1.5
            
            # Original similarity score
            similarity = result.get("similarity", 0.0)
            
            # Combine with weighted sum
            boosted_score = (
                (1 - recency_weight) * similarity +
                recency_weight * recency_score
            )
            
            result["temporal_score"] = recency_score
            result["original_similarity"] = similarity
            result["boosted_score"] = boosted_score
        
        # Re-sort by boosted score
        results.sort(key=lambda x: x["boosted_score"], reverse=True)
        
        logger.debug(f"Applied temporal boost (weight={recency_weight})")
        return results


class MultiHopRAG:
    """
    Advanced RAG system with:
    - Query decomposition
    - Multi-hop reasoning
    - Temporal awareness
    - Answer synthesis
    """
    
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.temporal_retriever = TemporalRetriever()
    
    async def answer_query(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        enable_web: bool = False,
        stream: bool = False
    ) -> Dict:
        """
        Answer query with advanced RAG pipeline
        """
        # Step 1: Analyze query
        analysis = self.query_analyzer.analyze_query(query)
        logger.info(f"Query analysis: {analysis}")
        
        # Step 2: Decompose if complex
        sub_queries = [query]
        if analysis["requires_multi_hop"]:
            sub_queries = await self.query_analyzer.decompose_query(query)
        
        # Step 3: Retrieve for each sub-query
        all_results = []
        for sub_query in sub_queries:
            query_embedding = await embedding_service.embed_text(sub_query)
            
            # Use hierarchical memory retrieval
            results = await memory_manager.retrieve_with_hierarchy(
                db=db,
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=5,
                include_summaries=True
            )
            
            # Apply temporal boost if temporal query
            if analysis["has_temporal"]:
                results = self.temporal_retriever.apply_temporal_boost(
                    results,
                    recency_weight=0.4,
                    temporal_query=True
                )
            
            all_results.extend(results)
        
        # Step 4: Deduplicate and rank
        seen_ids = set()
        unique_results = []
        for result in all_results:
            memory_id = result.get("memory_id")
            if memory_id not in seen_ids:
                seen_ids.add(memory_id)
                unique_results.append(result)
        
        # Sort by best score
        score_key = "boosted_score" if analysis["has_temporal"] else "similarity"
        unique_results.sort(key=lambda x: x.get(score_key, 0), reverse=True)
        unique_results = unique_results[:10]
        
        # Step 5: Build context
        context = context_builder.build_context(
            unique_results,
            include_metadata=True
        )
        
        # Step 6: Generate answer
        system_prompt = self._create_system_prompt(analysis, len(sub_queries) > 1)
        
        messages = context_builder.build_prompt(
            query=query,
            context=context,
            conversation_history=conversation_history,
            system_prompt=system_prompt
        )
        
        if stream:
            # Return streaming response
            return {
                "stream": llm_generator.generate_stream(messages),
                "analysis": analysis,
                "sub_queries": sub_queries,
                "results": unique_results
            }
        else:
            answer = await llm_generator.generate(messages)
            
            # Extract sources
            sources = context_builder.extract_sources(answer, unique_results)
            
            # Record memory accesses
            for result in unique_results[:5]:  # Top 5 results
                await memory_manager.record_memory_access(
                    db=db,
                    memory_id=result["memory_id"],
                    access_type="retrieval"
                )
            
            return {
                "answer": answer,
                "sources": sources,
                "analysis": analysis,
                "sub_queries": sub_queries,
                "results": unique_results
            }
    
    def _create_system_prompt(
        self,
        analysis: Dict,
        is_multi_hop: bool
    ) -> str:
        """Create appropriate system prompt based on query analysis"""
        
        base_prompt = """You are a helpful AI assistant with access to the user's personal memory.
Answer questions based on the provided context."""
        
        if is_multi_hop:
            base_prompt += """
This is a complex question that may require synthesizing information from multiple sources.
Break down your reasoning step by step."""
        
        if analysis["has_temporal"]:
            base_prompt += """
Pay special attention to temporal information and recency of sources."""
        
        if analysis["is_comparison"]:
            base_prompt += """
Structure your answer to clearly compare and contrast the relevant items."""
        
        base_prompt += """

Always cite your sources using [Source N] notation.
If the context doesn't contain relevant information, say so clearly."""
        
        return base_prompt


multi_hop_rag = MultiHopRAG()
