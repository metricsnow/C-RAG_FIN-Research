# Contextual RAG-Powered Financial Research Assistant

A production-ready RAG (Retrieval-Augmented Generation) system for semantic search across financial documents, featuring local LLM deployment with Ollama and comprehensive citation tracking.

## Table of Contents

- [Features](#features)
- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Project Structure](#project-structure)

## Features

### Core Capabilities

- **Semantic Document Search**: Natural language queries across financial documents with intelligent retrieval
- **Local LLM Deployment**: Privacy-first approach using Ollama for local inference (no data leaves your machine)
- **Citation Tracking**: Automatic source attribution with document references for every answer
- **SEC EDGAR Integration**: Automated fetching and indexing of SEC filings (10-K, 10-Q, 8-K forms)
- **Financial Domain Specialization**: Optimized for financial terminology and research queries
- **Vector Database**: Persistent ChromaDB storage for efficient similarity search
- **Streamlit UI**: Modern, interactive chat interface for querying documents

### Technical Features

- **Dual Embedding Support**: OpenAI (text-embedding-3-small) or Ollama embeddings
- **LangChain Integration**: Built on LangChain 1.0+ with Expression Language (LCEL)
- **Batch Processing**: Efficient batch embedding generation for large document collections
- **Metadata Management**: Rich document metadata (source, filename, type, date, chunk index)
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Performance Optimized**: Average query response time <5 seconds
- **Production Ready**: Multiple deployment options (local, ngrok, VPS)

### Data Collection

- **Automated EDGAR Fetching**: Fetch SEC filings from 10+ major companies automatically
- **Manual Document Ingestion**: Support for text and Markdown files
- **Chunking Strategy**: Intelligent text splitting with configurable chunk size and overlap
- **Indexing Verification**: Tools to verify document indexing and searchability

## Project Overview

The Contextual RAG-Powered Financial Research Assistant is an enterprise-grade RAG platform that enables semantic search across financial documents including market reports, research papers, SEC filings, and news articles. The system combines:

- **Retrieval-Augmented Generation (RAG)**: Enhances LLM responses with relevant document context
- **Vector Similarity Search**: Finds semantically similar content using embeddings
- **Local LLM Deployment**: Privacy-first approach with Ollama for sensitive financial data
- **Citation Tracking**: Ensures transparency and verifiability of answers

### Use Cases

- **Quantitative Research**: Search across financial research papers and reports
- **SEC Filing Analysis**: Query specific information from company filings
- **Market Research**: Find insights across multiple financial documents
- **Document Q&A**: Ask questions about indexed financial documents
- **Citation Verification**: Track sources for research and compliance

### Value Proposition

- **Privacy-First**: Local LLM deployment ensures sensitive financial data never leaves your machine
- **Production-Ready**: High-performance inference with validated architecture
- **Domain-Specialized**: Financial terminology understanding and citation tracking
- **Easy Deployment**: Multiple deployment options from local development to production VPS

## Prerequisites

Before installing, ensure you have:

- **Python 3.11 or higher** (Python 3.12 recommended)
- **Ollama installed and running** locally
  - Download from [ollama.ai](https://ollama.ai)
  - At least one model downloaded (Llama 3.2 or Mistral recommended)
- **(Optional) OpenAI API key** for embeddings (recommended for best performance)
  - Sign up at [platform.openai.com](https://platform.openai.com)
  - Get API key from API keys section

### System Requirements

- **RAM**: Minimum 8GB (16GB recommended for Ollama)
- **Storage**: ~5GB for dependencies and models
- **Network**: Internet connection for initial setup and OpenAI embeddings (if used)

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd project
```

### Step 2: Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root (optional but recommended):

```bash
# Create .env file
touch .env
# Edit .env and add your configuration
```

Edit `.env` file with your settings (all variables are optional with defaults):

```bash
# OpenAI API Key (optional, recommended for embeddings)
# Required if using OpenAI embeddings
OPENAI_API_KEY=your-api-key-here

# Embedding Provider: 'openai' or 'ollama' (default: 'openai')
EMBEDDING_PROVIDER=openai

# Ollama Configuration (defaults shown)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2

# ChromaDB Configuration (default: ./data/chroma_db)
CHROMA_DB_PATH=./data/chroma_db

# Application Configuration (optional)
LOG_LEVEL=INFO
MAX_DOCUMENT_SIZE_MB=10
DEFAULT_TOP_K=5
```

**Note**: The system will work with default values if `.env` is not created, but OpenAI embeddings require an API key.

### Step 5: Verify Ollama Installation

Ensure Ollama is running and a model is downloaded:

```bash
# Start Ollama server (if not running)
ollama serve

# Download a model (in another terminal)
ollama pull llama3.2  # Or: ollama pull mistral

# Test the installation
python scripts/test_ollama.py
```

### Step 6: Validate Setup

Run the validation script to verify all dependencies:

```bash
python scripts/validate_setup.py
```

This will check:
- Python version
- Virtual environment activation
- Required packages installation
- Ollama connectivity
- Environment variables configuration

## Configuration

### Environment Variables

The system uses environment variables loaded from `.env` file. Key configuration options:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | None | Optional (required for OpenAI embeddings) |
| `EMBEDDING_PROVIDER` | Embedding provider: 'openai' or 'ollama' | 'openai' | No |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | No |
| `LLM_MODEL` | Ollama model name | `llama3.2` | No |
| `CHROMA_DB_PATH` | ChromaDB storage path | `./data/chroma_db` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `MAX_DOCUMENT_SIZE_MB` | Maximum document size | `10` | No |
| `DEFAULT_TOP_K` | Default number of chunks to retrieve | `5` | No |

### Embedding Provider Selection

**OpenAI Embeddings (Recommended)**:
- Higher quality embeddings (1536 dimensions)
- Faster processing
- Requires API key
- Set `EMBEDDING_PROVIDER=openai` in `.env`

**Ollama Embeddings**:
- Fully local, no API key needed
- Slower processing
- Lower dimensional embeddings
- Set `EMBEDDING_PROVIDER=ollama` in `.env`

### Streamlit Configuration

Streamlit configuration is in `.streamlit/config.toml`:

```toml
[server]
address = "0.0.0.0"  # Allow external access
port = 8501
headless = true

[browser]
gatherUsageStats = false
```

## Usage Guide

### Quick Start

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Ingest documents** (if not already done):
   ```bash
   # Option 1: Fetch SEC EDGAR filings automatically
   python -u scripts/fetch_edgar_data.py
   
   # Option 2: Place documents in data/documents/ and process manually
   ```

3. **Start the application**:
   ```bash
   # Using deployment script
   bash scripts/deploy_local.sh
   
   # Or directly
   streamlit run app/ui/app.py
   ```

4. **Open browser**: Navigate to `http://localhost:8501`

### Using the Chat Interface

1. **Enter your query** in the chat input at the bottom
2. **Wait for response** (typically 3-5 seconds)
3. **Review answer and citations** displayed below the response
4. **Ask follow-up questions** as needed

### Example Queries

**Financial Terminology**:
```
What is the difference between EBITDA and operating income?
```

**Company-Specific Queries**:
```
What were Apple's revenue trends in the last fiscal year?
```

**Research Questions**:
```
What are the latest findings on algorithmic trading strategies?
```

**Document-Specific Queries**:
```
Summarize the risk factors mentioned in Microsoft's 10-K filing.
```

### Data Collection

#### Automated SEC EDGAR Fetching

Fetch and index SEC filings automatically:

```bash
python -u scripts/fetch_edgar_data.py
```

This script:
- Fetches filings from 10 major companies (AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, V, JNJ)
- Downloads 10-K, 10-Q, and 8-K forms
- Converts to text and ingests into ChromaDB
- Provides progress tracking and verification

**Verify indexing**:
```bash
python -u scripts/verify_document_indexing.py
```

#### Manual Document Ingestion

1. **Place documents** in `data/documents/`:
   - Text files (`.txt`)
   - Markdown files (`.md`)

2. **Process documents** using the ingestion pipeline:
   ```python
   from app.ingestion import create_pipeline
   from app.ingestion.document_loader import load_documents
   
   # Load documents
   documents = load_documents("data/documents/")
   
   # Process through pipeline
   pipeline = create_pipeline()
   chunk_ids = pipeline.process_document_objects(documents)
   ```

### Running Tests

The project includes comprehensive test suites:

```bash
# Basic RAG functionality
python tests/test_basic_rag.py

# Document ingestion
python scripts/test_ingestion.py

# ChromaDB operations
python scripts/test_chromadb.py

# Embedding generation
python scripts/test_embeddings.py

# RAG query system
python scripts/test_rag_query.py

# Citation tracking
python scripts/test_citation_tracking.py

# System integration (comprehensive)
python scripts/test_system_integration.py

# Streamlit UI integration
python scripts/test_streamlit_integration.py
```

### Development Workflow

1. **Always activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Follow task structure** in `dev/tasks/` directory

3. **Reference PRD** in `docs/prd-phase1.md` for requirements

4. **Run tests** before committing changes

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│                  (app/ui/app.py)                             │
│              Chat Interface + Session State                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   RAG Query System                            │
│                  (app/rag/chain.py)                          │
│    Query → Embedding → Vector Search → Context → LLM        │
└──────┬───────────────────────────────┬──────────────────────┘
       │                               │
       ▼                               ▼
┌──────────────────┐        ┌──────────────────┐
│  ChromaDB         │        │  Ollama LLM       │
│  Vector Store     │        │  (Local)          │
│  (app/vector_db/) │        │  (localhost:11434)│
└──────────────────┘        └──────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Document Ingestion Pipeline                     │
│         (app/ingestion/pipeline.py)                         │
│    Document → Chunking → Embeddings → ChromaDB Storage     │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

#### 1. Document Ingestion Layer

- **Document Loader** (`app/ingestion/document_loader.py`):
  - Supports text and Markdown files
  - RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
  - Metadata extraction (source, filename, type, date, chunk_index)
  - File size validation (max 10MB)

- **EDGAR Fetcher** (`app/ingestion/edgar_fetcher.py`):
  - SEC EDGAR API integration
  - Automated filing fetching
  - Rate limiting (10 requests/second)
  - Rich metadata extraction

- **Ingestion Pipeline** (`app/ingestion/pipeline.py`):
  - End-to-end processing: document → chunks → embeddings → storage
  - Batch processing support
  - Error handling and recovery

#### 2. Vector Database Layer

- **ChromaDB Store** (`app/vector_db/chroma_store.py`):
  - Persistent storage in `data/chroma_db/`
  - Automatic collection management
  - Similarity search by embedding or text
  - Document retrieval with metadata filtering

#### 3. RAG Query Layer

- **RAG Query System** (`app/rag/chain.py`):
  - LangChain Expression Language (LCEL) chain
  - Query embedding generation
  - Vector similarity search (top-k retrieval)
  - Context formatting for LLM prompts
  - Financial domain-optimized prompts
  - Error handling and validation

- **LLM Factory** (`app/rag/llm_factory.py`):
  - Ollama LLM instance creation
  - Model configuration
  - Connection management

- **Embedding Factory** (`app/rag/embedding_factory.py`):
  - OpenAI embeddings (text-embedding-3-small)
  - Ollama embeddings (fallback)
  - Batch embedding generation

#### 4. Frontend Layer

- **Streamlit App** (`app/ui/app.py`):
  - Chat interface using Streamlit components
  - Direct RAG system integration
  - Session state management
  - Citation display
  - Error handling with user-friendly messages

#### 5. Configuration Layer

- **Config Module** (`app/utils/config.py`):
  - Environment variable loading
  - Configuration validation
  - Default value management

### Data Flow

1. **Document Ingestion Flow**:
   ```
   Document File → Document Loader → Text Chunks → Embeddings → ChromaDB
   ```

2. **Query Processing Flow**:
   ```
   User Query → Query Embedding → Vector Search → Context Retrieval → 
   Prompt Construction → LLM Generation → Answer + Citations
   ```

### Technology Stack

- **Python 3.11+**: Core language
- **LangChain**: RAG framework and chain orchestration
- **Ollama**: Local LLM deployment
- **ChromaDB**: Vector database for embeddings
- **Streamlit**: Web frontend
- **OpenAI API**: Embedding generation (optional)
- **SEC EDGAR API**: Financial document fetching

## Deployment

The system supports multiple deployment options to suit different use cases:

### Option 1: Local Deployment (Development/Demo)

**Use Case**: Local development, testing, demos

```bash
# Activate virtual environment
source venv/bin/activate

# Run local deployment script
bash scripts/deploy_local.sh
```

**Access**: `http://localhost:8501`

**Features**:
- Automatic environment validation
- Ollama service check
- Streamlit startup with proper configuration

### Option 2: External Access with ngrok

**Use Case**: Demos, external testing, sharing with team

```bash
# Install ngrok (if not installed)
# macOS: brew install ngrok/ngrok/ngrok

# Run deployment with ngrok
bash scripts/deploy_with_ngrok.sh
```

**Features**:
- Public URL for external access
- Automatic tunnel management
- Local and public URL display

### Option 3: Production VPS Deployment

**Use Case**: Production deployment, public access

See comprehensive guide: [`docs/deployment.md`](docs/deployment.md)

**Includes**:
- VPS setup instructions
- Systemd service configuration
- Nginx reverse proxy setup
- SSL certificate configuration (Let's Encrypt)
- Service management and monitoring
- Security best practices

**Key Requirements**:
- VPS with Ubuntu 20.04+ (or similar Linux distribution)
- Minimum 8GB RAM (16GB recommended)
- Root or sudo access
- Domain name (for SSL)

## Troubleshooting

### Common Issues and Solutions

#### Import Errors

**Problem**: `ModuleNotFoundError` or import failures

**Solutions**:
1. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Verify all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. Check Python path:
   ```bash
   which python  # Should point to venv/bin/python
   ```

#### Ollama Connection Issues

**Problem**: Cannot connect to Ollama or model not found

**Solutions**:
1. Verify Ollama is running:
   ```bash
   ollama serve
   # Check in another terminal:
   curl http://localhost:11434/api/tags
   ```

2. Verify model is downloaded:
   ```bash
   ollama list
   # If empty, download a model:
   ollama pull llama3.2
   ```

3. Check OLLAMA_BASE_URL in `.env`:
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. Test Ollama connection:
   ```bash
   python scripts/test_ollama.py
   ```

#### ChromaDB Issues

**Problem**: ChromaDB errors or permission issues

**Solutions**:
1. Check directory permissions:
   ```bash
   ls -la data/chroma_db/
   # Ensure write permissions:
   chmod -R 755 data/chroma_db/
   ```

2. Verify ChromaDB path in configuration:
   ```bash
   # Check .env file
   CHROMA_DB_PATH=./data/chroma_db
   ```

3. Clear and rebuild database (if corrupted):
   ```bash
   rm -rf data/chroma_db/
   # Re-ingest documents
   ```

#### Streamlit Not Accessible

**Problem**: Cannot access Streamlit app in browser

**Solutions**:
1. Check Streamlit is running:
   ```bash
   ps aux | grep streamlit
   ```

2. Verify port 8501 is not in use:
   ```bash
   lsof -i :8501
   ```

3. Check firewall settings:
   ```bash
   # macOS: System Preferences → Security & Privacy → Firewall
   # Linux: sudo ufw allow 8501
   ```

4. Verify `.streamlit/config.toml` configuration:
   ```toml
   [server]
   address = "0.0.0.0"  # Allow external access
   port = 8501
   ```

#### OpenAI API Errors

**Problem**: Embedding generation fails with API errors

**Solutions**:
1. Verify API key is set:
   ```bash
   # Check .env file
   OPENAI_API_KEY=sk-...
   ```

2. Test API key:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. Check API quota and billing:
   - Visit [platform.openai.com/usage](https://platform.openai.com/usage)

4. Fallback to Ollama embeddings:
   ```bash
   # In .env file
   EMBEDDING_PROVIDER=ollama
   ```

#### Empty Query Results

**Problem**: Queries return no results or empty answers

**Solutions**:
1. Verify documents are indexed:
   ```bash
   python -u scripts/verify_document_indexing.py
   ```

2. Check ChromaDB collection:
   ```python
   from app.vector_db.chroma_store import ChromaStore
   store = ChromaStore()
   count = store.count()
   print(f"Documents in database: {count}")
   ```

3. Re-ingest documents if needed:
   ```bash
   python -u scripts/fetch_edgar_data.py
   ```

#### Performance Issues

**Problem**: Slow query response times

**Solutions**:
1. Use OpenAI embeddings (faster than Ollama):
   ```bash
   EMBEDDING_PROVIDER=openai
   ```

2. Reduce top-k retrieval (in `app/rag/chain.py`):
   ```python
   rag_system = RAGQuerySystem(top_k=3)  # Default is 5
   ```

3. Check system resources:
   ```bash
   # Monitor CPU and memory
   top
   # or
   htop
   ```

4. Verify Ollama model size (smaller models are faster)

### Getting Help

- **Check logs**: Streamlit shows errors in terminal
- **Run validation**: `python scripts/validate_setup.py`
- **Review documentation**: See `docs/` directory
- **Test components**: Run individual test scripts

## Contributing

We welcome contributions! Here's how you can help:

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Follow development standards**:
   - Use Python 3.11+
   - Follow PEP 8 style guide
   - Add type hints
   - Write docstrings (Google style)
   - Include tests for new features

4. **Run tests** before submitting:
   ```bash
   python scripts/test_system_integration.py
   ```

5. **Submit a pull request** with clear description

### Code Style

- **Formatting**: Use `black` for code formatting
- **Linting**: Follow PEP 8 guidelines
- **Type Hints**: Add type hints to all functions
- **Docstrings**: Use Google-style docstrings
- **Comments**: Add comments for complex logic

### Testing

- Write tests for new features
- Ensure all existing tests pass
- Add integration tests for new components

### Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features

### Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Error messages and stack traces
- Steps to reproduce
- Expected vs. actual behavior

## Project Structure

```
project/
├── app/                    # Application source code
│   ├── ingestion/          # Document ingestion pipeline
│   │   ├── document_loader.py    # Document loading and chunking
│   │   ├── edgar_fetcher.py      # SEC EDGAR API integration
│   │   └── pipeline.py           # End-to-end ingestion pipeline
│   ├── rag/                # RAG chain implementation
│   │   ├── chain.py              # RAG query system
│   │   ├── embedding_factory.py  # Embedding generation
│   │   └── llm_factory.py        # LLM instance creation
│   ├── ui/                 # Streamlit frontend
│   │   └── app.py                # Main Streamlit application
│   ├── utils/              # Utility functions
│   │   └── config.py            # Configuration management
│   └── vector_db/          # ChromaDB integration
│       └── chroma_store.py       # Vector database operations
├── data/                   # Data storage
│   ├── documents/          # Source documents (text, markdown)
│   └── chroma_db/          # ChromaDB persistence directory
├── tests/                  # Test files
│   └── test_basic_rag.py   # Basic RAG functionality tests
├── docs/                   # Documentation
│   ├── deployment.md       # Deployment guide
│   ├── edgar_integration.md # SEC EDGAR integration docs
│   ├── prd-phase1.md      # Phase 1 Product Requirements Document
│   └── prd-phase2.md       # Phase 2 Product Requirements Document
├── dev/                    # Development tasks and bugs
│   ├── tasks/              # Task definitions
│   └── bugs/               # Bug reports
├── scripts/                # Utility scripts
│   ├── deploy_local.sh     # Local deployment script
│   ├── deploy_with_ngrok.sh # ngrok deployment script
│   ├── fetch_edgar_data.py # EDGAR data fetching
│   ├── run_streamlit.py    # Streamlit runner
│   ├── test_*.py           # Various test scripts
│   └── validate_setup.py  # Setup validation
├── .streamlit/             # Streamlit configuration
│   └── config.toml         # Production configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## License

[Add your license information here]

## Acknowledgments

- **LangChain**: RAG framework and chain orchestration
- **Ollama**: Local LLM deployment
- **ChromaDB**: Vector database
- **Streamlit**: Web frontend framework
- **SEC EDGAR**: Financial document data source

---

**Last Updated**: 2025-01-27  
**Version**: 1.0.0  
**Status**: Production Ready
