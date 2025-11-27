from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# User Schemas
class UserCreate(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255, description="Unique namespace identifier")

class UserLogin(BaseModel):
    namespace: str = Field(..., min_length=1, description="Namespace identifier")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    namespace: str

class UserResponse(BaseModel):
    namespace: str
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
    namespace: str
    content_type: str
    content: Optional[str]
    metadata: Dict[str, Any]
    file_path: Optional[str]
    created_at: datetime
    
    # OCR and Layout data
    ocr_text: Optional[str] = None
    layout_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, memory):
        """Convert database model to response schema"""
        return cls(
            id=memory.id,
            namespace=memory.namespace,
            content_type=memory.content_type,
            content=memory.content,
            metadata=memory.meta_data or {},  # Convert meta_data to metadata
            file_path=memory.file_path,
            created_at=memory.created_at,
            ocr_text=memory.ocr_text,
            layout_data=memory.layout_data
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
    
    # Re-ranking and Hybrid search scores
    bm25_score: Optional[float] = None
    re_ranking_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    rank: Optional[int] = None

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
    namespace: str
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
    namespace: str
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


# OCR and Advanced Processing Schemas
class OCRResultBBox(BaseModel):
    points: List[List[float]]
    text: str
    confidence: float

class OCRResultParagraph(BaseModel):
    text: str
    confidence: float
    bboxes: List[OCRResultBBox]

class OCRPageResult(BaseModel):
    page_number: int
    text: str
    confidence: float
    paragraphs: List[OCRResultParagraph]
    layout: Dict[str, Any] = {}
    bboxes: List[OCRResultBBox] = []

class PDFExtractionResult(BaseModel):
    full_text: str
    num_chunks: int
    token_count: int
    metadata: Dict[str, Any]
    extraction_methods: List[str]
    layout_data: List[Dict[str, Any]]
    ocr_results: List[Dict[str, Any]]

# Re-ranking Schemas
class RerankedResult(BaseModel):
    id: str
    text: str
    score: float
    rank: int

class RerankerResponse(BaseModel):
    query: str
    results: List[RerankedResult]
    total_results: int

# Advanced Search Schemas
class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)
    content_type: Optional[str] = None
    fusion_method: str = Field(default="weighted", description="'weighted' or 'rrf'")
    use_reranking: bool = Field(default=True, description="Use Cross-Encoder re-ranking")

class AdvancedSearchResult(BaseModel):
    memory_id: UUID
    content_type: str
    chunk_text: str
    vector_similarity: float
    bm25_score: Optional[float] = None
    re_ranking_score: Optional[float] = None
    hybrid_score: float
    rank: int
    metadata: Dict[str, Any]
    created_at: datetime

class AdvancedSearchResponse(BaseModel):
    results: List[AdvancedSearchResult]
    query: str
    total_results: int
    fusion_method: str
    reranking_used: bool