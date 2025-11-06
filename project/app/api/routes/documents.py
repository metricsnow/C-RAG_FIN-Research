"""
Document management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import verify_api_key
from app.api.models.documents import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetadata,
)
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Global document manager instance (lazy initialization)
_document_manager: DocumentManager | None = None


def get_document_manager() -> DocumentManager:
    """
    Get or create document manager instance.

    Returns:
        DocumentManager instance
    """
    global _document_manager
    if _document_manager is None:
        logger.info("Initializing document manager for API")
        _document_manager = DocumentManager()
    return _document_manager


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents(
    doc_manager: DocumentManager = Depends(get_document_manager),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> DocumentListResponse:
    """
    List all documents in the vector database.

    Args:
        doc_manager: Document manager instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        List of all documents with metadata

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info("Retrieving all documents")

        documents_data = doc_manager.get_all_documents()

        # Convert to DocumentMetadata models
        documents = []
        for doc_data in documents_data:
            documents.append(
                DocumentMetadata(
                    id=doc_data.get("id", ""),
                    metadata=doc_data.get("metadata", {}),
                    content=(
                        doc_data.get("content", "")[:500]
                        if doc_data.get("content")
                        else None
                    ),  # Preview only
                )
            )

        logger.info(f"Retrieved {len(documents)} documents")

        return DocumentListResponse(
            documents=documents,
            total=len(documents),
            message=f"Retrieved {len(documents)} documents successfully",
        )

    except DocumentManagerError as e:
        logger.error(f"Document manager error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in list_documents endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document retrieval",
        ) from e


@router.get(
    "/{doc_id}", response_model=DocumentDetailResponse, status_code=status.HTTP_200_OK
)
async def get_document(
    doc_id: str,
    doc_manager: DocumentManager = Depends(get_document_manager),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> DocumentDetailResponse:
    """
    Get document details by ID.

    Args:
        doc_id: Document chunk ID
        doc_manager: Document manager instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Document details with metadata

    Raises:
        HTTPException: If document not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving document: {doc_id}")

        # Get all documents and find the one with matching ID
        all_documents = doc_manager.get_all_documents()
        document_data = None

        for doc_data in all_documents:
            if doc_data.get("id") == doc_id:
                document_data = doc_data
                break

        if not document_data:
            logger.warning(f"Document not found: {doc_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}",
            )

        document = DocumentMetadata(
            id=document_data.get("id", ""),
            metadata=document_data.get("metadata", {}),
            content=document_data.get("content"),
        )

        logger.info(f"Retrieved document: {doc_id}")

        return DocumentDetailResponse(
            document=document,
            message="Document retrieved successfully",
            error=None,
        )

    except HTTPException:
        raise
    except DocumentManagerError as e:
        logger.error(f"Document manager error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in get_document endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document retrieval",
        ) from e


@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    doc_id: str,
    doc_manager: DocumentManager = Depends(get_document_manager),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> dict:
    """
    Delete a document by ID.

    Args:
        doc_id: Document chunk ID
        doc_manager: Document manager instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        logger.info(f"Deleting document: {doc_id}")

        # Delete document using document manager
        deleted_count = doc_manager.delete_documents([doc_id])
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}",
            )

        logger.info(f"Document deleted successfully: {doc_id}")

        return {
            "message": f"Document {doc_id} deleted successfully",
            "doc_id": doc_id,
        }

    except DocumentManagerError as e:
        logger.error(f"Document manager error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in delete_document endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document deletion",
        ) from e
