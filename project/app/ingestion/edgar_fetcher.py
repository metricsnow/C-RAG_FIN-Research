"""
SEC EDGAR data fetcher for downloading free financial filings.

Fetches SEC EDGAR filings using the free public API and converts them
to text format for RAG ingestion.
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from urllib.parse import urljoin

from langchain_core.documents import Document


class EdgarFetcherError(Exception):
    """Custom exception for EDGAR fetcher errors."""

    pass


class EdgarFetcher:
    """
    SEC EDGAR data fetcher.

    Fetches filings from SEC EDGAR using free public APIs.
    Respects rate limits (10 requests per second).
    """

    BASE_URL = "https://data.sec.gov"
    USER_AGENT = "Financial Research Assistant (contact@example.com)"  # SEC requires user agent

    def __init__(self, rate_limit_delay: float = 0.1):
        """
        Initialize EDGAR fetcher.

        Args:
            rate_limit_delay: Delay between requests in seconds (default: 0.1 for 10 req/sec)
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json",
        })

    def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Make HTTP request to SEC EDGAR API with rate limiting.

        Args:
            url: URL to request

        Returns:
            JSON response as dictionary

        Raises:
            EdgarFetcherError: If request fails
        """
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise EdgarFetcherError(f"Failed to fetch from SEC EDGAR: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise EdgarFetcherError(f"Invalid JSON response from SEC EDGAR: {str(e)}") from e

    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get company CIK (Central Index Key) from ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            CIK as zero-padded string, or None if not found

        Raises:
            EdgarFetcherError: If lookup fails
        """
        try:
            # SEC provides company tickers JSON
            url = f"{self.BASE_URL}/files/company_tickers.json"
            data = self._make_request(url)
            
            # Search for ticker
            for entry in data.values():
                if isinstance(entry, dict) and entry.get("ticker") == ticker.upper():
                    cik = str(entry.get("cik_str", ""))
                    # Pad CIK to 10 digits
                    return cik.zfill(10)
            
            return None
        except Exception as e:
            raise EdgarFetcherError(f"Failed to lookup CIK for {ticker}: {str(e)}") from e

    def get_filing_history(self, cik: str) -> Dict[str, Any]:
        """
        Get filing history for a company by CIK.

        Args:
            cik: Company CIK (10-digit zero-padded)

        Returns:
            Filing history dictionary

        Raises:
            EdgarFetcherError: If fetch fails
        """
        if len(cik) != 10 or not cik.isdigit():
            raise EdgarFetcherError(f"Invalid CIK format: {cik}. Must be 10-digit string.")
        
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        return self._make_request(url)

    def get_recent_filings(
        self,
        cik: str,
        form_types: Optional[List[str]] = None,
        max_filings: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent filings for a company.

        Args:
            cik: Company CIK (10-digit zero-padded)
            form_types: List of form types to filter (e.g., ["10-K", "10-Q", "8-K"])
                       If None, returns all forms
            max_filings: Maximum number of filings to return (default: 10)

        Returns:
            List of filing dictionaries sorted by date (most recent first)

        Raises:
            EdgarFetcherError: If fetch fails
        """
        try:
            history = self.get_filing_history(cik)
            
            # Get recent filings
            recent = history.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accession_numbers = recent.get("accessionNumber", [])
            
            filings = []
            for i, form in enumerate(forms):
                if form_types is None or form in form_types:
                    filings.append({
                        "form": form,
                        "date": dates[i] if i < len(dates) else "unknown",
                        "accession_number": accession_numbers[i] if i < len(accession_numbers) else "unknown",
                        "cik": cik,
                    })
            
            # Sort by date (most recent first) and limit
            filings.sort(key=lambda x: x["date"], reverse=True)
            return filings[:max_filings]
            
        except Exception as e:
            raise EdgarFetcherError(f"Failed to get recent filings: {str(e)}") from e

    def download_filing_text(
        self,
        cik: str,
        accession_number: str,
        form_type: str
    ) -> str:
        """
        Download filing text content.

        Args:
            cik: Company CIK (10-digit zero-padded)
            accession_number: Filing accession number (e.g., "0000950170-23-027789")
            form_type: Form type (e.g., "10-K")

        Returns:
            Filing text content

        Raises:
            EdgarFetcherError: If download fails
        """
        try:
            # Convert accession number to path format
            # Example: 0000950170-23-027789 -> 0000950170-23-027789
            acc_num = accession_number.replace("-", "")
            # Format: CIK/accession-number/filing-name.txt
            # For text files, we try the .txt version first
            filing_name = f"{form_type.lower()}-{acc_num}.txt"
            url = f"{self.BASE_URL}/files/data/{cik}/{acc_num}/{filing_name}"
            
            try:
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response.text
            except requests.exceptions.RequestException:
                # Try alternative URL format or HTML version
                pass
            
            # Try HTML version if text not available
            filing_name_html = f"{form_type.lower()}-{acc_num}.htm"
            url_html = f"{self.BASE_URL}/files/data/{cik}/{acc_num}/{filing_name_html}"
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url_html, timeout=30)
            response.raise_for_status()
            
            # Extract text from HTML (simple extraction)
            import re
            from html import unescape
            text = response.text
            # Remove script and style tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Decode HTML entities
            text = unescape(text)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
            
        except Exception as e:
            raise EdgarFetcherError(
                f"Failed to download filing {accession_number}: {str(e)}"
            ) from e

    def fetch_filings_to_documents(
        self,
        tickers: List[str],
        form_types: Optional[List[str]] = None,
        max_filings_per_company: int = 5
    ) -> List[Document]:
        """
        Fetch EDGAR filings and convert to Document objects.

        Args:
            tickers: List of stock ticker symbols
            form_types: List of form types to fetch (e.g., ["10-K", "10-Q", "8-K"])
                       If None, fetches common forms: ["10-K", "10-Q", "8-K"]
            max_filings_per_company: Maximum filings per company (default: 5)

        Returns:
            List of Document objects with filings content

        Raises:
            EdgarFetcherError: If fetch fails
        """
        if form_types is None:
            form_types = ["10-K", "10-Q", "8-K"]
        
        documents = []
        
        for ticker in tickers:
            try:
                # Get CIK for ticker
                cik = self.get_company_cik(ticker)
                if not cik:
                    print(f"Warning: Could not find CIK for ticker {ticker}")
                    continue
                
                # Get recent filings
                filings = self.get_recent_filings(
                    cik,
                    form_types=form_types,
                    max_filings=max_filings_per_company
                )
                
                for filing in filings:
                    try:
                        # Download filing text
                        content = self.download_filing_text(
                            cik,
                            filing["accession_number"],
                            filing["form"]
                        )
                        
                        if not content or len(content.strip()) < 100:
                            print(f"Warning: Filing {filing['accession_number']} has insufficient content")
                            continue
                        
                        # Create Document object
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": f"SEC EDGAR - {ticker}",
                                "filename": f"{ticker}_{filing['form']}_{filing['date']}.txt",
                                "type": "edgar_filing",
                                "ticker": ticker,
                                "cik": cik,
                                "form_type": filing["form"],
                                "filing_date": filing["date"],
                                "accession_number": filing["accession_number"],
                                "date": datetime.now().isoformat(),
                            }
                        )
                        documents.append(doc)
                        print(f"✓ Fetched {ticker} {filing['form']} ({filing['date']})")
                        
                    except Exception as e:
                        print(f"Warning: Failed to download filing {filing['accession_number']}: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"Warning: Failed to fetch filings for {ticker}: {str(e)}")
                continue
        
        return documents

    def save_filings_to_files(
        self,
        documents: List[Document],
        output_dir: Path
    ) -> List[Path]:
        """
        Save Document objects to text files.

        Args:
            documents: List of Document objects
            output_dir: Directory to save files

        Returns:
            List of saved file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []
        
        for doc in documents:
            filename = doc.metadata.get("filename", "unknown.txt")
            file_path = output_dir / filename
            
            try:
                file_path.write_text(doc.page_content, encoding="utf-8")
                saved_paths.append(file_path)
            except Exception as e:
                print(f"Warning: Failed to save {filename}: {str(e)}")
                continue
        
        return saved_paths


def create_edgar_fetcher(rate_limit_delay: float = 0.1) -> EdgarFetcher:
    """
    Create an EDGAR fetcher instance.

    Args:
        rate_limit_delay: Delay between requests in seconds

    Returns:
        EdgarFetcher instance
    """
    return EdgarFetcher(rate_limit_delay=rate_limit_delay)

