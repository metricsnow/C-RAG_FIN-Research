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

### Next Steps

After setup, proceed with:
- **TASK-004**: Document Ingestion Pipeline - Text and Markdown Support
- **TASK-005**: ChromaDB Integration and Vector Database Setup
- **TASK-006**: Embedding Generation and Storage Integration

## Architecture

### Implemented Components

- **Configuration Management** (`app/utils/config.py`): Loads environment variables from `.env`
- **LLM Factory** (`app/rag/llm_factory.py`): Creates and configures Ollama LLM instances
- **RAG Chain** (`app/rag/chain.py`): Basic RAG chain using LangChain Expression Language (LCEL)
- **Test Script** (`tests/test_basic_rag.py`): Validates RAG chain functionality

### Notes

- PDF support is optional and deferred to Phase 2 if not needed
- OpenAI embeddings are recommended for MVP (simpler than Ollama embeddings)
- ChromaDB will persist data in `data/chroma_db/` directory
- All source documents should be placed in `data/documents/`
- `.env` file is gitignored - use `.env.example` as template

## Troubleshooting

- **Import errors**: Ensure virtual environment is activated
- **Ollama connection**: Verify Ollama is running on `localhost:11434`
- **ChromaDB issues**: Check `data/chroma_db/` directory permissions

