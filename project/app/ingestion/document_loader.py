"""
Document loader module for processing text and Markdown files.

Handles document loading, text extraction, chunking, and metadata management
for the RAG system.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentIngestionError(Exception):
    """Custom exception for document ingestion errors."""

    pass


class DocumentLoader:
    """
    Document loader for processing text and Markdown files.

    Supports:
    - Text files (.txt)
    - Markdown files (.md)
    - File size validation (max 10MB)
    - Document chunking with metadata
    - Error handling for corrupted/unsupported files
    """

    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize document loader.

        Args:
            chunk_size: Size of text chunks in characters (default: 1000)
            chunk_overlap: Overlap between chunks in characters (default: 200)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def _validate_file(self, file_path: Path) -> None:
        """
        Validate file before processing.

        Args:
            file_path: Path to the file to validate

        Raises:
            DocumentIngestionError: If file validation fails
        """
        logger.debug(f"Validating file: {file_path}")
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise DocumentIngestionError(f"File not found: {file_path}")

        if not file_path.is_file():
            logger.error(f"Path is not a file: {file_path}")
            raise DocumentIngestionError(f"Path is not a file: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            logger.warning(
                f"File size ({file_size} bytes) exceeds maximum "
                f"allowed size ({self.MAX_FILE_SIZE_BYTES} bytes): {file_path}"
            )
            raise DocumentIngestionError(
                f"File size ({file_size} bytes) exceeds maximum "
                f"allowed size ({self.MAX_FILE_SIZE_BYTES} bytes)"
            )

        # Check file extension
        file_ext = file_path.suffix.lower()
        if file_ext not in [".txt", ".md"]:
            logger.error(f"Unsupported file format: {file_ext} for file: {file_path}")
            raise DocumentIngestionError(
                f"Unsupported file format: {file_ext}. " "Supported formats: .txt, .md"
            )
        logger.debug(f"File validation successful: {file_path}")

    def _get_file_type(self, file_path: Path) -> str:
        """
        Get file type from extension.

        Args:
            file_path: Path to the file

        Returns:
            File type string ("text" or "markdown")
        """
        ext = file_path.suffix.lower()
        if ext == ".md":
            return "markdown"
        return "text"

    def _load_text_file(self, file_path: Path) -> Document:
        """
        Load a text file using LangChain TextLoader.

        Args:
            file_path: Path to the text file

        Returns:
            Document object with content and metadata

        Raises:
            DocumentIngestionError: If file loading fails
        """
        logger.info(f"Loading text file: {file_path}")
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents = loader.load()
            if not documents:
                logger.error(f"Failed to load content from: {file_path}")
                raise DocumentIngestionError(
                    f"Failed to load content from: {file_path}"
                )
            logger.debug(f"Successfully loaded text file: {file_path}")
            return documents[0]
        except Exception as e:
            logger.error(
                f"Error loading text file {file_path}: {str(e)}", exc_info=True
            )
            raise DocumentIngestionError(
                f"Error loading text file {file_path}: {str(e)}"
            ) from e

    def _load_markdown_file(self, file_path: Path) -> Document:
        """
        Load a Markdown file.

        For Markdown files, we use TextLoader as it handles .md files well.
        More sophisticated parsing can be added later if needed.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Document object with content and metadata

        Raises:
            DocumentIngestionError: If file loading fails
        """
        logger.info(f"Loading Markdown file: {file_path}")
        try:
            # TextLoader can handle Markdown files effectively
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents = loader.load()
            if not documents:
                logger.error(f"Failed to load content from: {file_path}")
                raise DocumentIngestionError(
                    f"Failed to load content from: {file_path}"
                )
            logger.debug(f"Successfully loaded Markdown file: {file_path}")
            return documents[0]
        except Exception as e:
            logger.error(
                f"Error loading Markdown file {file_path}: {str(e)}", exc_info=True
            )
            raise DocumentIngestionError(
                f"Error loading Markdown file {file_path}: {str(e)}"
            ) from e

    def load_document(self, file_path: Path) -> Document:
        """
        Load a document from file.

        Args:
            file_path: Path to the document file

        Returns:
            Document object with content and metadata

        Raises:
            DocumentIngestionError: If document loading fails
        """
        logger.info(f"Loading document: {file_path}")
        # Validate file
        self._validate_file(file_path)

        # Determine file type and load accordingly
        file_type = self._get_file_type(file_path)
        if file_type == "markdown":
            document = self._load_markdown_file(file_path)
        else:
            document = self._load_text_file(file_path)

        # Add/update metadata
        document.metadata.update(
            {
                "source": str(file_path),
                "filename": file_path.name,
                "type": file_type,
                "date": datetime.now().isoformat(),
            }
        )
        logger.debug(f"Document loaded successfully: {file_path} (type: {file_type})")
        return document

    def chunk_document(self, document: Document) -> List[Document]:
        """
        Split a document into chunks with metadata.

        Args:
            document: Document object to chunk

        Returns:
            List of Document chunks with metadata including chunk_index
        """
        logger.debug(
            f"Chunking document (source: {document.metadata.get('source', 'unknown')})"
        )
        # Split document into chunks
        chunks = self.text_splitter.split_documents([document])

        # Add chunk_index to metadata
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            # Preserve original metadata
            chunk.metadata.update(document.metadata)

        logger.info(f"Document chunked into {len(chunks)} chunks")
        return chunks

    def process_document(self, file_path: Path) -> List[Document]:
        """
        Process a document: load, validate, and chunk.

        This is the main entry point for document processing.

        Args:
            file_path: Path to the document file

        Returns:
            List of Document chunks with metadata

        Raises:
            DocumentIngestionError: If document processing fails
        """
        # Load document
        document = self.load_document(file_path)

        # Chunk document
        chunks = self.chunk_document(document)

        return chunks

    def process_documents(self, file_paths: List[Path]) -> List[Document]:
        """
        Process multiple documents sequentially.

        Args:
            file_paths: List of paths to document files

        Returns:
            List of all Document chunks from all processed documents

        Raises:
            DocumentIngestionError: If any document processing fails
        """
        all_chunks = []

        for file_path in file_paths:
            try:
                chunks = self.process_document(file_path)
                all_chunks.extend(chunks)
            except DocumentIngestionError as e:
                # Log error but continue processing other files
                logger.warning(f"Failed to process {file_path}: {str(e)}")
                continue

        return all_chunks
