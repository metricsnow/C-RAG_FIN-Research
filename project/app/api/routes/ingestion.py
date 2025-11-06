"""
Document ingestion API routes.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.auth import verify_api_key
from app.api.models.ingestion import IngestionRequest, IngestionResponse
from app.ingestion.pipeline import (
    IngestionPipeline,
    IngestionPipelineError,
    create_pipeline,
)
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

# Global ingestion pipeline instance (lazy initialization)
_ingestion_pipeline: IngestionPipeline | None = None


def get_ingestion_pipeline() -> IngestionPipeline:
    """
    Get or create ingestion pipeline instance.

    Returns:
        IngestionPipeline instance
    """
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        logger.info("Initializing ingestion pipeline for API")
        _ingestion_pipeline = create_pipeline()
    return _ingestion_pipeline


@router.post("", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    request: IngestionRequest | None = None,
    file: UploadFile | None = File(None),  # noqa: B008
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> IngestionResponse:
    """
    Ingest a document from file path or uploaded file.

    Args:
        request: Ingestion request with file_path and store_embeddings (optional)
        file: Uploaded file (if ingesting from upload)
        pipeline: Ingestion pipeline instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Ingestion response with chunk IDs and status

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        # Get parameters from request or defaults
        # FastAPI will parse JSON body into request if provided
        file_path = request.file_path if request and request.file_path else None
        store_embeddings = request.store_embeddings if request else True

        # Validate input
        if not file_path and not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Either file_path in request body or "
                    "file upload must be provided"
                ),
            )

        # Handle file upload
        if file:
            # Save uploaded file temporarily
            upload_dir = config.DOCUMENTS_DIR
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path_obj = upload_dir / file.filename
            with open(file_path_obj, "wb") as f:
                content = await file.read()
                f.write(content)

            file_path = str(file_path_obj)
            logger.info(f"Saved uploaded file to: {file_path}")

        # Validate file path
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File path is required",
            )

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}",
            )

        # Check file size
        file_size = file_path_obj.stat().st_size
        max_size = config.max_document_size_mb * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size} bytes) exceeds maximum "
                f"({max_size} bytes)",
            )

        logger.info(f"Processing document ingestion: {file_path}")

        # Process document
        chunk_ids = pipeline.process_document(
            file_path=file_path_obj, store_embeddings=store_embeddings
        )

        logger.info(
            f"Document ingested successfully: "
            f"file={file_path}, chunks={len(chunk_ids)}"
        )

        return IngestionResponse(
            success=True,
            chunk_ids=chunk_ids,
            chunks_created=len(chunk_ids),
            message=f"Document ingested successfully: {len(chunk_ids)} chunks created",
            error=None,
        )

    except HTTPException:
        raise
    except IngestionPipelineError as e:
        logger.error(f"Ingestion pipeline error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document ingestion failed: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in ingestion endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document ingestion",
        ) from e
