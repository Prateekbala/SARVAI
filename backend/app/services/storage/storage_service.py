from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.models import User, Memory, Embedding
from app.services.embeddings.embedding_service import embedding_service
from app.services.embeddings.qdrant_manager import qdrant_manager
import logging

logger = logging.getLogger(__name__)

class StorageService:
    
    async def create_user(self, db: AsyncSession, namespace: str) -> User:
        """Create a new user with namespace only"""
        try:
            # Create user
            user = User(namespace=namespace)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"User created: {user.namespace}")
            return user
        except Exception as e:
            await db.rollback()
            logger.error(f"User creation failed: {e}")
            raise
    
    async def get_user_by_namespace(self, db: AsyncSession, namespace: str) -> Optional[User]:
        """Get user by namespace"""
        result = await db.execute(select(User).where(User.namespace == namespace))
        return result.scalar_one_or_none()
    
    async def create_memory(
        self,
        db: AsyncSession,
        namespace: str,
        content_type: str,
        content: str,
        chunks: List[Dict[str, Any]],  # Changed from List[str] to support pre-computed embeddings
        meta_data: Dict[str, Any] = None,  # Renamed from metadata
        file_path: Optional[str] = None
    ) -> Memory:
        """
        Create a memory with embeddings stored in Qdrant
        
        Args:
            db: Database session
            namespace: User namespace
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
            # Determine Qdrant collection based on content type
            if content_type in ["image"]:
                collection_name = "clip_embeddings"
            else:  # text, pdf, audio all use text embeddings
                collection_name = "text_embeddings"
            
            # Create memory
            memory = Memory(
                namespace=namespace,
                content_type=content_type,
                content=content,
                meta_data=meta_data or {},
                file_path=file_path
            )
            db.add(memory)
            await db.flush()  # Get memory ID without committing
            
            # Process chunks and embeddings
            # Separate chunks into text chunks that need embedding and pre-computed chunks
            text_chunks_to_embed = []
            text_chunk_indices = []
            pre_computed_chunks = {}
            
            for idx, chunk in enumerate(chunks):
                if isinstance(chunk, dict):
                    # Pre-computed embedding (e.g., CLIP for images)
                    pre_computed_chunks[idx] = {
                        "text": chunk.get("text", ""),
                        "embedding": chunk.get("embedding")
                    }
                else:
                    # Text chunk - will generate embedding
                    chunk_text = str(chunk).strip()
                    if chunk_text:  # Only add non-empty chunks
                        text_chunks_to_embed.append(chunk_text)
                        text_chunk_indices.append(idx)
            
            # Batch embed all text chunks at once
            text_embeddings = {}
            if text_chunks_to_embed:
                embeddings_data = await embedding_service.embed_batch(text_chunks_to_embed)
                for chunk_idx, embedding in zip(text_chunk_indices, embeddings_data):
                    text_embeddings[chunk_idx] = embedding
            
            # Prepare data for Qdrant storage
            embeddings_for_qdrant = []
            chunk_texts_for_qdrant = []
            embedding_objects = []
            
            for idx, chunk in enumerate(chunks):
                if idx in pre_computed_chunks:
                    chunk_data = pre_computed_chunks[idx]
                    chunk_text = chunk_data["text"]
                    embedding = chunk_data["embedding"]
                elif idx in text_embeddings:
                    chunk_text = text_chunks_to_embed[text_chunk_indices.index(idx)]
                    embedding = text_embeddings[idx]
                else:
                    # Skip empty chunks
                    logger.warning(f"Skipping empty chunk at index {idx}")
                    continue
                
                if not embedding:
                    logger.warning(f"No embedding for chunk {idx}, skipping")
                    continue
                
                embeddings_for_qdrant.append(embedding)
                chunk_texts_for_qdrant.append(chunk_text)
                
                # Create embedding object for PostgreSQL (metadata only)
                embedding_obj = Embedding(
                    memory_id=memory.id,
                    chunk_text=chunk_text,
                    chunk_index=idx,
                    qdrant_point_id=""  # Will be set after Qdrant upsert
                )
                embedding_objects.append(embedding_obj)
            
            # Store embeddings in Qdrant
            if embeddings_for_qdrant:
                qdrant_point_ids = await embedding_service.store_in_qdrant(
                    collection_name=collection_name,
                    embeddings=embeddings_for_qdrant,
                    namespace=namespace,
                    memory_id=str(memory.id),
                    chunk_texts=chunk_texts_for_qdrant,
                    content_type=content_type
                )
                
                # Update embedding objects with Qdrant point IDs
                for embedding_obj, point_id in zip(embedding_objects, qdrant_point_ids):
                    embedding_obj.qdrant_point_id = point_id
            
            # Add embedding objects to database
            for embedding_obj in embedding_objects:
                db.add(embedding_obj)
            
            await db.commit()
            await db.refresh(memory)
            
            logger.info(f"Memory created: {memory.id} with {len(chunk_texts_for_qdrant)} chunks in Qdrant")
            return memory
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Memory creation failed: {e}")
            raise
    
    async def search_memories(
        self,
        db: AsyncSession,
        namespace: str,
        query_embedding: List[float],
        top_k: int = 5,
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories using vector similarity via Qdrant
        
        Args:
            db: Database session
            namespace: User namespace
            query_embedding: Query embedding vector
            top_k: Number of results to return
            content_type: Optional filter by content type
            
        Returns:
            List of search results with similarity scores
        """
        try:
            # Determine which collection to search
            if content_type == "image":
                collection_name = "clip_embeddings"
            else:
                collection_name = "text_embeddings"
            
            # Search in Qdrant
            qdrant_results = await embedding_service.search_qdrant(
                collection_name=collection_name,
                query_embedding=query_embedding,
                namespace=namespace,
                content_type=content_type,
                top_k=top_k
            )
            
            if not qdrant_results:
                logger.info(f"No results found in Qdrant for namespace {namespace}")
                return []
            
            # Enrich results with database metadata
            results = []
            for result in qdrant_results:
                try:
                    memory_id = result["payload"].get("memory_id")
                    
                    # Get memory from database for additional metadata
                    query = select(Memory).where(
                        Memory.id == UUID(memory_id),
                        Memory.namespace == namespace
                    )
                    db_result = await db.execute(query)
                    memory = db_result.scalar_one_or_none()
                    
                    if memory:
                        results.append({
                            "memory_id": memory_id,
                            "content_type": memory.content_type,
                            "chunk_text": result["payload"].get("chunk_text", ""),
                            "chunk_index": result["payload"].get("chunk_index", 0),
                            "similarity_score": float(result["similarity_score"]),
                            "metadata": memory.meta_data or {},
                            "created_at": memory.created_at
                        })
                except Exception as e:
                    logger.warning(f"Failed to enrich result: {e}")
                    continue
            
            logger.info(f"Found {len(results)} enriched results for namespace {namespace}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def get_memories(
        self,
        db: AsyncSession,
        namespace: str,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Memory], int]:
        """Get paginated memories for a user"""
        try:
            # Get total count
            count_query = select(func.count(Memory.id)).where(Memory.namespace == namespace)
            total = await db.scalar(count_query)
            
            # Get memories
            query = (
                select(Memory)
                .where(Memory.namespace == namespace)
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
        namespace: str,
        memory_id: UUID
    ) -> bool:
        """Delete a memory and its embeddings from both PostgreSQL and Qdrant"""
        try:
            # Check if memory exists and belongs to user
            query = select(Memory).where(
                Memory.id == memory_id,
                Memory.namespace == namespace
            )
            result = await db.execute(query)
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete embeddings from Qdrant (both collections, only one will have data)
            try:
                qdrant_manager.delete_by_memory_id("text_embeddings", str(memory_id))
            except:
                pass  # Collection might not have this memory
            
            try:
                qdrant_manager.delete_by_memory_id("clip_embeddings", str(memory_id))
            except:
                pass  # Collection might not have this memory
            
            # Delete memory from PostgreSQL (cascades to embeddings table)
            await db.delete(memory)
            await db.commit()
            
            logger.info(f"Memory deleted: {memory_id} (from both PostgreSQL and Qdrant)")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Delete memory failed: {e}")
            raise

# Global instance
storage_service = StorageService()