"""
LangChain-compatible Qdrant Vectorstore

Provides a LangChain Vectorstore interface for Qdrant to enable integration
with LangChain's retrieval chains, agents, and other components.
"""

from typing import Any, List, Optional, Tuple
from langchain.schema import Document
from langchain.vectorstores.base import VectorStore
from app.services.embeddings.qdrant_manager import qdrant_manager
from app.services.embeddings.embedding_service import embedding_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStore):
    """LangChain VectorStore interface for Qdrant"""
    
    def __init__(
        self,
        collection_name: str = "text_embeddings",
        namespace: str = None,
        embedding_function=None
    ):
        """
        Initialize Qdrant VectorStore
        
        Args:
            collection_name: Name of the Qdrant collection
            namespace: User namespace for filtering
            embedding_function: Function to generate embeddings
        """
        self.collection_name = collection_name
        self.namespace = namespace
        self.embedding_function = embedding_function or embedding_service
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[str]:
        """
        Add texts to the vectorstore
        
        Args:
            texts: List of text documents
            metadatas: List of metadata dicts
            ids: List of document IDs
            
        Returns:
            List of added document IDs
        """
        try:
            # Generate embeddings
            embeddings = []
            for text in texts:
                embedding = self.embedding_function.embed_text(text)
                embeddings.append(embedding)
            
            # Create points for Qdrant
            from qdrant_client.models import PointStruct
            
            points = []
            for idx, (text, embedding) in enumerate(zip(texts, embeddings)):
                point_id = ids[idx] if ids else hash(text) & 0x7FFFFFFF
                
                payload = metadatas[idx] if metadatas else {}
                payload.update({
                    "text": text,
                    "namespace": self.namespace or "default"
                })
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upsert to Qdrant
            point_ids = qdrant_manager.upsert_embeddings(self.collection_name, points)
            
            logger.info(f"Added {len(point_ids)} texts to {self.collection_name}")
            return [str(pid) for pid in point_ids]
        
        except Exception as e:
            logger.error(f"Failed to add texts: {e}")
            raise
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of LangChain Document objects
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_function.embed_text(query)
            
            # Search in Qdrant
            results = qdrant_manager.search_embeddings(
                collection_name=self.collection_name,
                query_embedding=query_embedding,
                namespace=self.namespace or "default",
                top_k=k
            )
            
            # Convert to LangChain Documents
            documents = []
            for result in results:
                payload = result.get("payload", {})
                doc = Document(
                    page_content=payload.get("text", ""),
                    metadata={
                        "point_id": result.get("point_id"),
                        "similarity_score": result.get("similarity_score"),
                        **{k: v for k, v in payload.items() if k != "text"}
                    }
                )
                documents.append(doc)
            
            return documents
        
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents with scores
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_function.embed_text(query)
            
            # Search in Qdrant
            results = qdrant_manager.search_embeddings(
                collection_name=self.collection_name,
                query_embedding=query_embedding,
                namespace=self.namespace or "default",
                top_k=k
            )
            
            # Convert to LangChain Documents with scores
            documents_with_scores = []
            for result in results:
                payload = result.get("payload", {})
                doc = Document(
                    page_content=payload.get("text", ""),
                    metadata={
                        "point_id": result.get("point_id"),
                        **{k: v for k, v in payload.items() if k != "text"}
                    }
                )
                score = result.get("similarity_score", 0.0)
                documents_with_scores.append((doc, score))
            
            return documents_with_scores
        
        except Exception as e:
            logger.error(f"Similarity search with score failed: {e}")
            raise
    
    def delete(self, ids: List[str], **kwargs: Any) -> Optional[bool]:
        """
        Delete documents by IDs
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            True if successful
        """
        try:
            from qdrant_client.models import PointIdsList
            
            # Convert string IDs to integers
            int_ids = [int(id) if id.isdigit() else hash(id) & 0x7FFFFFFF for id in ids]
            
            result = qdrant_manager.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=int_ids)
            )
            
            logger.info(f"Deleted {result.deleted} points from {self.collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding,
        **kwargs: Any
    ) -> "QdrantVectorStore":
        """
        Create a QdrantVectorStore from documents
        
        Args:
            documents: List of LangChain Document objects
            embedding: Embedding function
            
        Returns:
            QdrantVectorStore instance
        """
        vectorstore = cls(**kwargs)
        
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        vectorstore.add_texts(texts, metadatas)
        
        return vectorstore
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any
    ) -> "QdrantVectorStore":
        """
        Create a QdrantVectorStore from texts
        
        Args:
            texts: List of text documents
            embedding: Embedding function
            metadatas: Optional metadata for each text
            
        Returns:
            QdrantVectorStore instance
        """
        vectorstore = cls(**kwargs)
        vectorstore.add_texts(texts, metadatas)
        return vectorstore
