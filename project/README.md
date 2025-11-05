# Contextual RAG-Powered Financial Research Assistant

A production-ready RAG (Retrieval-Augmented Generation) system for semantic search across financial documents, featuring local LLM deployment with Ollama and comprehensive citation tracking.

## Project Structure

```
project/
├── app/                    # Application source code
│   ├── ingestion/          # Document ingestion pipeline
│   ├── rag/                # RAG chain implementation
│   ├── ui/                 # Streamlit frontend
│   ├── vector_db/          # ChromaDB integration
│   └── utils/              # Utility functions
├── data/                   # Data storage
│   ├── documents/          # Source documents (PDFs, Markdown, text)
│   └── chroma_db/          # ChromaDB persistence directory
├── tests/                  # Test files
├── docs/                   # Documentation
│   ├── deployment.md       # Deployment guide
│   ├── edgar_integration.md # SEC EDGAR integration docs
│   └── prd.md              # Product requirements document
├── dev/                    # Development tasks and bugs
├── scripts/                # Utility scripts
│   ├── deploy_local.sh     # Local deployment script
│   ├── deploy_with_ngrok.sh # ngrok deployment script
│   └── ...                 # Other utility scripts
├── .streamlit/             # Streamlit configuration
│   └── config.toml         # Production configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Prerequisites

- Python 3.11 or higher
- Ollama installed and running locally
- (Optional) OpenAI API key for embeddings

## Setup Instructions

### 1. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key (if using OpenAI embeddings)
```

### 4. Verify Ollama Installation

Ensure Ollama is running and a model is downloaded:

```bash
ollama serve  # Start Ollama server (if not running)
ollama pull llama3.2  # Or mistral
# Test the installation:
python scripts/test_ollama.py
```

### 5. Validate Setup

Run the validation script to verify all dependencies:

```bash
python scripts/validate_setup.py
```

## Development Workflow

1. Always activate virtual environment before working:
   ```bash
   source venv/bin/activate
   ```

2. Follow task structure in `dev/tasks/` directory
3. Reference PRD in `docs/prd.md` for requirements

## Current Status

### Completed Tasks
- ✅ **TASK-001**: Environment Setup and Dependency Management
  - Virtual environment created and configured
  - All dependencies installed (langchain, streamlit, chromadb, etc.)
  - Project structure initialized
  - Configuration management implemented
- ✅ **TASK-002**: Ollama Installation and Model Configuration
  - Ollama installed and running at `http://localhost:11434`
  - Llama 3.2 model downloaded (2.0 GB)
  - API endpoint verified and tested
  - Test script created (`scripts/test_ollama.py`)
  - Response time: ~0.4 seconds (excellent performance)
- ✅ **TASK-003**: LangChain Framework Integration and Basic RAG Chain
  - Ollama LLM integration via langchain_community
  - Basic RAG chain implementation using LangChain 1.0+ LCEL
  - Document loading and text splitting
  - Configuration module for environment variables
  - Test script for RAG chain validation
- ✅ **TASK-004**: Document Ingestion Pipeline - Text and Markdown Support
  - Document loader module with TextLoader and MarkdownLoader support
  - RecursiveCharacterTextSplitter with chunk_size=1000, overlap=200
  - Comprehensive metadata management (source, filename, type, date, chunk_index)
  - File size validation (max 10MB)
  - Error handling for corrupted/unsupported files
  - Test suite with 6 test cases (all passing)
  - Implementation: `app/ingestion/document_loader.py`
- ✅ **TASK-005**: ChromaDB Integration and Vector Database Setup
  - Persistent ChromaDB client with automatic collection management
  - Document addition with embeddings support
  - Similarity search by embedding or text
  - Document retrieval by ID with metadata filtering
  - Test suite with 7 test cases (all passing)
  - Implementation: `app/vector_db/chroma_store.py`
  - Storage location: `data/chroma_db/` (persistent)
