from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import timedelta
import io

from app.database import get_db
from app.schemas.schemas import (
    UserCreate, UserResponse, UserLogin, TokenResponse,
    TextMemoryRequest, MemoryResponse,
    MemoryListResponse, SearchRequest, SearchResponse, SearchResult,
    SuccessResponse, ErrorResponse, ImageMemoryRequest, PDFMemoryRequest,
    AudioMemoryRequest, AskRequest, AskResponse, Source, ConversationCreate,
    ConversationResponse, ConversationWithMessages, MessageResponse,
    WebSearchRequest, WebSearchResponse, WebSearchResult,
    PreferencesUpdate, PreferencesResponse, UserStatsResponse,
    TimelineResponse, TimelineGroup, PopularSearchesResponse, PopularSearch,
    AdvancedSearchRequest, AdvancedSearchResponse, AdvancedSearchResult
)
from app.services.storage.storage_service import storage_service
from app.services.storage.minio_service import minio_service
from app.services.ingestion.text_processor import text_processor
from app.services.ingestion.image_processor import image_processor
from app.services.ingestion.pdf_processor import pdf_processor
from app.services.ingestion.audio_processor import audio_processor
from app.services.embeddings.embedding_service import embedding_service
from app.services.auth.auth_service import auth_service
from app.services.auth.auth_middleware import get_current_user_namespace, get_optional_user_namespace
from app.services.personalization.preferences_service import preferences_service
from app.services.personalization.reranking_service import reranking_service
from app.services.analytics.analytics_service import analytics_service
from app.services.retrieval.advanced_hybrid_search import advanced_hybrid_search
from app.services.retrieval.cross_encoder_reranker import reranker
from app.middleware.rate_limiting import limiter
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with namespace only"""
    try:
        # Check if namespace already exists
        existing_user = await storage_service.get_user_by_namespace(db, user_data.namespace)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Namespace already exists"
            )
        
        # Create the user with namespace
        user = await storage_service.create_user(
            db, 
            namespace=user_data.namespace
        )
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with namespace only"""
    try:
        # Get user by namespace
        user = await storage_service.get_user_by_namespace(db, login_data.namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid namespace"
            )
        
        # Create access token with namespace
        access_token = auth_service.create_access_token(user.namespace)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            namespace=user.namespace
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/users/{namespace}", response_model=UserResponse)
async def get_user(
    namespace: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user by namespace"""
    user = await storage_service.get_user_by_namespace(db, namespace)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user



@router.post("/remember/text", response_model=SuccessResponse)
async def remember_text(
    request: TextMemoryRequest,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Store text memory
    
    This endpoint:
    1. Validates the user exists
    2. Processes and chunks the text
    3. Generates embeddings for each chunk
    4. Stores everything in the database
    """
    try:
        # Verify user exists
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Process text
        processed = await text_processor.process_text(
            request.text,
            request.metadata
        )
        
        # Create memory with embeddings
        memory = await storage_service.create_memory(
            db=db,
            namespace=namespace,
            content_type="text",
            content=processed["original_text"],
            chunks=processed["chunks"],
            meta_data=processed["metadata"]
        )
        
        return SuccessResponse(
            success=True,
            message="Text memory stored successfully",
            data={
                "memory_id": str(memory.id),
                "num_chunks": processed["num_chunks"],
                "token_count": processed["token_count"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text memory creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store text memory: {str(e)}"
        )

@router.post("/remember/image", response_model=SuccessResponse)
async def remember_image(
    file: UploadFile = File(...),
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Store image memory
    
    This endpoint:
    1. Validates the user and image file
    2. Extracts text via OCR
    3. Generates CLIP embeddings
    4. Uploads image to MinIO
    5. Stores everything in the database
    """
    try:
        # Verify user exists
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Read file data
        file_data = await file.read()
        file_stream = io.BytesIO(file_data)
        
        # Validate image
        image_processor.validate_image(file_stream)
        file_stream.seek(0)
        
        # Process image (OCR + CLIP)
        processed = await image_processor.process_image(
            file_stream,
            metadata={"original_filename": file.filename}
        )
        
        # Upload to MinIO
        file_stream.seek(0)
        object_path = minio_service.upload_file(
            file_stream,
            namespace,
            "image",
            file.filename,
            file.content_type or "image/jpeg"
        )
        
        # Create memory with OCR text chunks
        memory = await storage_service.create_memory(
            db=db,
            namespace=namespace,
            content_type="image",
            content=processed["ocr_text"],
            chunks=[{
                "text": processed["ocr_text"],
                "embedding": processed["clip_embedding"]
            }],
            meta_data=processed["metadata"],
            file_path=object_path
        )
        
        return SuccessResponse(
            success=True,
            message="Image memory stored successfully",
            data={
                "memory_id": str(memory.id),
                "file_path": object_path,
                "ocr_text_length": len(processed["ocr_text"]),
                "has_text": processed["metadata"]["has_text"]
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Image memory creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store image memory: {str(e)}"
        )

@router.post("/remember/pdf", response_model=SuccessResponse)
async def remember_pdf(
    file: UploadFile = File(...),
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Store PDF memory
    
    This endpoint:
    1. Validates the user and PDF file
    2. Extracts text from all pages (with OCR fallback)
    3. Chunks and generates embeddings
    4. Uploads PDF to MinIO
    5. Stores everything in the database
    """
    try:
        # Verify user exists
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Read file data
        file_data = await file.read()
        file_stream = io.BytesIO(file_data)
        
        # Validate PDF
        pdf_info = pdf_processor.validate_pdf(file_stream)
        file_stream.seek(0)
        
        # Process PDF
        processed = await pdf_processor.process_pdf(
            file_stream,
            metadata={
                "original_filename": file.filename,
                **pdf_info
            }
        )
        
        # Upload to MinIO
        file_stream.seek(0)
        object_path = minio_service.upload_file(
            file_stream,
            namespace,
            "pdf",
            file.filename,
            "application/pdf"
        )
        
        # Create memory with text chunks
        memory = await storage_service.create_memory(
            db=db,
            namespace=namespace,
            content_type="pdf",
            content=processed["full_text"],
            chunks=processed["chunks"],
            meta_data=processed["metadata"],
            file_path=object_path
        )
        
        return SuccessResponse(
            success=True,
            message="PDF memory stored successfully",
            data={
                "memory_id": str(memory.id),
                "file_path": object_path,
                "num_chunks": processed["num_chunks"],
                "token_count": processed["token_count"],
                "page_count": processed["metadata"]["page_count"]
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"PDF memory creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store PDF memory: {str(e)}"
        )

@router.post("/remember/audio", response_model=SuccessResponse)
async def remember_audio(
    file: UploadFile = File(...),
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Store audio memory
    
    This endpoint:
    1. Validates the user and audio file
    2. Transcribes audio using Whisper
    3. Chunks transcript and generates embeddings
    4. Uploads audio to MinIO
    5. Stores everything in the database
    """
    try:
        # Verify user exists
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Read file data
        file_data = await file.read()
        file_stream = io.BytesIO(file_data)
        
        # Validate audio
        audio_processor.validate_audio(file_stream, file.filename)
        file_stream.seek(0)
        
        # Process audio (transcription)
        processed = await audio_processor.process_audio(
            file_stream,
            file.filename,
            metadata={"original_filename": file.filename}
        )
        
        # Upload to MinIO
        file_stream.seek(0)
        object_path = minio_service.upload_file(
            file_stream,
            namespace,
            "audio",
            file.filename,
            file.content_type or "audio/mpeg"
        )
        
        # Create memory with transcript chunks
        memory = await storage_service.create_memory(
            db=db,
            namespace=namespace,
            content_type="audio",
            content=processed["transcript"],
            chunks=processed["chunks"],
            meta_data=processed["metadata"],
            file_path=object_path
        )
        
        return SuccessResponse(
            success=True,
            message="Audio memory stored successfully",
            data={
                "memory_id": str(memory.id),
                "file_path": object_path,
                "num_chunks": processed["num_chunks"],
                "token_count": processed["token_count"],
                "language": processed["metadata"]["language"],
                "duration_seconds": processed["metadata"]["duration_seconds"]
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Audio memory creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store audio memory: {str(e)}"
        )

@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    namespace: str = Query(..., description="User namespace"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all memories for a user with pagination"""
    try:
        skip = (page - 1) * page_size
        memories, total = await storage_service.get_memories(
            db, namespace, skip=skip, limit=page_size
        )
        
        # Convert database models to response schemas
        memory_responses = [MemoryResponse.from_db_model(m) for m in memories]
        
        return MemoryListResponse(
            memories=memory_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"List memories failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memories"
        )

@router.delete("/memories/{memory_id}", response_model=SuccessResponse)
async def delete_memory(
    memory_id: UUID,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a memory"""
    try:
        deleted = await storage_service.delete_memory(db, namespace, memory_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found or does not belong to user"
            )
        
        return SuccessResponse(
            success=True,
            message="Memory deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete memory failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )

# ==================== SEARCH ENDPOINT ====================

@router.post("/search/advanced", response_model=AdvancedSearchResponse)
@limiter.limit("20/minute")
async def advanced_search(
    request: Request,
    advanced_request: AdvancedSearchRequest,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced hybrid search with semantic + lexical + re-ranking
    
    This endpoint:
    1. Generates query embedding
    2. Performs hybrid search (vector + BM25)
    3. Optionally applies Cross-Encoder re-ranking
    4. Returns ranked results with detailed scores
    
    Features:
    - Vector similarity search for semantic matching
    - BM25 for lexical/keyword matching  
    - Cross-Encoder for relevance re-ranking
    - Configurable fusion methods (weighted, RRF)
    """
    try:
        # Verify user exists
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(advanced_request.query)
        
        # Perform advanced hybrid search
        results = await advanced_hybrid_search.search(
            db=db,
            namespace=namespace,
            query_embedding=query_embedding,
            query_text=advanced_request.query,
            top_k=advanced_request.top_k,
            content_type=advanced_request.content_type,
            fusion_method=advanced_request.fusion_method,
            use_reranking=advanced_request.use_reranking
        )
        
        # Format results
        search_results = []
        for result in results:
            search_result = AdvancedSearchResult(
                memory_id=result["memory_id"],
                content_type=result["content_type"],
                chunk_text=result["chunk_text"],
                vector_similarity=result.get("similarity", 0.0),
                bm25_score=result.get("bm25_score"),
                re_ranking_score=result.get("re_ranking_score"),
                hybrid_score=result.get("hybrid_score", 0.0),
                rank=result.get("rank", 0),
                metadata=result.get("metadata", {}),
                created_at=result["created_at"]
            )
            search_results.append(search_result)
        
        return AdvancedSearchResponse(
            results=search_results,
            query=advanced_request.query,
            total_results=len(search_results),
            fusion_method=advanced_request.fusion_method,
            reranking_used=advanced_request.use_reranking
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search failed: {str(e)}"
        )


@router.get("/search", response_model=SearchResponse)
async def search_memories(
    q: str = Query(..., description="Search query", min_length=1),
    namespace: str = Query(..., description="User namespace"),
    top_k: int = Query(5, ge=1, le=50),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search memories using semantic similarity
    
    This endpoint:
    1. Generates an embedding for the query
    2. Performs vector similarity search
    3. Returns ranked results with similarity scores
    """
    try:
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(q)
        
        # Search memories
        results = await storage_service.search_memories(
            db=db,
            namespace=namespace,
            query_embedding=query_embedding,
            top_k=top_k * 2,
            content_type=content_type
        )
        
        reranked_results = await reranking_service.rerank_results(results, namespace, db)
        
        final_results = reranked_results[:top_k]
        
        search_results = [
            SearchResult(**result) for result in final_results
        ]
        
        return SearchResponse(
            results=search_results,
            query=q,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )



@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SARVAI API",
        "version": "0.1.0"
    }



@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question using RAG (Retrieval-Augmented Generation)
    
    This endpoint:
    1. Processes the query
    2. Retrieves relevant memories (hybrid search)
    3. Optionally searches the web
    4. Builds context
    5. Generates answer using LLM
    """
    from app.services.rag.query_processor import query_processor
    from app.services.rag.retriever import retriever
    from app.services.rag.context_builder import context_builder
    from app.services.rag.generator import llm_generator
    from app.models.models import Conversation, Message
    from datetime import datetime
    
    try:
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        conversation_history = []
        conversation_id = request.conversation_id
        
        if conversation_id:
            from sqlalchemy import select
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
            messages = result.scalars().all()
            conversation_history = [
                {"role": m.role, "content": m.content} for m in messages
            ]
        
        processed_query = query_processor.process(
            request.question,
            conversation_history
        )
        
        retrieval_results = await retriever.retrieve(
            db=db,
            namespace=namespace,
            query=request.question,
            top_k=request.top_k,
            enable_web=request.enable_web_search
        )
        
        local_results = retrieval_results.get("local_results", [])
        web_results = retrieval_results.get("web_results", [])
        has_memory = retrieval_results.get("has_memory", False)
        all_results = local_results + web_results
        
        context = context_builder.build_context(all_results)
        
        prompt_messages = context_builder.build_prompt(
            query=request.question,
            context=context,
            conversation_history=conversation_history,
            has_memory=has_memory
        )
        
        answer = await llm_generator.generate(prompt_messages)
        
        sources = context_builder.extract_sources(answer, all_results)
        
        if not conversation_id:
            from app.models.models import Conversation
            conversation = Conversation(
                namespace=namespace,
                title=request.question[:100]
            )
            db.add(conversation)
            await db.flush()
            conversation_id = conversation.id
        
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.question,
            meta_data=processed_query
        )
        db.add(user_message)
        
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            meta_data={
                "sources_count": len(sources),
                "web_search_used": len(web_results) > 0
            }
        )
        db.add(assistant_message)
        
        await db.commit()
        
        logger.info(f"RAG answer generated: {len(answer)} chars, {len(sources)} sources")
        
        return AskResponse(
            answer=answer,
            sources=sources,
            conversation_id=conversation_id,
            web_search_used=len(web_results) > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ask endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}"
        )

@router.post("/ask/stream")
async def ask_question_stream(
    request: AskRequest,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question with streaming response
    """
    from sse_starlette.sse import EventSourceResponse
    from app.services.rag.query_processor import query_processor
    from app.services.rag.retriever import retriever
    from app.services.rag.context_builder import context_builder
    from app.services.rag.generator import llm_generator
    from app.models.models import Conversation, Message
    import json
    
    async def event_generator():
        try:
            user = await storage_service.get_user_by_namespace(db, namespace)
            if not user:
                yield {"data": json.dumps({"error": "User not found"})}
                return
            
            conversation_history = []
            conversation_id = request.conversation_id
            
            if conversation_id:
                from sqlalchemy import select
                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                )
                messages = result.scalars().all()
                conversation_history = [
                    {"role": m.role, "content": m.content} for m in messages
                ]
            
            retrieval_results = await retriever.retrieve(
                db=db,
                namespace=namespace,
                query=request.question,
                top_k=request.top_k,
                enable_web=request.enable_web_search
            )
            
            all_results = retrieval_results.get("local_results", []) + retrieval_results.get("web_results", [])
            
            context = context_builder.build_context(all_results)
            prompt_messages = context_builder.build_prompt(
                query=request.question,
                context=context,
                conversation_history=conversation_history
            )
            
            full_answer = ""
            
            async for chunk in llm_generator.generate_stream(prompt_messages):
                full_answer += chunk
                yield {"data": json.dumps({"chunk": chunk})}
            
            sources = context_builder.extract_sources(full_answer, all_results)
            
            if not conversation_id:
                conversation = Conversation(
                    namespace=namespace,
                    title=request.question[:100]
                )
                db.add(conversation)
                await db.flush()
                conversation_id = conversation.id
            
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=request.question
            )
            db.add(user_message)
            
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_answer,
                meta_data={
                    "sources_count": len(sources),
                    "web_search_used": len(retrieval_results.get("web_results", [])) > 0
                }
            )
            db.add(assistant_message)
            
            await db.commit()
            
            yield {
                "data": json.dumps({
                    "done": True,
                    "conversation_id": str(conversation_id),
                    "sources": [s.dict() if hasattr(s, 'dict') else s for s in sources]
                })
            }
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield {"data": json.dumps({"error": str(e)})}
    
    return EventSourceResponse(event_generator())

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    from app.models.models import Conversation
    
    try:
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        conversation = Conversation(
            namespace=namespace,
            title=request.title or "New Conversation"
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create conversation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """List all conversations for a user"""
    from app.models.models import Conversation
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.namespace == namespace)
            .order_by(Conversation.updated_at.desc())
        )
        conversations = result.scalars().all()
        return conversations
        
    except Exception as e:
        logger.error(f"List conversations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )

@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation with all messages"""
    from app.models.models import Conversation, Message
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.namespace == namespace
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = messages_result.scalars().all()
        
        return ConversationWithMessages(
            id=conversation.id,
            namespace=conversation.namespace,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[MessageResponse.from_orm(m) for m in messages]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )

@router.delete("/conversations/{conversation_id}", response_model=SuccessResponse)
async def delete_conversation(
    conversation_id: UUID,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    from app.models.models import Conversation
    from sqlalchemy import select, delete
    
    try:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.namespace == namespace
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        await db.delete(conversation)
        await db.commit()
        
        return SuccessResponse(
            success=True,
            message="Conversation deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )



@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences"""
    try:
        preferences = await preferences_service.get_preferences(db, namespace)
        
        if not preferences:
            preferences = await preferences_service.create_preferences(db, namespace)
        
        return preferences
        
    except Exception as e:
        logger.error(f"Get preferences failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )

@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    request: PreferencesUpdate,
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    try:
        preferences = await preferences_service.update_preferences(
            db=db,
            namespace=namespace,
            boost_topics=request.boost_topics,
            suppress_topics=request.suppress_topics,
            search_preferences=request.search_preferences
        )
        
        return preferences
        
    except Exception as e:
        logger.error(f"Update preferences failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

@router.post("/preferences/boost/{topic}", response_model=PreferencesResponse)
async def add_boost_topic(
    topic: str,
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Add a topic to boost in search results"""
    try:
        preferences = await preferences_service.add_boost_topic(db, namespace, topic)
        return preferences
        
    except Exception as e:
        logger.error(f"Add boost topic failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add boost topic"
        )

@router.delete("/preferences/boost/{topic}", response_model=PreferencesResponse)
async def remove_boost_topic(
    topic: str,
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Remove a topic from boost list"""
    try:
        preferences = await preferences_service.remove_boost_topic(db, namespace, topic)
        return preferences
        
    except Exception as e:
        logger.error(f"Remove boost topic failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove boost topic"
        )

@router.post("/preferences/suppress/{topic}", response_model=PreferencesResponse)
async def add_suppress_topic(
    topic: str,
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Add a topic to suppress in search results"""
    try:
        preferences = await preferences_service.add_suppress_topic(db, namespace, topic)
        return preferences
        
    except Exception as e:
        logger.error(f"Add suppress topic failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add suppress topic"
        )

@router.delete("/preferences/suppress/{topic}", response_model=PreferencesResponse)
async def remove_suppress_topic(
    topic: str,
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Remove a topic from suppress list"""
    try:
        preferences = await preferences_service.remove_suppress_topic(db, namespace, topic)
        return preferences
        
    except Exception as e:
        logger.error(f"Remove suppress topic failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove suppress topic"
        )

# ==================== ANALYTICS & STATS ENDPOINTS ====================

@router.get("/stats/dashboard", response_model=UserStatsResponse)
async def get_dashboard_stats(
    namespace: str = Depends(get_current_user_namespace),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive user statistics for dashboard"""
    try:
        stats = await analytics_service.get_user_stats(db, namespace)
        return UserStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Get dashboard stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.get("/memories/timeline", response_model=TimelineResponse)
async def get_memories_timeline(
    namespace: str = Depends(get_current_user_namespace),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get memories grouped by date for timeline view"""
    try:
        skip = (page - 1) * page_size
        timeline = await analytics_service.get_timeline_grouped(
            db=db,
            namespace=namespace,
            skip=skip,
            limit=page_size
        )
        
        total_items = sum(len(group["memories"]) for group in timeline)
        
        return TimelineResponse(
            timeline=timeline,
            total_items=total_items
        )
        
    except Exception as e:
        logger.error(f"Get timeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve timeline"
        )

@router.get("/stats/popular-searches", response_model=PopularSearchesResponse)
async def get_popular_searches(
    namespace: str = Depends(get_current_user_namespace),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get most popular search queries"""
    try:
        searches = await analytics_service.get_popular_searches(db, namespace, limit)
        
        return PopularSearchesResponse(
            searches=[PopularSearch(**s) for s in searches]
        )
        
    except Exception as e:
        logger.error(f"Get popular searches failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular searches"
        )

# ==================== WEB SEARCH ENDPOINTS ====================

@router.post("/web/search", response_model=WebSearchResponse)
async def web_search(
    request: WebSearchRequest,
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search the web and optionally cache results
    """
    from app.services.web.search_service import web_search_service
    from app.services.web.scraper import web_scraper
    
    try:
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        search_results = await web_search_service.search(
            request.query,
            num_results=request.num_results
        )
        
        results = []
        cached_count = 0
        scraped_count = 0
        
        for item in search_results:
            url = item.get("url", "")
            
            scraped = await web_scraper.scrape_url(url)
            
            if scraped.get("content"):
                scraped_count += 1
                results.append(WebSearchResult(
                    title=scraped.get("title") or item.get("title", ""),
                    url=url,
                    snippet=item.get("snippet", ""),
                    content=scraped["content"][:1000]
                ))
            else:
                results.append(WebSearchResult(
                    title=item.get("title", ""),
                    url=url,
                    snippet=item.get("snippet", ""),
                    content=None
                ))
        
        return WebSearchResponse(
            results=results,
            query=request.query,
            cached=cached_count,
            scraped=scraped_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Web search failed: {str(e)}"
        )

@router.post("/web/scrape")
async def scrape_url(
    url: str = Query(..., description="URL to scrape"),
    namespace: str = Query(..., description="User namespace"),
    db: AsyncSession = Depends(get_db)
):
    """Scrape content from a specific URL"""
    from app.services.web.scraper import web_scraper
    
    try:
        user = await storage_service.get_user_by_namespace(db, namespace)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = await web_scraper.scrape_url(url)
        
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Scraping failed: {result['error']}"
            )
        
        return {
            "success": True,
            "url": result["url"],
            "title": result["title"],
            "content": result["content"],
            "domain": result["domain"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scrape URL failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape URL: {str(e)}"
        )