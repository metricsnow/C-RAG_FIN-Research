"""
API client wrapper for FastAPI backend endpoints.

Provides a synchronous HTTP client for Streamlit frontend to communicate
with the FastAPI backend, replacing direct RAG system calls.
"""

from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    ConnectionError,
    RequestException,
    Timeout,
)
from urllib3.util.retry import Retry

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class APIConnectionError(APIClientError):
    """Raised when API connection fails."""

    pass


class APIError(APIClientError):
    """Raised when API returns an error response."""

    def __init__(
        self, message: str, status_code: int, response: Optional[Dict[str, Any]] = None
    ):
        # Pass message to parent, store additional attributes
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class APIClient:
    """
    HTTP client wrapper for FastAPI backend endpoints.

    Provides methods for all API operations including queries, document
    management, and health checks. Handles errors, retries, and
    request/response serialization.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (defaults to config.api_client_base_url)
            api_key: API key for authentication (optional)
            timeout: Request timeout in seconds (defaults to config.api_client_timeout)
            max_retries: Maximum number of retry attempts for transient failures
        """
        self.base_url = (base_url or config.api_client_base_url).rstrip("/")
        # Use API_KEY from config if api_client_key is empty
        self.api_key = api_key or config.api_client_key or config.api_key
        self.timeout = timeout or config.api_client_timeout
        self.max_retries = max_retries

        # Create session with retry strategy
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({"Content-Type": "application/json"})
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})

        logger.info(
            f"Initialized API client: base_url={self.base_url}, "
            f"timeout={self.timeout}, max_retries={max_retries}"
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API endpoint.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path (e.g., '/api/v1/query')
            json_data: JSON payload for request body
            params: Query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=self.timeout,
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                error_detail = "Unknown error"
                error_data = {}
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", str(error_data))
                except Exception:
                    error_detail = response.text or f"HTTP {response.status_code}"

                logger.error(
                    f"API error: {response.status_code} - {error_detail} "
                    f"(endpoint: {endpoint})"
                )
                raise APIError(
                    message=f"API error: {error_detail}",
                    status_code=response.status_code,
                    response=error_data,
                )

            # Parse JSON response
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                raise APIClientError(f"Invalid JSON response: {str(e)}")

        except Timeout as e:
            logger.error(f"Request timeout: {str(e)} (endpoint: {endpoint})")
            raise APIConnectionError(
                f"Request timeout after {self.timeout} seconds. "
                f"The API may be slow or unavailable."
            ) from e
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)} (endpoint: {endpoint})")
            raise APIConnectionError(
                f"Failed to connect to API at {self.base_url}. "
                f"Please ensure the API server is running."
            ) from e
        except APIError:
            # Re-raise API errors as-is
            raise
        except RequestException as e:
            logger.error(f"Request error: {str(e)} (endpoint: {endpoint})")
            raise APIConnectionError(f"Request failed: {str(e)}") from e

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.

        Returns:
            Health status dictionary

        Raises:
            APIConnectionError: If health check fails
        """
        try:
            return self._make_request("GET", "/api/v1/health")
        except APIConnectionError:
            # Health check failures are expected when API is down
            raise
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise APIConnectionError(f"Health check failed: {str(e)}") from e

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        filters: Optional[Dict[str, Any]] = None,
        enable_query_parsing: bool = True,
    ) -> Dict[str, Any]:
        """
        Send query to RAG system via API.

        Args:
            question: Natural language question
            top_k: Number of top chunks to retrieve
            conversation_history: Previous conversation messages
            filters: Query filters (ticker, form_type, date_from, etc.)
            enable_query_parsing: Enable automatic query parsing

        Returns:
            Query response dictionary with answer, sources, etc.

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response
        """
        # Build request payload
        request_data: Dict[str, Any] = {
            "question": question,
            "enable_query_parsing": enable_query_parsing,
        }

        if top_k is not None:
            request_data["top_k"] = top_k

        if conversation_history:
            request_data["conversation_history"] = conversation_history

        if filters:
            request_data["filters"] = filters

        # Make API request
        response = self._make_request("POST", "/api/v1/query", json_data=request_data)

        # Convert response to match expected format from RAGQuerySystem
        # API returns QueryResponse model, convert to dict format
        result: Dict[str, Any] = {
            "answer": response.get("answer", ""),
            "sources": [],
            "chunks_used": response.get("chunks_used", 0),
        }

        # Convert SourceMetadata models to dict format
        sources = response.get("sources", [])
        for source in sources:
            result["sources"].append(
                {
                    "source": source.get("source"),
                    "filename": source.get("filename"),
                    "ticker": source.get("ticker"),
                    "form_type": source.get("form_type"),
                    "chunk_index": source.get("chunk_index"),
                    "date": source.get("date"),
                }
            )

        # Include parsed_query if available
        if "parsed_query" in response:
            result["parsed_query"] = response["parsed_query"]

        # Include error if present
        if "error" in response and response["error"]:
            result["error"] = response["error"]

        return result

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents via API.

        Returns:
            List of document dictionaries with metadata

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response
        """
        response = self._make_request("GET", "/api/v1/documents")

        # Convert DocumentListResponse to list format
        documents = response.get("documents", [])
        result = []

        for doc in documents:
            # Convert DocumentMetadata to dict format
            result.append(
                {
                    "id": doc.get("id", ""),
                    "metadata": doc.get("metadata", {}),
                    "content": doc.get("content", ""),
                }
            )

        return result

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Get document details by ID via API.

        Args:
            doc_id: Document chunk ID

        Returns:
            Document dictionary with id, metadata, and content

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response (404 if not found)
        """
        response = self._make_request("GET", f"/api/v1/documents/{doc_id}")

        # Convert DocumentDetailResponse to dict format
        doc = response.get("document", {})
        return {
            "id": doc.get("id", ""),
            "metadata": doc.get("metadata", {}),
            "content": doc.get("content", ""),
        }

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document by ID via API.

        Args:
            doc_id: Document chunk ID

        Returns:
            True if deletion successful

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response
        """
        try:
            self._make_request("DELETE", f"/api/v1/documents/{doc_id}")
            return True
        except APIError as e:
            if e.status_code == 404:
                logger.warning(f"Document not found for deletion: {doc_id}")
                return False
            raise

    def get_version_history(self, source: str) -> List[Dict[str, Any]]:
        """
        Get version history for a document source via API.

        Args:
            source: Source filename

        Returns:
            List of version information dictionaries

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response
        """
        response = self._make_request("GET", f"/api/v1/documents/{source}/versions")
        return response.get("versions", [])

    def compare_versions(
        self, source: str, version1: int, version2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions of a document via API.

        Args:
            source: Source filename
            version1: First version number
            version2: Second version number

        Returns:
            Comparison result dictionary

        Raises:
            APIConnectionError: If connection fails
            APIError: If API returns error response
        """
        response = self._make_request(
            "GET",
            f"/api/v1/documents/{source}/versions/compare",
            params={"version1": version1, "version2": version2},
        )
        return response
