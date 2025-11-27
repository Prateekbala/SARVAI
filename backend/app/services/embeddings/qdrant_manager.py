"""
Qdrant Vector Database Manager

Handles initialization and management of Qdrant collections for:
- Text embeddings
- Image embeddings (CLIP)
- Audio embeddings (Whisper transcripts)
- PDF chunk embeddings
"""

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manager for Qdrant vector database operations"""
    
    def __init__(self):
        """Initialize Qdrant client"""
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                timeout=30
            )
            logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
            self.is_connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.is_connected = False
            self.client = None
    
    async def initialize_collections(self):
        """Initialize all Qdrant collections if they don't exist"""
        if not self.is_connected:
            logger.error("Qdrant client not connected")
            return
        
        try:
            # Get list of existing collections
            collections = self.client.get_collections()
            existing_collection_names = [col.name for col in collections.collections]
            
            # Define collections to create
            collections_config = {
                "text_embeddings": {
                    "size": 384,  # sentence-transformers/all-MiniLM-L6-v2 dimension
                    "distance": Distance.COSINE,
                    "description": "Text embeddings from sentence transformers"
                },
                "clip_embeddings": {
                    "size": 512,  # CLIP model dimension
                    "distance": Distance.COSINE,
                    "description": "Image embeddings from CLIP model"
                },
                "web_source_embeddings": {
                    "size": 384,
                    "distance": Distance.COSINE,
                    "description": "Web source embeddings for RAG"
                }
            }
            
            # Create missing collections
            for collection_name, config in collections_config.items():
                if collection_name not in existing_collection_names:
                    logger.info(f"Creating collection: {collection_name}")
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config["size"],
                            distance=config["distance"]
                        )
                    )
                    
                    # Create payload indexes for filtering
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="namespace",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="memory_id",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="content_type",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    logger.info(f"Collection {collection_name} created successfully")
                else:
                    logger.info(f"Collection {collection_name} already exists")
            
            logger.info("Qdrant collections initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    def upsert_embeddings(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> List[int]:
        """
        Upsert embeddings into Qdrant collection
        
        Args:
            collection_name: Name of the collection
            points: List of PointStruct objects with embeddings
            
        Returns:
            List of point IDs that were upserted
        """
        if not self.is_connected:
            raise RuntimeError("Qdrant client not connected")
        
        try:
            result = self.client.upsert(
                collection_name=collection_name,
                wait=True,
                points=points
            )
            logger.debug(f"Upserted {len(points)} points into {collection_name}")
            return [p.id for p in points]
        except Exception as e:
            logger.error(f"Failed to upsert embeddings: {e}")
            raise
    
    def search_embeddings(
        self,
        collection_name: str,
        query_embedding: List[float],
        namespace: str,
        content_type: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in Qdrant
        
        Args:
            collection_name: Name of the collection to search
            query_embedding: Query embedding vector
            namespace: User namespace for filtering
            content_type: Optional filter by content type
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores and payloads
        """
        if not self.is_connected:
            raise RuntimeError("Qdrant client not connected")
        
        try:
            # Build filter
            must_conditions = [
                models.FieldCondition(
                    key="namespace",
                    match=models.MatchValue(value=namespace)
                )
            ]
            
            if content_type:
                must_conditions.append(
                    models.FieldCondition(
                        key="content_type",
                        match=models.MatchValue(value=content_type)
                    )
                )
            
            filter_obj = models.Filter(must=must_conditions) if must_conditions else None
            
            # Search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=filter_obj,
                limit=top_k,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "point_id": result.id,
                    "similarity_score": result.score,
                    "payload": result.payload or {}
                })
            
            logger.debug(f"Found {len(formatted_results)} results in {collection_name}")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def delete_by_memory_id(
        self,
        collection_name: str,
        memory_id: str
    ) -> int:
        """
        Delete all embeddings associated with a memory
        
        Args:
            collection_name: Name of the collection
            memory_id: Memory ID to delete
            
        Returns:
            Number of points deleted
        """
        if not self.is_connected:
            raise RuntimeError("Qdrant client not connected")
        
        try:
            delete_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="memory_id",
                        match=models.MatchValue(value=memory_id)
                    )
                ]
            )
            
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=delete_filter)
            )
            
            logger.debug(f"Deleted embeddings for memory {memory_id}")
            return result.deleted
        
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    def delete_by_namespace(
        self,
        collection_name: str,
        namespace: str
    ) -> int:
        """
        Delete all embeddings for a namespace (user)
        
        Args:
            collection_name: Name of the collection
            namespace: Namespace to delete
            
        Returns:
            Number of points deleted
        """
        if not self.is_connected:
            raise RuntimeError("Qdrant client not connected")
        
        try:
            delete_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="namespace",
                        match=models.MatchValue(value=namespace)
                    )
                ]
            )
            
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=delete_filter)
            )
            
            logger.debug(f"Deleted all embeddings for namespace {namespace}")
            return result.deleted
        
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        if not self.is_connected:
            raise RuntimeError("Qdrant client not connected")
        
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count or 0
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise


# Global instance
qdrant_manager = QdrantManager()