- ✅ **TASK-006**: Embedding Generation and Storage Integration
  - Embedding factory supporting OpenAI (text-embedding-3-small) and Ollama
  - Batch embedding generation for document chunks
  - Complete ingestion pipeline integrating document loading, chunking, embeddings, and ChromaDB
  - End-to-end processing: document → chunks → embeddings → storage
  - Similarity search integration
  - Test suite with 4 test cases (all passing)
  - Implementation: `app/rag/embedding_factory.py`, `app/ingestion/pipeline.py`
  - Embedding dimensions: 1536 (OpenAI text-embedding-3-small)
- ✅ **TASK-007**: RAG Query System Implementation
  - Complete RAG query system with LangChain Expression Language (LCEL) chain pattern
  - Natural language query processing with query embedding generation
  - Vector similarity search in ChromaDB with configurable top-k (default: 5)
  - Context retrieval and formatting for LLM prompts
  - Financial domain-optimized prompt template
  - Ollama LLM integration for answer generation
  - Comprehensive error handling (empty results, LLM failures, invalid inputs)
  - Test suite with 7 test cases (all passing)
  - Implementation: `app/rag/chain.py` (RAGQuerySystem class)
  - Test script: `scripts/test_rag_query.py`
- ✅ **TASK-008**: Streamlit Frontend - Basic Chat Interface
  - Basic chat interface using Streamlit `st.chat_input` and `st.chat_message` components
  - Direct integration with RAG query system (no API layer)
  - Session state management for chat history
  - Simple citation display: "Source: document.pdf" format
  - Error handling with user-friendly error messages
  - Single-turn queries (no conversation history sidebar for MVP)
  - Implementation: `app/ui/app.py` (Streamlit application)
  - Run script: `scripts/run_streamlit.py`
- ✅ **TASK-009**: Citation Tracking Implementation
  - Citation tracking system fully implemented and verified
  - Source metadata extraction from retrieved chunks
  - Citation formatting: "Source: filename.pdf" for single source, "Sources: file1.pdf, file2.txt" for multiple
  - Integration with Streamlit UI displaying citations below each answer
  - Comprehensive test suite: `scripts/test_citation_tracking.py` (5 test cases, all passing)
  - Implementation: `app/ui/app.py` (format_citations function)
- ✅ **TASK-010**: Financial Document Collection and Indexing
  - SEC EDGAR data fetcher implemented (`app/ingestion/edgar_fetcher.py`)
  - Free public SEC EDGAR API integration with comprehensive status printing
  - Automated fetching and ingestion script: `scripts/fetch_edgar_data.py`
  - Supports fetching 10-K, 10-Q, and 8-K filings from major companies
  - **50 documents collected** from 10 companies (AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, V, JNJ)
  - **511 chunks generated** from 50 documents
  - All documents indexed in ChromaDB and verified as searchable
  - Verification script: `scripts/verify_document_indexing.py`
  - Direct Document object processing in ingestion pipeline
- ✅ **TASK-011**: System Testing and Integration Debugging
  - Comprehensive system integration test suite: `scripts/test_system_integration.py` (11 tests)
  - Streamlit UI integration tests: `scripts/test_streamlit_integration.py` (4 tests)
  - All 15 tests passed successfully
  - Performance benchmarks validated: Average response time 3.46s (target: <5s) ✓
  - Component testing: Document ingestion, embedding generation, vector DB, RAG query system
  - Query type testing: Financial terminology, general research, specific document queries
  - Error handling validated: Empty queries, invalid documents, graceful error recovery
  - End-to-end integration validated: Document → ingestion → query → citations
  - Bug fixes: LLM factory deprecation warning (langchain-ollama support with fallback)
  - All system components working together correctly
- ✅ **TASK-012**: Deployment Setup and Configuration
  - Streamlit production configuration (`.streamlit/config.toml`)
  - Local deployment script (`scripts/deploy_local.sh`)
  - ngrok deployment script (`scripts/deploy_with_ngrok.sh`) for external access
  - Comprehensive deployment documentation (`docs/deployment.md`)
  - Three deployment options: Local, ngrok tunneling, VPS production
  - Service management and troubleshooting guides
  - Security configuration and best practices

