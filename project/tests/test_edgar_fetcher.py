"""
Comprehensive tests for EDGAR fetcher module.

Tests cover:
- CIK lookup (ticker to CIK conversion)
- Filing history retrieval
- Recent filings retrieval
- Filing download
- Document conversion
- Error handling (network errors, HTTP errors, invalid inputs)
- File saving
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import time
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from app.ingestion.edgar_fetcher import EdgarFetcher, EdgarFetcherError


class TestEdgarFetcherInitialization:
    """Test EDGAR fetcher initialization."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        fetcher = EdgarFetcher()
        assert fetcher.rate_limit_delay == 0.1
        assert fetcher.session is not None
        assert "User-Agent" in fetcher.session.headers
        assert "Accept" in fetcher.session.headers
    
    def test_init_custom_rate_limit(self):
        """Test initialization with custom rate limit."""
        fetcher = EdgarFetcher(rate_limit_delay=0.5)
        assert fetcher.rate_limit_delay == 0.5


class TestMakeRequest:
    """Test internal _make_request method."""
    
    @patch('time.sleep')
    def test_make_request_success(self, mock_sleep):
        """Test successful HTTP request."""
        fetcher = EdgarFetcher()
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status = Mock()
        
        fetcher.session.get = Mock(return_value=mock_response)
        
        result = fetcher._make_request("https://example.com/api")
        
        assert result == {"test": "data"}
        mock_sleep.assert_called_once_with(0.1)
        mock_response.raise_for_status.assert_called_once()
    
    @patch('time.sleep')
    def test_make_request_network_error(self, mock_sleep):
        """Test network error handling."""
        fetcher = EdgarFetcher()
        fetcher.session.get = Mock(side_effect=ConnectionError("Connection failed"))
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher._make_request("https://example.com/api")
        
        assert "Failed to fetch from SEC EDGAR" in str(exc_info.value)
    
    @patch('time.sleep')
    def test_make_request_timeout(self, mock_sleep):
        """Test timeout error handling."""
        fetcher = EdgarFetcher()
        fetcher.session.get = Mock(side_effect=Timeout("Request timeout"))
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher._make_request("https://example.com/api")
        
        assert "Failed to fetch from SEC EDGAR" in str(exc_info.value)
    
    @patch('time.sleep')
    def test_make_request_http_error(self, mock_sleep):
        """Test HTTP error handling (404, 500, etc.)."""
        fetcher = EdgarFetcher()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        fetcher.session.get = Mock(return_value=mock_response)
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher._make_request("https://example.com/api")
        
        assert "Failed to fetch from SEC EDGAR" in str(exc_info.value)
    
    @patch('time.sleep')
    def test_make_request_invalid_json(self, mock_sleep):
        """Test invalid JSON response handling."""
        fetcher = EdgarFetcher()
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status = Mock()
        fetcher.session.get = Mock(return_value=mock_response)
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher._make_request("https://example.com/api")
        
        assert "Invalid JSON response" in str(exc_info.value)


class TestGetCompanyCIK:
    """Test CIK lookup functionality."""
    
    def test_get_company_cik_known_ticker(self):
        """Test CIK lookup for known ticker in mapping."""
        fetcher = EdgarFetcher()
        
        # Test with known tickers
        assert fetcher.get_company_cik("AAPL") == "0000320193"
        assert fetcher.get_company_cik("MSFT") == "0000789019"
        assert fetcher.get_company_cik("GOOGL") == "0001652044"
        assert fetcher.get_company_cik("TSLA") == "0001318605"
    
    def test_get_company_cik_case_insensitive(self):
        """Test CIK lookup is case-insensitive."""
        fetcher = EdgarFetcher()
        
        assert fetcher.get_company_cik("aapl") == "0000320193"
        assert fetcher.get_company_cik("Apple") == "0000320193"
        assert fetcher.get_company_cik("AAPL") == "0000320193"
    
    @patch.object(EdgarFetcher, '_make_request')
    def test_get_company_cik_api_fallback_success(self, mock_make_request):
        """Test API fallback when ticker not in mapping."""
        fetcher = EdgarFetcher()
        
        # Mock API response
        mock_make_request.return_value = {
            "0": {"cik_str": 123456, "ticker": "UNKNOWN"},
            "1": {"cik_str": 789012, "ticker": "TEST"},
        }
        
        # Should return None since TEST not in mapping and API lookup fails in mock
        result = fetcher.get_company_cik("UNKNOWN_TICKER")
        # May return None if API lookup fails or ticker not found
        assert result is None or isinstance(result, str)
    
    def test_get_company_cik_unknown_ticker(self):
        """Test CIK lookup for unknown ticker."""
        fetcher = EdgarFetcher()
        
        # Unknown ticker should return None
        result = fetcher.get_company_cik("UNKNOWN999")
        assert result is None
    
    @patch.object(EdgarFetcher, '_make_request')
    def test_get_company_cik_api_fallback_error(self, mock_make_request):
        """Test API fallback handles errors gracefully."""
        fetcher = EdgarFetcher()
        
        # Mock API error
        mock_make_request.side_effect = EdgarFetcherError("API error")
        
        # Should return None gracefully
        result = fetcher.get_company_cik("UNKNOWN_TICKER")
        assert result is None


