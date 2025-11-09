from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr

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