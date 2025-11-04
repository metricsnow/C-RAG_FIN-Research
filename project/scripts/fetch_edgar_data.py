"""
Script to fetch SEC EDGAR filings and ingest them into the RAG system.

This script:
1. Fetches free EDGAR filings from SEC
2. Converts them to text format
3. Ingests them into ChromaDB via the ingestion pipeline
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion import IngestionPipeline, create_pipeline
from app.ingestion.edgar_fetcher import EdgarFetcher, EdgarFetcherError, create_edgar_fetcher
from app.utils.config import config


def main():
    """Main function to fetch and ingest EDGAR data."""
    print("\n" + "="*60)
    print("SEC EDGAR Data Fetching and Ingestion")
    print("="*60)
    
    # Popular financial companies for initial data collection
    # These will provide a good mix of 10-K, 10-Q, and 8-K filings
    tickers = [
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "GOOGL", # Alphabet
        "AMZN",  # Amazon
        "META",  # Meta
        "TSLA",  # Tesla
        "NVDA",  # NVIDIA
        "JPM",   # JPMorgan Chase
        "V",     # Visa
        "JNJ",   # Johnson & Johnson
    ]
    
    # Form types to fetch (10-K annual reports, 10-Q quarterly, 8-K current events)
    form_types = ["10-K", "10-Q", "8-K"]
    
    print(f"\nFetching EDGAR filings for {len(tickers)} companies...")
    print(f"Form types: {', '.join(form_types)}")
    print(f"Target: 5 filings per company (up to {len(tickers) * 5} total)\n")
    
    try:
        # Create EDGAR fetcher
        edgar_fetcher = create_edgar_fetcher(rate_limit_delay=0.1)
        print("✓ EDGAR fetcher initialized")
        
        # Fetch filings
        print("\nFetching filings from SEC EDGAR...")
        documents = edgar_fetcher.fetch_filings_to_documents(
            tickers=tickers,
            form_types=form_types,
            max_filings_per_company=5
        )
        
        print(f"\n✓ Fetched {len(documents)} filings")
        
        if not documents:
            print("⚠ No documents fetched. Exiting.")
            return 1
        
        # Optionally save to files
        save_to_files = True
        if save_to_files:
            output_dir = config.DOCUMENTS_DIR / "edgar_filings"
            saved_paths = edgar_fetcher.save_filings_to_files(documents, output_dir)
            print(f"✓ Saved {len(saved_paths)} filings to {output_dir}")
        
        # Ingest into ChromaDB
        print("\n" + "="*60)
        print("Ingesting EDGAR filings into ChromaDB...")
        print("="*60)
        
        pipeline = create_pipeline(collection_name="documents")
        
        # Process documents directly from Document objects
        print(f"\nProcessing {len(documents)} documents...")
        
        chunk_ids = pipeline.process_document_objects(documents)
        print(f"✓ Ingested {len(chunk_ids)} chunks into ChromaDB")
        
        # Verify ingestion
        doc_count = pipeline.get_document_count()
        print(f"✓ Total documents in ChromaDB: {doc_count}")
        
        print("\n" + "="*60)
        print("EDGAR Data Ingestion Complete!")
        print("="*60)
        print(f"  - Filings fetched: {len(documents)}")
        if save_to_files:
            print(f"  - Files saved: {len(saved_paths)}")
        print(f"  - Chunks ingested: {len(chunk_ids)}")
        print(f"  - Total documents in DB: {doc_count}")
        print("\n✓ EDGAR data is now available in your RAG system!")
        
        return 0
        
    except EdgarFetcherError as e:
        print(f"\n✗ EDGAR fetch error: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