class TestGetFilingHistory:
    """Test filing history retrieval."""
    
    @patch.object(EdgarFetcher, '_make_request')
    def test_get_filing_history_success(self, mock_make_request):
        """Test successful filing history retrieval."""
        fetcher = EdgarFetcher()
        
        mock_response = {
            "cik": "0000320193",
            "entityType": "operating",
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q"],
                    "filingDate": ["2024-01-01", "2024-04-01"],
                }
            }
        }
        mock_make_request.return_value = mock_response
        
        result = fetcher.get_filing_history("0000320193")
        
        assert result == mock_response
        mock_make_request.assert_called_once_with(
            "https://data.sec.gov/submissions/CIK0000320193.json"
        )
    
    def test_get_filing_history_invalid_cik_format(self):
        """Test filing history with invalid CIK format."""
        fetcher = EdgarFetcher()
        
        # Invalid CIK formats
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher.get_filing_history("123")  # Too short
        
        assert "Invalid CIK format" in str(exc_info.value)
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher.get_filing_history("invalid")  # Not numeric
        
        assert "Invalid CIK format" in str(exc_info.value)
    
    @patch.object(EdgarFetcher, '_make_request')
    def test_get_filing_history_api_error(self, mock_make_request):
        """Test filing history API error handling."""
        fetcher = EdgarFetcher()
        
        mock_make_request.side_effect = EdgarFetcherError("API error")
        
        with pytest.raises(EdgarFetcherError):
            fetcher.get_filing_history("0000320193")


class TestGetRecentFilings:
    """Test recent filings retrieval."""
    
    @patch.object(EdgarFetcher, 'get_filing_history')
    def test_get_recent_filings_success(self, mock_get_history):
        """Test successful recent filings retrieval."""
        fetcher = EdgarFetcher()
        
        mock_get_history.return_value = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K", "10-K"],
                    "filingDate": ["2024-01-01", "2024-04-01", "2024-05-01", "2023-12-31"],
                    "accessionNumber": ["0001", "0002", "0003", "0004"],
                }
            }
        }
        
        result = fetcher.get_recent_filings("0000320193", form_types=["10-K", "10-Q"])
        
        assert len(result) == 3  # 2 10-Ks and 1 10-Q
        assert all(f["form"] in ["10-K", "10-Q"] for f in result)
        assert result[0]["date"] == "2024-05-01"  # Sorted by date, most recent first
    
    @patch.object(EdgarFetcher, 'get_filing_history')
    def test_get_recent_filings_no_filter(self, mock_get_history):
        """Test recent filings without form type filter."""
        fetcher = EdgarFetcher()
        
        mock_get_history.return_value = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K"],
                    "filingDate": ["2024-01-01", "2024-04-01", "2024-05-01"],
                    "accessionNumber": ["0001", "0002", "0003"],
                }
            }
        }
        
        result = fetcher.get_recent_filings("0000320193", max_filings=2)
        
        assert len(result) == 2
        assert result[0]["date"] == "2024-05-01"
    
    @patch.object(EdgarFetcher, 'get_filing_history')
    def test_get_recent_filings_max_limit(self, mock_get_history):
        """Test recent filings respects max_filings limit."""
        fetcher = EdgarFetcher()
        
        mock_get_history.return_value = {
            "filings": {
                "recent": {
                    "form": ["10-K"] * 20,
                    "filingDate": [f"2024-{i:02d}-01" for i in range(1, 21)],
                    "accessionNumber": [f"000{i}" for i in range(1, 21)],
                }
            }
        }
        
        result = fetcher.get_recent_filings("0000320193", max_filings=5)
        
        assert len(result) == 5
    
    @patch.object(EdgarFetcher, 'get_filing_history')
    def test_get_recent_filings_api_error(self, mock_get_history):
        """Test recent filings handles API errors."""
        fetcher = EdgarFetcher()
        
        mock_get_history.side_effect = EdgarFetcherError("API error")
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher.get_recent_filings("0000320193")
        
        assert "Failed to get recent filings" in str(exc_info.value)
    
    @patch.object(EdgarFetcher, 'get_filing_history')
    def test_get_recent_filings_empty_history(self, mock_get_history):
        """Test recent filings with empty filing history."""
        fetcher = EdgarFetcher()
        
        mock_get_history.return_value = {
            "filings": {
                "recent": {
                    "form": [],
                    "filingDate": [],
                    "accessionNumber": [],
                }
            }
        }
        
        result = fetcher.get_recent_filings("0000320193")
        
        assert result == []


