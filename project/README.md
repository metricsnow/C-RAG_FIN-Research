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
├── dev/                    # Development tasks and bugs
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

### Running the Streamlit App

After setup and document ingestion, run the Streamlit frontend:

```bash
# Option 1: Using the run script
python scripts/run_streamlit.py

# Option 2: Direct Streamlit command
streamlit run app/ui/app.py
```

The app will open in your browser at `http://localhost:8501`.

### Next Steps

After setup, proceed with:
- **TASK-009**: Citation Tracking Implementation (enhanced citation display)

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
- **Embedding Generation** (`app/rag/embedding_factory.py`): OpenAI and Ollama embedding generation with batch processing
- **ChromaDB Integration** (`app/vector_db/chroma_store.py`): Persistent vector database for document embeddings
- **Test Scripts**:
  - `tests/test_basic_rag.py`: Validates basic RAG chain functionality
  - `scripts/test_ingestion.py`: Tests document ingestion pipeline
  - `scripts/test_chromadb.py`: Tests ChromaDB operations
  - `scripts/test_embeddings.py`: Tests embedding generation and storage
  - `scripts/test_rag_query.py`: Tests complete RAG query system (7 test cases)
  - `scripts/example_chromadb_usage.py`: ChromaDB usage examples

### Notes

- PDF support is optional and deferred to Phase 2 if not needed
- OpenAI embeddings are recommended for MVP (simpler than Ollama embeddings)
  - Default model: text-embedding-3-small (1536 dimensions)
  - Configure via `EMBEDDING_PROVIDER` in `.env` (openai or ollama)
- ChromaDB will persist data in `data/chroma_db/` directory
- All source documents should be placed in `data/documents/`
- Complete ingestion pipeline: document → chunks → embeddings → ChromaDB
- `.env` file is gitignored - use `.env.example` as template

## Troubleshooting

- **Import errors**: Ensure virtual environment is activated
- **Ollama connection**: Verify Ollama is running on `localhost:11434`
- **ChromaDB issues**: Check `data/chroma_db/` directory permissions

