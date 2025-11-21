from typing import List, Dict, Optional
import tiktoken
import logging

logger = logging.getLogger(__name__)

class ContextBuilder:
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 4096):
        self.model = model
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
    def count_tokens(self, text: str) -> int:
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using character approximation")
            return len(text) // 4
    
    def build_context(
        self,
        results: List[Dict],
        max_context_tokens: Optional[int] = None,
        include_metadata: bool = True
    ) -> str:
        max_tokens = max_context_tokens or (self.max_tokens // 2)
        
        context_parts = []
        current_tokens = 0
        
        seen_content = set()
        
        for i, result in enumerate(results):
            chunk_text = result.get("chunk_text", "")
            
            if not chunk_text or chunk_text in seen_content:
                continue
            
            seen_content.add(chunk_text)
            
            context_block = self._format_result(result, i + 1, include_metadata)
            block_tokens = self.count_tokens(context_block)
            
            if current_tokens + block_tokens > max_tokens:
                logger.info(f"Context limit reached at {i+1}/{len(results)} results")
                break
            
            context_parts.append(context_block)
            current_tokens += block_tokens
        
        if not context_parts:
            logger.warning("No context built from results")
            return ""
        
        context = "\n\n---\n\n".join(context_parts)
        logger.info(f"Built context with {len(context_parts)} chunks, ~{current_tokens} tokens")
        
        return context
    
    def _format_result(self, result: Dict, index: int, include_metadata: bool) -> str:
        lines = [f"[Source {index}]"]
        
        content_type = result.get("content_type", "unknown")
        lines.append(f"Type: {content_type}")
        
        if include_metadata:
            metadata = result.get("metadata", {})
            
            if content_type == "image" and metadata.get("has_text"):
                lines.append("Content: Image with extracted text")
            elif content_type == "pdf":
                page_count = metadata.get("page_count", "unknown")
                lines.append(f"Pages: {page_count}")
            elif content_type == "audio":
                duration = metadata.get("duration_seconds", 0)
                lines.append(f"Duration: {duration:.1f}s")
        
        chunk_text = result.get("chunk_text", "").strip()
        lines.append(f"\nContent:\n{chunk_text}")
        
        return "\n".join(lines)
    
    def build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        messages = []
        
        if not system_prompt:
            system_prompt = """You are a helpful AI assistant with access to the user's personal memory.
Answer questions based on the provided context. If the context doesn't contain relevant information, say so clearly.
Always cite your sources using [Source N] notation."""
        
        messages.append({"role": "system", "content": system_prompt})
        
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    messages.append({"role": role, "content": content})
        
        if context:
            context_message = f"""Here is relevant information from the user's memory:

{context}

Please answer the following question based on this information."""
            messages.append({"role": "system", "content": context_message})
        else:
            messages.append({
                "role": "system",
                "content": "No relevant information found in user's memory. Provide a helpful response based on your general knowledge."
            })
        
        messages.append({"role": "user", "content": query})
        
        total_tokens = sum(self.count_tokens(m["content"]) for m in messages)
        logger.info(f"Built prompt with {len(messages)} messages, ~{total_tokens} tokens")
        
        return messages
    
    def extract_sources(self, response: str, results: List[Dict]) -> List[Dict]:
        import re
        
        source_pattern = r'\[Source (\d+)\]'
        cited_indices = set()
        
        for match in re.finditer(source_pattern, response):
            index = int(match.group(1)) - 1
            cited_indices.add(index)
        
        sources = []
        for idx in sorted(cited_indices):
            if 0 <= idx < len(results):
                result = results[idx]
                sources.append({
                    "memory_id": str(result.get("memory_id")),
                    "content_type": result.get("content_type"),
                    "snippet": result.get("chunk_text", "")[:200],
                    "similarity": result.get("similarity") or result.get("hybrid_score", 0)
                })
        
        return sources

context_builder = ContextBuilder()