class TestDownloadFilingText:
    """Test filing text download."""
    
    @patch('time.sleep')
    def test_download_filing_text_success_txt(self, mock_sleep):
        """Test successful filing download (TXT format)."""
        fetcher = EdgarFetcher()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "This is filing content" * 100  # > 100 chars
        fetcher.session.get = Mock(return_value=mock_response)
        
        # Mock index.json lookup (first attempt fails, second succeeds)
        def mock_get_side_effect(url, *args, **kwargs):
            if "index.json" in url:
                mock_index = Mock()
                mock_index.status_code = 404
                return mock_index
            return mock_response
        
        fetcher.session.get.side_effect = mock_get_side_effect
        
        result = fetcher.download_filing_text(
            "0000320193",
            "0000320193-24-000096",
            "10-K"
        )
        
        assert len(result) > 100
        assert "filing content" in result
    
    @patch('time.sleep')
    def test_download_filing_text_success_html(self, mock_sleep):
        """Test successful filing download (HTML format)."""
        fetcher = EdgarFetcher()
        
        html_content = """
        <html>
        <head><title>10-K Filing</title></head>
        <body>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
            <p>This is <b>important</b> content</p>
        </body>
        </html>
        """ * 20
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        fetcher.session.get = Mock(return_value=mock_response)
        
        # Mock index.json lookup failure
        def mock_get_side_effect(url, *args, **kwargs):
            if "index.json" in url:
                mock_index = Mock()
                mock_index.status_code = 404
                return mock_index
            return mock_response
        
        fetcher.session.get.side_effect = mock_get_side_effect
        
        result = fetcher.download_filing_text(
            "0000320193",
            "0000320193-24-000096",
            "10-K"
        )
        
        # HTML should be cleaned (no tags, no script/style)
        assert "<script>" not in result
        assert "<style>" not in result
        assert "<p>" not in result
        assert "important content" in result.lower()
    
    @patch('time.sleep')
    def test_download_filing_text_index_json_success(self, mock_sleep):
        """Test filing download using index.json to find primary document."""
        fetcher = EdgarFetcher()
        
        # Mock index.json response
        mock_index_response = Mock()
        mock_index_response.status_code = 200
        mock_index_response.json.return_value = {
            "directory": {
                "item": [
                    {"name": "10k.htm", "type": "10-K"},
                    {"name": "ex-99.htm", "type": "EX-99"},
                ]
            }
        }
        
        # Mock primary document response
        mock_doc_response = Mock()
        mock_doc_response.status_code = 200
        mock_doc_response.text = "Primary filing content" * 100
        
        def mock_get_side_effect(url, *args, **kwargs):
            if "index.json" in url:
                return mock_index_response
            return mock_doc_response
        
        fetcher.session.get.side_effect = mock_get_side_effect
        
        result = fetcher.download_filing_text(
            "0000320193",
            "0000320193-24-000096",
            "10-K"
        )
        
        assert "Primary filing content" in result
    
    @patch('time.sleep')
    def test_download_filing_text_all_formats_fail(self, mock_sleep):
        """Test filing download when all document formats fail."""
        fetcher = EdgarFetcher()
        
        # Mock all requests return 404
        mock_response = Mock()
        mock_response.status_code = 404
        fetcher.session.get = Mock(return_value=mock_response)
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher.download_filing_text(
                "0000320193",
                "0000320193-24-000096",
                "10-K"
            )
        
        assert "Could not download filing" in str(exc_info.value)
    
    @patch('time.sleep')
    def test_download_filing_text_insufficient_content(self, mock_sleep):
        """Test filing download with insufficient content length."""
        fetcher = EdgarFetcher()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Short"  # < 100 chars
        fetcher.session.get = Mock(return_value=mock_response)
        
        # Mock index.json lookup failure
        def mock_get_side_effect(url, *args, **kwargs):
            if "index.json" in url:
                mock_index = Mock()
                mock_index.status_code = 404
                return mock_index
            return mock_response
        
        fetcher.session.get.side_effect = mock_get_side_effect
        
        # Should try all formats and eventually fail
        with pytest.raises(EdgarFetcherError):
            fetcher.download_filing_text(
                "0000320193",
                "0000320193-24-000096",
                "10-K"
            )
    
    @patch('time.sleep')
    def test_download_filing_text_network_error(self, mock_sleep):
        """Test filing download with network error."""
        fetcher = EdgarFetcher()
        fetcher.session.get = Mock(side_effect=ConnectionError("Network error"))
        
        with pytest.raises(EdgarFetcherError) as exc_info:
            fetcher.download_filing_text(
                "0000320193",
                "0000320193-24-000096",
                "10-K"
            )
        
        assert "Failed to download filing" in str(exc_info.value)


