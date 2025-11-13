"""API routes for the QA service."""

from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional
from app.models import QuestionRequest, AnswerResponse, ErrorResponse
from app.services.qa_service import QAService
from app.utils.logger import get_logger
from app.utils.exceptions import (
    MessagesAPIError,
    EmbeddingError,
    LLMError,
    ValidationError
)

logger = get_logger(__name__)

router = APIRouter()

# Global QA service instance (initialized in main.py)
qa_service: Optional[QAService] = None


def set_qa_service(service: QAService):
    """Set the QA service instance."""
    global qa_service
    qa_service = service


@router.get(
    "/ask",
    response_model=AnswerResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse}
    },
    summary="Ask a question",
    description="Answer a natural language question based on member messages"
)
async def ask_question(
    question: str = Query(..., description="Natural language question to answer")
):
    """
    Answer a question using RAG (Retrieval-Augmented Generation).
    
    This endpoint:
    1. Fetches messages from the messages API
    2. Uses semantic search to find relevant messages
    3. Generates an answer using an LLM
    
    Args:
        question: Natural language question
        
    Returns:
        AnswerResponse with the answer and source message IDs
    """
    if not qa_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="QA service not initialized"
        )
    
    if not question or not question.strip():
        raise ValidationError("Question cannot be empty")
    
    try:
        answer, source_ids = await qa_service.answer_question(question)
        
        return AnswerResponse(answer=answer)
        
    except MessagesAPIError as e:
        logger.error("Messages API error", error=str(e))
        raise
    except EmbeddingError as e:
        logger.error("Embedding error", error=str(e))
        raise
    except LLMError as e:
        logger.error("LLM error", error=str(e))
        raise
    except Exception as e:
        logger.error(
            "Unexpected error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/ask",
    response_model=AnswerResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse}
    },
    summary="Ask a question (POST)",
    description="Answer a natural language question based on member messages (POST version)"
)
async def ask_question_post(request: QuestionRequest):
    """
    Answer a question using RAG (POST version).
    
    Same as GET /ask but accepts question in request body.
    """
    return await ask_question(question=request.question)


@router.get(
    "/health",
    summary="Health check",
    description="Check if the service is healthy"
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "aurora-qa-service"}


@router.post(
    "/refresh-cache",
    summary="Refresh cache",
    description="Force refresh both message and embedding caches"
)
async def refresh_cache():
    """
    Force refresh all caches.
    
    This endpoint will:
    1. Clear the message cache and fetch fresh messages
    2. Clear the embedding cache and recompute embeddings
    
    Use this when you know new data has been added to the messages API.
    """
    if not qa_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="QA service not initialized"
        )
    
    try:
        logger.info("Manual cache refresh requested")
        
        # Force refresh messages (this will also trigger embedding refresh)
        messages = await qa_service.message_service.fetch_all_messages(force_refresh=True)
        
        # Clear embedding cache to force recomputation
        if hasattr(qa_service.hybrid_search_service, '_cached_embeddings'):
            qa_service.hybrid_search_service._cached_embeddings = None
            qa_service.hybrid_search_service._cached_message_hashes = None
            qa_service.hybrid_search_service._cache_timestamp = None
        
        # Also clear disk cache
        import os
        from pathlib import Path
        
        cache_files = [
            Path(".cache/embeddings_cache.pkl"),
            Path(".cache/messages_cache.json")
        ]
        
        cleared_files = []
        for cache_file in cache_files:
            if cache_file.exists():
                os.remove(cache_file)
                cleared_files.append(str(cache_file))
        
        logger.info(
            "Cache refresh completed",
            message_count=len(messages),
            cleared_files=cleared_files
        )
        
        return {
            "status": "success",
            "message": "Cache refreshed successfully",
            "message_count": len(messages),
            "cleared_files": cleared_files,
            "note": "Next query will rebuild embeddings cache"
        }
        
    except Exception as e:
        logger.error("Cache refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache refresh failed: {str(e)}"
        )

