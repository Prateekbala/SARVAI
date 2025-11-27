from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    namespace = Column(String(255), primary_key=True, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace = Column(String(255), ForeignKey("users.namespace"), nullable=False, index=True)
    content_type = Column(String(50), nullable=False)  # 'text', 'image', 'pdf', 'audio'
    content = Column(Text)
    meta_data = Column(JSONB, default={})  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # New columns for hierarchical memory
    memory_type = Column(String(50), default='episodic', index=True)  # 'episodic', 'semantic', 'procedural'
    importance_score = Column(Integer, default=50)  # 0-100 scale
    last_accessed = Column(DateTime, default=datetime.utcnow, index=True)
    
    # OCR and Layout Parsing
    ocr_text = Column(Text, nullable=True)  # Enhanced OCR extracted text
    layout_data = Column(JSONB, nullable=True)  # Layout structure and positioning data
    
    # Relationships
    user = relationship("User", back_populates="memories")
    embeddings = relationship("Embedding", back_populates="memory", cascade="all, delete-orphan")
    accesses = relationship("MemoryAccess", back_populates="memory", cascade="all, delete-orphan")

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=False, index=True)
    # embedding is now stored in Qdrant, not in PostgreSQL
    chunk_text = Column(Text)
    chunk_index = Column(Integer, default=0)
    # qdrant_point_id stores the ID of the point in Qdrant collection
    qdrant_point_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Re-ranking and BM25 scores
    bm25_score = Column(Integer, default=0, nullable=True)  # BM25 relevance score
    re_ranking_score = Column(Integer, default=0, nullable=True)  # Cross-Encoder re-ranking score
    
    # Relationships
    memory = relationship("Memory", back_populates="embeddings")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace = Column(String(255), ForeignKey("users.namespace"), nullable=False, index=True)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class WebSource(Base):
    __tablename__ = "web_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    title = Column(String(500))
    content = Column(Text)
    # embedding is now stored in Qdrant
    qdrant_point_id = Column(String(255), unique=True, nullable=True, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSONB, default={})

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace = Column(String(255), ForeignKey("users.namespace"), unique=True, nullable=False, index=True)
    boost_topics = Column(ARRAY(String), default=[])
    suppress_topics = Column(ARRAY(String), default=[])
    search_preferences = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")


class MemoryAccess(Base):
    """Track memory access patterns for importance calculation"""
    __tablename__ = "memory_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    access_type = Column(String(50), nullable=False)  # 'retrieval', 'edit', 'view'
    accessed_at = Column(DateTime, default=datetime.utcnow, index=True)
    meta_data = Column(JSONB, default={})
    
    memory = relationship("Memory", back_populates="accesses")


class MemorySummary(Base):
    """Consolidated semantic summaries of episodic memories"""
    __tablename__ = "memory_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace = Column(String(255), ForeignKey("users.namespace", ondelete="CASCADE"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    # summary_embedding is now stored in Qdrant
    qdrant_point_id = Column(String(255), unique=True, nullable=False, index=True)
    source_memory_ids = Column(ARRAY(String), nullable=False)  # Array of memory UUIDs
    memory_count = Column(Integer, nullable=False)
    date_range_start = Column(DateTime, nullable=False, index=True)
    date_range_end = Column(DateTime, nullable=False, index=True)
    importance_score = Column(Integer, default=50)  # 0-100 scale
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")