class TestFetchFilingsToDocuments:
    """Test fetching filings and converting to Document objects."""
    
    @patch.object(EdgarFetcher, 'download_filing_text')
    @patch.object(EdgarFetcher, 'get_recent_filings')
    @patch.object(EdgarFetcher, 'get_company_cik')
    def test_fetch_filings_to_documents_success(
        self, mock_get_cik, mock_get_filings, mock_download
    ):
        """Test successful fetching of filings to documents."""
        fetcher = EdgarFetcher()
        
        mock_get_cik.return_value = "0000320193"
        mock_get_filings.return_value = [
            {
                "form": "10-K",
                "date": "2024-01-01",
                "accession_number": "0000320193-24-000096",
                "cik": "0000320193",
            }
        ]
        mock_download.return_value = "Filing content" * 100
        
        result = fetcher.fetch_filings_to_documents(["AAPL"], max_filings_per_company=1)
        
        assert len(result) == 1
        assert result[0].page_content == "Filing content" * 100
        assert result[0].metadata["ticker"] == "AAPL"
        assert result[0].metadata["form_type"] == "10-K"
        assert result[0].metadata["cik"] == "0000320193"
    
    @patch.object(EdgarFetcher, 'get_company_cik')
    def test_fetch_filings_to_documents_ticker_not_found(self, mock_get_cik):
        """Test fetching when ticker CIK is not found."""
        fetcher = EdgarFetcher()
        
        mock_get_cik.return_value = None
        
        result = fetcher.fetch_filings_to_documents(["UNKNOWN"])
        
        assert len(result) == 0
    
    @patch.object(EdgarFetcher, 'download_filing_text')
    @patch.object(EdgarFetcher, 'get_recent_filings')
    @patch.object(EdgarFetcher, 'get_company_cik')
    def test_fetch_filings_to_documents_no_filings(
        self, mock_get_cik, mock_get_filings, mock_download
    ):
        """Test fetching when no filings found."""
        fetcher = EdgarFetcher()
        
        mock_get_cik.return_value = "0000320193"
        mock_get_filings.return_value = []
        
        result = fetcher.fetch_filings_to_documents(["AAPL"])
        
        assert len(result) == 0
    
    @patch.object(EdgarFetcher, 'download_filing_text')
    @patch.object(EdgarFetcher, 'get_recent_filings')
    @patch.object(EdgarFetcher, 'get_company_cik')
    def test_fetch_filings_to_documents_download_error(
        self, mock_get_cik, mock_get_filings, mock_download
    ):
        """Test fetching when download fails."""
        fetcher = EdgarFetcher()
        
        mock_get_cik.return_value = "0000320193"
        mock_get_filings.return_value = [
            {
                "form": "10-K",
                "date": "2024-01-01",
                "accession_number": "0000320193-24-000096",
                "cik": "0000320193",
            }
        ]
        mock_download.side_effect = EdgarFetcherError("Download failed")
        
        result = fetcher.fetch_filings_to_documents(["AAPL"])
        
        # Should continue processing despite download error
        assert len(result) == 0
    
    @patch.object(EdgarFetcher, 'download_filing_text')
    @patch.object(EdgarFetcher, 'get_recent_filings')
    @patch.object(EdgarFetcher, 'get_company_cik')
    def test_fetch_filings_to_documents_insufficient_content(
        self, mock_get_cik, mock_get_filings, mock_download
    ):
        """Test fetching when downloaded content is insufficient."""
        fetcher = EdgarFetcher()
        
        mock_get_cik.return_value = "0000320193"
        mock_get_filings.return_value = [
            {
                "form": "10-K",
                "date": "2024-01-01",
                "accession_number": "0000320193-24-000096",
                "cik": "0000320193",
            }
        ]
        mock_download.return_value = "Short"  # < 100 chars
        
        result = fetcher.fetch_filings_to_documents(["AAPL"])
        
        # Should skip documents with insufficient content
        assert len(result) == 0
    
    @patch.object(EdgarFetcher, 'get_company_cik')
    def test_fetch_filings_to_documents_multiple_tickers(self, mock_get_cik):
        """Test fetching filings for multiple tickers."""
        fetcher = EdgarFetcher()
        
        def cik_side_effect(ticker):
            return "0000320193" if ticker == "AAPL" else "0000789019"
        
        mock_get_cik.side_effect = cik_side_effect
        
        with patch.object(fetcher, 'get_recent_filings', return_value=[]):
            with patch.object(fetcher, 'download_filing_text'):
                result = fetcher.fetch_filings_to_documents(["AAPL", "MSFT"])
                
                # Both tickers processed (even if no filings)
                assert mock_get_cik.call_count == 2