### Deployment

The system is ready for deployment with multiple options:

#### Quick Local Deployment

```bash
# Activate virtual environment
source venv/bin/activate

# Run local deployment script
bash scripts/deploy_local.sh
```

The app will be available at `http://localhost:8501`.

#### External Access with ngrok

For demos or external access, use ngrok tunneling:

```bash
# Install ngrok first (if not installed)
# macOS: brew install ngrok/ngrok/ngrok

# Run deployment with ngrok
bash scripts/deploy_with_ngrok.sh
```

This provides a public URL for external access.

#### Production VPS Deployment

For production deployment on a VPS, see the comprehensive guide:

```bash
# See detailed instructions in:
docs/deployment.md
```

The deployment guide includes:
- VPS setup instructions
- Systemd service configuration
- Nginx reverse proxy setup
- SSL certificate configuration
- Service management and troubleshooting

**For complete deployment documentation, see:** [`docs/deployment.md`](docs/deployment.md)

### Running the Streamlit App

After setup and document ingestion, run the Streamlit frontend:

```bash
# Option 1: Using the run script
python scripts/run_streamlit.py

# Option 2: Direct Streamlit command
streamlit run app/ui/app.py
```

The app will open in your browser at `http://localhost:8501`.

### Data Collection

#### SEC EDGAR Data (Free Public API)

The system includes an automated SEC EDGAR data fetcher that downloads free financial filings:

```bash
# Fetch and ingest EDGAR filings from major companies
python -u scripts/fetch_edgar_data.py
```

This will fetch 50 EDGAR filings from 10 major companies, convert them to text, and ingest them into ChromaDB. The script provides detailed progress information including:
- Company progress tracking `[1/10]`, `[2/10]`, etc.
- CIK lookup status
- Individual filing download progress with file sizes
- Ingestion progress with timing information

**Verification:**
```bash
# Verify documents are indexed and searchable
python -u scripts/verify_document_indexing.py
```

**Features:**
- Fetches filings from 10 major companies (AAPL, MSFT, GOOGL, AMZN, etc.)
- Downloads 10-K (annual reports), 10-Q (quarterly reports), and 8-K (current events) forms
- Automatically converts to text format and ingests into ChromaDB
- Rate limiting (respects SEC guidelines: 10 requests/second)
- Rich metadata (ticker, CIK, form type, filing date)

**EDGAR Fetcher Module:**
- `app/ingestion/edgar_fetcher.py`: SEC EDGAR API integration
- `scripts/fetch_edgar_data.py`: Automated fetching and ingestion script

**Usage:**
```python
from app.ingestion import create_edgar_fetcher, create_pipeline

# Fetch EDGAR filings
edgar_fetcher = create_edgar_fetcher()
documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=["AAPL", "MSFT"],
    form_types=["10-K", "10-Q"],
    max_filings_per_company=5
)

# Ingest into ChromaDB
pipeline = create_pipeline()
chunk_ids = pipeline.process_document_objects(documents)
```

#### Manual Document Ingestion

Place documents in `data/documents/` directory:
- Text files (`.txt`)
- Markdown files (`.md`)

Then process through the ingestion pipeline.

### Next Steps

After setup, proceed with:
- **TASK-013**: README and Documentation Creation (deployment setup complete)

## Architecture

### Implemented Components

- **Configuration Management** (`app/utils/config.py`): Loads environment variables from `.env`
- **LLM Factory** (`app/rag/llm_factory.py`): Creates and configures Ollama LLM instances
- **RAG Query System** (`app/rag/chain.py`): Complete RAG query system using LangChain Expression Language (LCEL)
  - Natural language query processing
  - Query embedding generation
  - Vector similarity search in ChromaDB
  - Context retrieval (top-k chunks)
  - Financial domain-optimized prompt template
  - LLM answer generation via Ollama
