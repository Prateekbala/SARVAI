from typing import List, Dict, Optional, AsyncGenerator
import httpx
import logging
import json
from app.config import settings

logger = logging.getLogger(__name__)

class LLMGenerator:
    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if stream:
                full_response = ""
                async for chunk in self.generate_stream(messages, temperature, max_tokens):
                    full_response += chunk
                return full_response
            else:
                return await self._generate_ollama(messages, temperature, max_tokens)
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_response(messages)
    
    async def _generate_ollama(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                return data.get("message", {}).get("content", "")
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_base_url}")
            raise Exception("Ollama service not available. Please ensure Ollama is running.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        url = f"{self.ollama_base_url}/api/chat"
        
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    yield content
                            
                            if data.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming response: {line}")
                            continue
                            
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_base_url}")
            yield "Error: Ollama service not available. Please ensure Ollama is running."
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        query = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        
        return f"""I apologize, but I'm unable to generate a response at the moment due to a technical issue.

Your question: {query}

Please ensure:
1. Ollama is running (run: ollama serve)
2. The model '{self.ollama_model}' is available (run: ollama pull {self.ollama_model})
3. Ollama is accessible at {self.ollama_base_url}

You can also try using a different model by updating the OLLAMA_MODEL in your .env file."""
    
    async def health_check(self) -> Dict[str, bool]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                model_available = any(m.get("name") == self.ollama_model for m in models)
                
                return {
                    "ollama_running": True,
                    "model_available": model_available,
                    "available_models": [m.get("name") for m in models]
                }
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "ollama_running": False,
                "model_available": False,
                "available_models": []
            }

llm_generator = LLMGenerator()