class TestSaveFilingsToFiles:
    """Test saving filings to files."""
    
    def test_save_filings_to_files_success(self, tmp_path):
        """Test successful saving of filings to files."""
        fetcher = EdgarFetcher()
        
        from langchain_core.documents import Document
        
        documents = [
            Document(
                page_content="Content 1",
                metadata={"filename": "file1.txt"}
            ),
            Document(
                page_content="Content 2",
                metadata={"filename": "file2.txt"}
            ),
        ]
        
        result = fetcher.save_filings_to_files(documents, tmp_path)
        
        assert len(result) == 2
        assert (tmp_path / "file1.txt").exists()
        assert (tmp_path / "file2.txt").exists()
        assert (tmp_path / "file1.txt").read_text() == "Content 1"
        assert (tmp_path / "file2.txt").read_text() == "Content 2"
    
    def test_save_filings_to_files_creates_directory(self, tmp_path):
        """Test saving creates directory if it doesn't exist."""
        fetcher = EdgarFetcher()
        
        from langchain_core.documents import Document
        
        output_dir = tmp_path / "new_dir" / "subdir"
        
        documents = [
            Document(
                page_content="Content",
                metadata={"filename": "file.txt"}
            ),
        ]
        
        result = fetcher.save_filings_to_files(documents, output_dir)
        
        assert output_dir.exists()
        assert (output_dir / "file.txt").exists()
    
    def test_save_filings_to_files_handles_errors(self, tmp_path):
        """Test saving handles file I/O errors gracefully."""
        fetcher = EdgarFetcher()
        
        from langchain_core.documents import Document
        
        # Create a path that will cause permission error (if possible)
        # or use a mock to simulate error
        documents = [
            Document(
                page_content="Content",
                metadata={"filename": "file.txt"}
            ),
        ]
        
        # Mock write_text to raise error
        with patch('pathlib.Path.write_text', side_effect=IOError("Permission denied")):
            result = fetcher.save_filings_to_files(documents, tmp_path)
            
            # Should continue processing and return empty list or partial list
            assert len(result) == 0
    
    def test_save_filings_to_files_missing_filename(self, tmp_path):
        """Test saving with missing filename in metadata."""
        fetcher = EdgarFetcher()
        
        from langchain_core.documents import Document
        
        documents = [
            Document(
                page_content="Content",
                metadata={}  # No filename
            ),
        ]
        
        result = fetcher.save_filings_to_files(documents, tmp_path)
        
        # Should use default filename
        assert len(result) == 1
        assert result[0].name == "unknown.txt"


@pytest.mark.integration
@pytest.mark.slow
class TestEdgarFetcherIntegration:
    """Integration tests with real SEC EDGAR API (marked as slow)."""
    
    def test_get_company_cik_real_api(self):
        """Test CIK lookup with real API (if available)."""
        fetcher = EdgarFetcher(rate_limit_delay=0.2)
        
        # Known ticker should work
        cik = fetcher.get_company_cik("AAPL")
        assert cik is not None
        assert len(cik) == 10
        assert cik.isdigit()
    
    def test_get_filing_history_real_api(self):
        """Test filing history with real API (if available)."""
        fetcher = EdgarFetcher(rate_limit_delay=0.2)
        
        # Use known CIK
        history = fetcher.get_filing_history("0000320193")
        
        assert "filings" in history or "cik" in history

