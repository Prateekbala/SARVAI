from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID

class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Memory Schemas
class TextMemoryRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text content to remember")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ImageMemoryRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PDFMemoryRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AudioMemoryRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MemoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    content_type: str
    content: Optional[str]
    metadata: Dict[str, Any]
    file_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, memory):
        """Convert database model to response schema"""
        return cls(
            id=memory.id,
            user_id=memory.user_id,
            content_type=memory.content_type,
            content=memory.content,
            metadata=memory.meta_data or {},  # Convert meta_data to metadata
            file_path=memory.file_path,
            created_at=memory.created_at
        )

class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int
    page: int
    page_size: int

# Search Schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    content_type: Optional[str] = None

class SearchResult(BaseModel):
    memory_id: UUID
    content_type: str
    chunk_text: str
    similarity_score: float
    metadata: Dict[str, Any]
    created_at: datetime

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int

# Generic Response
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to ask")
    conversation_id: Optional[UUID] = None
    enable_web_search: bool = Field(default=False, description="Enable web search fallback")
    top_k: int = Field(default=5, ge=1, le=20)

class Source(BaseModel):
    memory_id: Optional[str] = None
    content_type: str
    snippet: str
    similarity: float
    url: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    conversation_id: UUID
    web_search_used: bool = False

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse]

class WebSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    num_results: int = Field(default=5, ge=1, le=10)

class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    content: Optional[str] = None

class WebSearchResponse(BaseModel):
    results: List[WebSearchResult]
    query: str
    cached: int = 0
    scraped: int = 0

# User Preferences Schemas
class PreferencesUpdate(BaseModel):
    boost_topics: Optional[List[str]] = None
    suppress_topics: Optional[List[str]] = None
    search_preferences: Optional[Dict[str, Any]] = None

class PreferencesResponse(BaseModel):
    id: UUID
    user_id: UUID
    boost_topics: List[str]
    suppress_topics: List[str]
    search_preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Analytics Schemas
class UserStatsResponse(BaseModel):
    total_memories: int
    memories_by_type: Dict[str, int]
    total_conversations: int
    total_messages: int
    recent_activity: Dict[str, int]
    storage_info: Dict[str, Any]

class TimelineMemory(BaseModel):
    id: str
    content_type: str
    content_preview: Optional[str]
    file_path: Optional[str]
    metadata: Dict[str, Any]
    created_at: str

class TimelineGroup(BaseModel):
    date: str
    memories: List[TimelineMemory]

class TimelineResponse(BaseModel):
    timeline: List[TimelineGroup]
    total_items: int

class PopularSearch(BaseModel):
    query: str
    count: int

class PopularSearchesResponse(BaseModel):
    searches: List[PopularSearch]