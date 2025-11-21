from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.models import User, Memory, Embedding
from app.services.embeddings.embedding_service import embedding_service
from app.services.auth.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)

class StorageService:
    
    async def create_user(self, db: AsyncSession, email: str, password: str) -> User:
        """Create a new user with email and password"""
        try:
            # Hash the password
            password_hash = auth_service.hash_password(password)
            
            # Create user
            user = User(email=email, password_hash=password_hash)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"User created: {user.id} ({email})")
            return user
        except Exception as e:
            await db.rollback()
            logger.error(f"User creation failed: {e}")
            raise
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(db, email)
        
        if not user or not user.password_hash:
            return None
        
        if not auth_service.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def create_memory(
        self,
        db: AsyncSession,
        user_id: UUID,
        content_type: str,
        content: str,
        chunks: List[Dict[str, Any]],  # Changed from List[str] to support pre-computed embeddings
        meta_data: Dict[str, Any] = None,  # Renamed from metadata
        file_path: Optional[str] = None
    ) -> Memory:
        """
        Create a memory with embeddings
        
        Args:
            db: Database session
            user_id: User ID
            content_type: Type of content ('text', 'image', 'pdf', 'audio')
            content: Full content text
            chunks: List of chunks. Each chunk can be:
                    - A string (for text) - will generate embedding
                    - A dict with 'text' and 'embedding' keys (pre-computed)
            metadata: Optional metadata
            file_path: Optional file path in MinIO
            
        Returns:
            Created Memory object
        """
        try:
            # Create memory
            memory = Memory(
                user_id=user_id,
                content_type=content_type,
                content=content,
                meta_data=meta_data or {},
                file_path=file_path
            )
            db.add(memory)
            await db.flush()  # Get memory ID without committing
            
            # Process chunks and embeddings
            for idx, chunk in enumerate(chunks):
                if isinstance(chunk, dict):
                    # Pre-computed embedding (e.g., CLIP for images)
                    chunk_text = chunk.get("text", "")
                    embedding = chunk.get("embedding")
                else:
                    # Text chunk - generate embedding
                    chunk_text = chunk
                    embeddings_data = await embedding_service.embed_batch([chunk_text])
                    embedding = embeddings_data[0]
                
                embedding_obj = Embedding(
                    memory_id=memory.id,
                    embedding=embedding,
                    chunk_text=chunk_text,
                    chunk_index=idx
                )
                db.add(embedding_obj)
            
            await db.commit()
            await db.refresh(memory)
            
            logger.info(f"Memory created: {memory.id} with {len(chunks)} chunks")
            return memory
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Memory creation failed: {e}")
            raise
    
    async def search_memories(
        self,
        db: AsyncSession,
        user_id: UUID,
        query_embedding: List[float],
        top_k: int = 5,
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories using vector similarity
        
        Args:
            db: Database session
            user_id: User ID
            query_embedding: Query embedding vector
            top_k: Number of results to return
            content_type: Optional filter by content type
            
        Returns:
            List of search results with similarity scores
        """
        try:
            # Build query
            query = (
                select(
                    Embedding,
                    Memory,
                    Embedding.embedding.cosine_distance(query_embedding).label("distance")
                )
                .join(Memory, Embedding.memory_id == Memory.id)
                .where(Memory.user_id == user_id)
            )
            
            # Add content type filter if specified
            if content_type:
                query = query.where(Memory.content_type == content_type)
            
            # Order by similarity and limit
            query = query.order_by("distance").limit(top_k)
            
            result = await db.execute(query)
            rows = result.all()
            
            # Format results
            results = []
            for embedding, memory, distance in rows:
                results.append({
                    "memory_id": memory.id,
                    "content_type": memory.content_type,
                    "chunk_text": embedding.chunk_text,
                    "similarity_score": float(1 - distance),  # Convert distance to similarity
                    "metadata": memory.meta_data or {},  # Rename to match schema
                    "created_at": memory.created_at
                })
            
            logger.info(f"Found {len(results)} results for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def get_memories(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Memory], int]:
        """Get paginated memories for a user"""
        try:
            # Get total count
            count_query = select(func.count(Memory.id)).where(Memory.user_id == user_id)
            total = await db.scalar(count_query)
            
            # Get memories
            query = (
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            memories = result.scalars().all()
            
            return list(memories), total
            
        except Exception as e:
            logger.error(f"Get memories failed: {e}")
            raise
    
    async def delete_memory(
        self,
        db: AsyncSession,
        user_id: UUID,
        memory_id: UUID
    ) -> bool:
        """Delete a memory and its embeddings"""
        try:
            # Check if memory exists and belongs to user
            query = select(Memory).where(
                Memory.id == memory_id,
                Memory.user_id == user_id
            )
            result = await db.execute(query)
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete memory (cascades to embeddings)
            await db.delete(memory)
            await db.commit()
            
            logger.info(f"Memory deleted: {memory_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Delete memory failed: {e}")
            raise

# Global instance
storage_service = StorageService()