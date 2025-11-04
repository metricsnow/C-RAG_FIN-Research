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
        # Common ticker-to-CIK mapping for major companies
        # This avoids API dependency issues and provides reliable lookups
        TICKER_TO_CIK = {
            "AAPL": "0000320193",  # Apple Inc.
            "MSFT": "0000789019",  # Microsoft Corporation
            "GOOGL": "0001652044",  # Alphabet Inc.
            "AMZN": "0001018724",  # Amazon.com Inc.
            "META": "0001326801",  # Meta Platforms Inc.
            "TSLA": "0001318605",  # Tesla, Inc.
            "NVDA": "0001045810",  # NVIDIA Corporation
            "JPM": "0000019617",   # JPMorgan Chase & Co.
            "V": "0001403161",     # Visa Inc.
            "JNJ": "0000200406",   # Johnson & Johnson
            "WMT": "0000104169",   # Walmart Inc.
            "PG": "0000080424",    # Procter & Gamble Co.
            "MA": "0001141391",    # Mastercard Inc.
            "HD": "0000354950",    # The Home Depot, Inc.
            "DIS": "0001001039",   # The Walt Disney Company
            "BAC": "0000070858",   # Bank of America Corp.
            "XOM": "0000034088",   # Exxon Mobil Corporation
            "VZ": "0000732712",    # Verizon Communications Inc.
            "CVX": "0000093410",   # Chevron Corporation
            "KO": "0000021344",    # The Coca-Cola Company
        }
        
        ticker_upper = ticker.upper()
        if ticker_upper in TICKER_TO_CIK:
            return TICKER_TO_CIK[ticker_upper]
        
        # Fallback: Try API lookup if ticker not in mapping
        try:
            # SEC provides company tickers JSON (may require authentication)
            url = f"{self.BASE_URL}/files/company_tickers.json"
            data = self._make_request(url)
            
            # Search for ticker
            for entry in data.values():
                if isinstance(entry, dict) and entry.get("ticker") == ticker_upper:
                    cik = str(entry.get("cik_str", ""))
                    # Pad CIK to 10 digits
                    return cik.zfill(10)
        except Exception:
            # API lookup failed, but we already tried the mapping
            pass
        
        return None

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

        Based on SEC EDGAR API structure:
        - Base URL: https://www.sec.gov/Archives/edgar/data/
        - Path: {CIK}/{ACCESSION-NUMBER-WITH-DASHES}/filename
        - Accession number format: CIK-YY-SSSSSS (keep dashes)

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
            # SEC EDGAR archive structure (per official documentation)
            # Format: https://www.sec.gov/Archives/edgar/data/CIK/ACC-NUM-WITHOUT-DASHES/primary-document
            # Note: Accession number in URL path has dashes REMOVED, but CIK keeps leading zeros
            base_url = "https://www.sec.gov/Archives/edgar/data"
            
            # Remove dashes from accession number for URL path
            # Example: "0000320193-24-000096" -> "000032019324000096"
            acc_path_no_dashes = accession_number.replace("-", "")
            
            # Also keep version with dashes for index.json (if it exists)
            acc_path_with_dashes = accession_number
            
            # First, try to get the index.json to find the primary document
            # Try both with and without dashes
            index_url_no_dashes = f"{base_url}/{cik}/{acc_path_no_dashes}/index.json"
            index_url_with_dashes = f"{base_url}/{cik}/{acc_path_with_dashes}/index.json"
            primary_document = None
            
            # Try index.json without dashes first (most common format)
            for index_url in [index_url_no_dashes, index_url_with_dashes]:
                try:
                    time.sleep(self.rate_limit_delay)
                    response = self.session.get(index_url, timeout=30)
                    if response.status_code == 200:
                        index_data = response.json()
                        # Parse index structure to find primary document
                        # Index structure: {"directory": {"item": [...]}}
                        if isinstance(index_data, dict):
                            directory = index_data.get("directory", {})
                            if isinstance(directory, dict):
                                items = directory.get("item", [])
                                if not isinstance(items, list):
                                    items = [items] if items else []
                                
                                # Find primary document (usually the main filing document)
                                for item in items:
                                    if isinstance(item, dict):
                                        # Primary documents are usually named like "10k.htm" or "10-k.htm"
                                        doc_name = item.get("name", "")
                                        doc_type = item.get("type", "")
                                        
                                        # Look for primary document matching form type
                                        if form_type.replace("-", "").lower() in doc_name.lower() or \
                                           doc_type == form_type or \
                                           (doc_name and not doc_name.startswith("ex-")):
                                            primary_document = doc_name
                                            # Prefer HTML files for better content
                                            if doc_name.endswith(".htm") or doc_name.endswith(".html"):
                                                break
                        if primary_document:
                            break  # Found primary document, exit loop
                except Exception:
                    # Index lookup failed for this URL, try next
                    continue
            
            # Build list of document names to try (primary document first if found)
            document_names = []
            if primary_document:
                document_names.append(primary_document)
            
            # Add common document name patterns
            # Format: form-type-{accession_number_without_dashes}.{ext}
            acc_no_dashes = accession_number.replace("-", "")
            document_names.extend([
                f"{form_type.lower()}-{acc_no_dashes}.txt",
                f"{form_type.lower()}-{acc_no_dashes}.htm",
                f"{form_type.lower()}.txt",
                f"{form_type.lower()}.htm",
                f"{form_type.replace('-', '')}.txt",
                f"{form_type.replace('-', '')}.htm",
            ])
            
            # Try each document name (use path without dashes)
            for doc_name in document_names:
                url = f"{base_url}/{cik}/{acc_path_no_dashes}/{doc_name}"
                try:
                    time.sleep(self.rate_limit_delay)
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        text = response.text
                        
                        # If HTML, extract text content
                        if doc_name.endswith('.htm') or doc_name.endswith('.html'):
                            import re
                            from html import unescape
                            # Remove script and style tags
                            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                            # Remove HTML tags but preserve structure
                            text = re.sub(r'<[^>]+>', ' ', text)
                            # Decode HTML entities
                            text = unescape(text)
                            # Clean up whitespace
                            text = re.sub(r'\s+', ' ', text)
                            text = text.strip()
                        
                        # Validate content length
                        if text and len(text.strip()) > 100:
                            return text
                except requests.exceptions.RequestException:
                    continue
                except Exception:
                    continue
            
            # If all attempts failed, raise error
            raise EdgarFetcherError(
                f"Could not download filing {accession_number} - tried multiple document formats. "
                f"Tried URLs: {base_url}/{cik}/{acc_path_no_dashes}/[filename]"
            )
            
        except EdgarFetcherError:
            raise
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
        total_companies = len(tickers)
        
        for idx, ticker in enumerate(tickers, 1):
            try:
                print(f"\n[{idx}/{total_companies}] Processing {ticker}...")
                
                # Get CIK for ticker
                print(f"  → Looking up CIK for {ticker}...", end=" ", flush=True)
                cik = self.get_company_cik(ticker)
                if not cik:
                    print(f"✗ Not found")
                    continue
                print(f"✓ CIK: {cik}")
                
                # Get recent filings
                print(f"  → Fetching filing history...", end=" ", flush=True)
                filings = self.get_recent_filings(
                    cik,
                    form_types=form_types,
                    max_filings=max_filings_per_company
                )
                print(f"✓ Found {len(filings)} filings")
                
                if not filings:
                    print(f"  ⚠ No filings found for {ticker}")
                    continue
                
                # Download each filing
                print(f"  → Downloading filings...")
                for filing_idx, filing in enumerate(filings, 1):
                    try:
                        print(f"    [{filing_idx}/{len(filings)}] {filing['form']} ({filing['date']})...", end=" ", flush=True)
                        
                        # Download filing text
                        content = self.download_filing_text(
                            cik,
                            filing["accession_number"],
                            filing["form"]
                        )
                        
                        if not content or len(content.strip()) < 100:
                            print(f"✗ Insufficient content")
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
                        content_size = len(content) // 1024  # Size in KB
                        print(f"✓ Downloaded ({content_size} KB)")
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"✗ Error: {error_msg[:80]}")
                        # Print full error for debugging if it's a download error
                        if "Could not download" in error_msg or "Failed to download" in error_msg:
                            print(f"    Details: {error_msg}")
                        continue
                
                print(f"  ✓ {ticker}: {len([d for d in documents if d.metadata.get('ticker') == ticker])} filings fetched")
                
            except Exception as e:
                print(f"  ✗ Failed to process {ticker}: {str(e)[:50]}")
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

