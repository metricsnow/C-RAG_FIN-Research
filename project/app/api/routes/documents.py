"""
Document management API routes.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

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


@router.get("/{source}/versions", status_code=status.HTTP_200_OK)
async def get_version_history(
    source: str,
    doc_manager: DocumentManager = Depends(get_document_manager),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> dict:
    """
    Get version history for a document source.

    Args:
        source: Source filename
        doc_manager: Document manager instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Version history information

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Retrieving version history for: {source}")

        version_history = doc_manager.get_version_history(source)

        logger.info(f"Retrieved {len(version_history)} versions for: {source}")

        return {
            "source": source,
            "versions": version_history,
            "total_versions": len(version_history),
        }

    except DocumentManagerError as e:
        logger.error(f"Document manager error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve version history: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in get_version_history endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during version history retrieval",
        ) from e


@router.get("/{source}/versions/compare", status_code=status.HTTP_200_OK)
async def compare_versions(
    source: str,
    version1: int,
    version2: int,
    doc_manager: DocumentManager = Depends(get_document_manager),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> dict:
    """
    Compare two versions of a document.

    Args:
        source: Source filename
        version1: First version number
        version2: Second version number
        doc_manager: Document manager instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Comparison results

    Raises:
        HTTPException: If comparison fails
    """
    try:
        logger.info(f"Comparing versions {version1} and {version2} for: {source}")

        comparison = doc_manager.compare_versions(source, version1, version2)

        logger.info(f"Comparison complete for: {source}")

        return {
            "source": source,
            "version1": version1,
            "version2": version2,
            "comparison": comparison,
        }

    except DocumentManagerError as e:
        logger.error(f"Document manager error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare versions: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in compare_versions endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during version comparison",
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
            logger.warning(f"Document not found for deletion: {doc_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}",
            )

        logger.info(f"Document deleted successfully: {doc_id}")

        return {
            "message": f"Document {doc_id} deleted successfully",
            "doc_id": doc_id,
        }

    except HTTPException:
        raise
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


@router.post("/reindex", status_code=status.HTTP_200_OK)
async def reindex_document(
    file: UploadFile = File(...),  # noqa: B008
    preserve_metadata: bool = True,
    increment_version: bool = True,
    doc_manager: DocumentManager = Depends(get_document_manager),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> dict:
    """
    Re-index a document by uploading a new version.

    Args:
        file: Uploaded document file
        preserve_metadata: Whether to preserve original metadata
        increment_version: Whether to increment version number
        doc_manager: Document manager instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Re-indexing result with statistics

    Raises:
        HTTPException: If re-indexing fails
    """
    import os
    import tempfile

    tmp_path: Optional[Path] = None
    try:
        logger.info(f"Re-indexing document: {file.filename}")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix if file.filename else ""
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        # Re-index document
        result = doc_manager.reindex_document(
            tmp_path,
            preserve_metadata=preserve_metadata,
            increment_version=increment_version,
        )

        logger.info(
            f"Re-indexing complete: {result['old_chunks_deleted']} deleted, "
            f"{result['new_chunks_created']} created, version {result['version']}"
        )

        return {
            "message": "Document re-indexed successfully",
            "old_chunks_deleted": result["old_chunks_deleted"],
            "new_chunks_created": result["new_chunks_created"],
            "version": result["version"],
            "new_chunk_ids": result["new_chunk_ids"],
        }

    except DocumentManagerError as e:
        logger.error(f"Document manager error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-index document: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in reindex_document endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document re-indexing",
        ) from e
    finally:
        # Clean up temporary file
        if tmp_path and tmp_path.exists():
            os.unlink(tmp_path)