- **Streamlit Frontend** (`app/ui/app.py`): Basic chat interface for querying documents
  - Chat interface using Streamlit chat components
  - Direct RAG system integration
  - Session state management
  - Simple citation display
  - Error handling
- **Document Ingestion** (`app/ingestion/document_loader.py`): Text and Markdown document processing with chunking
- **Ingestion Pipeline** (`app/ingestion/pipeline.py`): Complete end-to-end pipeline (document → chunks → embeddings → ChromaDB)
- **EDGAR Fetcher** (`app/ingestion/edgar_fetcher.py`): SEC EDGAR API integration for automated financial document fetching
- **Embedding Generation** (`app/rag/embedding_factory.py`): OpenAI and Ollama embedding generation with batch processing
- **ChromaDB Integration** (`app/vector_db/chroma_store.py`): Persistent vector database for document embeddings
- **Test Scripts**:
  - `tests/test_basic_rag.py`: Validates basic RAG chain functionality
  - `scripts/test_ingestion.py`: Tests document ingestion pipeline
  - `scripts/test_chromadb.py`: Tests ChromaDB operations
  - `scripts/test_embeddings.py`: Tests embedding generation and storage
  - `scripts/test_rag_query.py`: Tests complete RAG query system (7 test cases)
  - `scripts/test_citation_tracking.py`: Tests citation tracking system (5 test cases)
  - `scripts/test_system_integration.py`: Comprehensive system integration tests (11 test cases)
  - `scripts/test_streamlit_integration.py`: Streamlit UI integration tests (4 test cases)
  - `scripts/example_chromadb_usage.py`: ChromaDB usage examples
- **Data Collection Scripts**:
  - `scripts/fetch_edgar_data.py`: Automated SEC EDGAR data fetching and ingestion
- **Deployment Scripts**:
  - `scripts/deploy_local.sh`: Local deployment automation
  - `scripts/deploy_with_ngrok.sh`: ngrok tunneling deployment
- **Deployment Configuration**:
  - `.streamlit/config.toml`: Streamlit production configuration
- **Documentation**:
  - `docs/deployment.md`: Comprehensive deployment guide
  - `docs/edgar_integration.md`: SEC EDGAR integration documentation
  - `docs/prd.md`: Product requirements document

### Notes

- PDF support is optional and deferred to Phase 2 if not needed
- OpenAI embeddings are recommended for MVP (simpler than Ollama embeddings)
  - Default model: text-embedding-3-small (1536 dimensions)
  - Configure via `EMBEDDING_PROVIDER` in `.env` (openai or ollama)
- ChromaDB will persist data in `data/chroma_db/` directory
- All source documents should be placed in `data/documents/`
- EDGAR filings are saved to `data/documents/edgar_filings/` (optional)
- Complete ingestion pipeline: document → chunks → embeddings → ChromaDB
- EDGAR data can be fetched automatically using `scripts/fetch_edgar_data.py`
- `.env` file is gitignored - use `.env.example` as template

## Deployment

The system supports multiple deployment options:

1. **Local Deployment**: For development and testing
   - Script: `scripts/deploy_local.sh`
   - Access: `http://localhost:8501`

2. **ngrok Deployment**: For external demos and testing
   - Script: `scripts/deploy_with_ngrok.sh`
   - Access: Public ngrok URL

3. **VPS Deployment**: For production use
   - Guide: `docs/deployment.md`
   - Includes: Systemd, Nginx, SSL configuration

For detailed deployment instructions, see [`docs/deployment.md`](docs/deployment.md).

## Troubleshooting

- **Import errors**: Ensure virtual environment is activated
- **Ollama connection**: Verify Ollama is running on `localhost:11434`
- **ChromaDB issues**: Check `data/chroma_db/` directory permissions
- **Deployment issues**: See `docs/deployment.md` troubleshooting section
- **Streamlit not accessible**: Check firewall settings and `.streamlit/config.toml` configuration

