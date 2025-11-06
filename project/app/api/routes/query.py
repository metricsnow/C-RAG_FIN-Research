"""
RAG query API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import verify_api_key
from app.api.models.query import QueryRequest, QueryResponse, SourceMetadata
from app.rag.chain import RAGQueryError, RAGQuerySystem, create_rag_system
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

# Global RAG system instance (lazy initialization)
_rag_system: RAGQuerySystem | None = None


def get_rag_system() -> RAGQuerySystem:
    """
    Get or create RAG query system instance.

    Returns:
        RAGQuerySystem instance
    """
    global _rag_system
    if _rag_system is None:
        logger.info("Initializing RAG query system for API")
        _rag_system = create_rag_system()
    return _rag_system


@router.post("", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query(
    request: QueryRequest,
    rag_system: RAGQuerySystem = Depends(get_rag_system),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> QueryResponse:
    """
    Process a RAG query and generate an answer.

    Args:
        request: Query request with question and optional parameters
        rag_system: RAG query system instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Query response with answer and sources

    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"Processing API query: '{request.question[:50]}...'")

        # Process query
        result = rag_system.query(
            question=request.question,
            top_k=request.top_k,
            conversation_history=request.conversation_history,
        )

        # Convert sources to SourceMetadata models
        sources = []
        for source in result.get("sources", []):
            sources.append(
                SourceMetadata(
                    source=source.get("source"),
                    filename=source.get("filename"),
                    ticker=source.get("ticker"),
                    form_type=source.get("form_type"),
                    chunk_index=source.get("chunk_index"),
                    date=source.get("date"),
                )
            )

        # Build response
        response = QueryResponse(
            answer=result.get("answer", ""),
            sources=sources,
            chunks_used=result.get("chunks_used", 0),
            error=result.get("error"),
        )

        logger.info(
            f"Query processed successfully: "
            f"answer_length={len(response.answer)}, "
            f"sources={len(response.sources)}"
        )

        return response

    except RAGQueryError as e:
        logger.error(f"RAG query error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query processing failed: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during query processing",
        ) from e
