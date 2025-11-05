# Contextual RAG-Powered Financial Research Assistant

A production-ready RAG (Retrieval-Augmented Generation) system for semantic search across financial documents, featuring flexible LLM deployment (Ollama or OpenAI) and comprehensive citation tracking.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-green.svg)](https://python.langchain.com/)
[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success.svg)](https://github.com/metricsnow/C-RAG_FIN-Research)

**Full documentation**: See [`project/README.md`](project/README.md) for comprehensive setup and usage instructions.

## Project Overview

This is a **public showcase project** demonstrating a production-ready RAG (Retrieval-Augmented Generation) system specifically designed for financial research. The system enables semantic search across financial documents including SEC filings, research papers, market reports, and news articles.

The project showcases modern AI integration patterns, production-grade architecture, and best practices for building RAG applications. It serves as a reference implementation for:

- **Quantitative Developers**: Seeking AI-enhanced research tools and semantic search capabilities
- **Data Engineers**: Requiring scalable document processing and vector database integration examples
- **LLM Integration Engineers**: Needing production-ready RAG implementation patterns
- **AI Strategy Consultants**: Demonstrating strategic AI implementation with measurable outcomes

**Key Value Propositions**:
- **Privacy-First Architecture**: Local LLM deployment (Ollama) ensures sensitive financial data never leaves your infrastructure
- **Production-Ready**: Comprehensive testing (82.75% coverage), monitoring (Prometheus metrics), and error handling
- **Financial Domain Specialization**: Optimized for financial terminology with custom embeddings and domain-specific prompts
- **Flexible Deployment**: Multiple deployment options from local development to production VPS
- **Modern Tech Stack**: Built with LangChain 1.0+, ChromaDB, and contemporary Python practices

## Technology Stack

### Core Technologies
- **Python 3.11+**: Core language with type hints and modern features
- **LangChain 1.0+**: RAG framework and chain orchestration using Expression Language (LCEL)
- **ChromaDB**: Vector database for persistent embedding storage
- **Streamlit**: Interactive web frontend for query interface

### LLM & Embeddings
- **Ollama**: Local LLM deployment (Llama 3.2) for privacy-first inference
- **OpenAI API**: Optional embeddings (text-embedding-3-small) and LLM (gpt-4o-mini) support
- **Dual Provider Support**: Switchable LLM providers via UI toggle

### Data Sources & Integration
- **SEC EDGAR API**: Automated fetching and indexing of SEC filings (10-K, 10-Q, 8-K)
- **Document Processing**: Support for text and Markdown files with intelligent chunking

### Development & Quality
- **Pydantic**: Type-safe configuration management with validation
- **pytest**: Comprehensive test suite with 174 tests (82.75% coverage)
- **mypy**: Static type checking for code quality
- **Pre-commit Hooks**: Automated code formatting (black, isort, flake8)
- **Prometheus**: Metrics collection and monitoring
- **Sphinx**: API documentation generation

## System Process Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT INGESTION FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  Documents   │
    │ (Text/MD/    │
    │  SEC EDGAR)  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │  Document Loader │  Extract text, validate size, extract metadata
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │   Text Chunking  │  RecursiveCharacterTextSplitter (800 chars, 150 overlap)
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Embedding Gen    │  OpenAI text-embedding-3-small or Ollama embeddings
    │ (Batch Process)  │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │   ChromaDB       │  Store chunks + embeddings + metadata
    │  Vector Store    │
    └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                           QUERY PROCESSING FLOW                         │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ User Query   │  Natural language question
    │ (Streamlit)  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │ Query Embedding │  Convert query to vector representation
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Vector Search    │  Similarity search in ChromaDB (top-k retrieval)
    │ (ChromaDB)       │  Optional: Hybrid search (semantic + BM25)
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Context Retrieval│  Retrieve top-k relevant document chunks
    │ (Top-K Chunks)   │  Optional: Reranking with cross-encoder
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Prompt Building  │  Format context + query with financial domain prompts
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ LLM Generation   │  Ollama (local) or OpenAI (cloud) inference
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Answer +         │  Generated answer with source citations
    │ Citations        │
    └──────────────────┘
```

## Key Features

### Core Capabilities
- **Semantic Document Search**: Natural language queries across financial documents with intelligent retrieval
- **Flexible LLM Deployment**: Choose between local Ollama (privacy-first) or OpenAI (cloud) for inference
- **Citation Tracking**: Automatic source attribution with document references for every answer
- **SEC EDGAR Integration**: Automated fetching and indexing of SEC filings (10-K, 10-Q, 8-K forms)
- **Financial Domain Specialization**: Optimized for financial terminology and research queries

### Technical Features
- **Dual LLM Support**: OpenAI (gpt-4o-mini) or Ollama (llama3.2) - switchable via UI toggle
- **Dual Embedding Support**: OpenAI (text-embedding-3-small) or Ollama embeddings
- **Advanced RAG Optimizations**: Hybrid search (semantic + BM25), reranking, query expansion
- **Vector Database**: Persistent ChromaDB storage for efficient similarity search
- **Streamlit UI**: Modern, interactive chat interface with model selection toggle
- **Performance Optimized**: Average query response time <5 seconds (achieved: 3.46s)
- **Monitoring & Observability**: Prometheus metrics and health check endpoints
- **Code Quality**: Pre-commit hooks, static type checking (mypy), comprehensive logging

## Project Status

### Phase 1 (MVP) - ✅ Complete

**All 13 MVP Tasks Completed**:
- ✅ **Foundation Setup**: Environment, Ollama, LangChain integration
- ✅ **Core Integration**: Document ingestion, ChromaDB, embeddings
- ✅ **Query Interface**: RAG system, Streamlit UI, citation tracking
- ✅ **Document Collection**: 50+ documents indexed, 511 chunks
- ✅ **System Testing**: Comprehensive test suite with 174 tests
- ✅ **Deployment**: Local, ngrok, and VPS deployment options
- ✅ **Documentation**: Comprehensive README and deployment guides

**Performance**: Average query response time **3.46 seconds** (target: <5s) ✅

### Post-MVP Enhancements - ✅ Complete

**All 10 Post-MVP Enhancement Tasks Completed**:
- ✅ **Code Quality**: Pre-commit hooks (black, flake8, isort), static type checking (mypy)
- ✅ **Test Coverage**: Enhanced to **82.75%** (exceeded 80% target) with 174 comprehensive tests
- ✅ **Monitoring**: Prometheus metrics and health check endpoints
- ✅ **Logging**: Comprehensive logging infrastructure across all modules
- ✅ **Configuration**: Pydantic-based type-safe configuration with validation
- ✅ **Dependencies**: Modern dependency management with `pyproject.toml` (PEP 621)
- ✅ **Documentation**: API documentation generation with Sphinx

**Test Coverage**: **82.75%** (174 tests) ✅ - All core modules above 80% coverage

### Phase 2 - 📋 Planning

See [`project/docs/prd-phase2.md`](project/docs/prd-phase2.md) for Phase 2 enhancements:
- FastAPI backend implementation
- Enhanced data integration (yfinance, FRED, IMF, World Bank)
- Advanced analytics (FinBERT sentiment analysis)
- Full conversation memory
- Additional performance optimizations

## Performance Metrics

- **Query Response Time**: 3.46s average (target: <5s) ✅
- **Documents Indexed**: 50 documents, 511 chunks
- **Test Coverage**: **82.75%** (174 tests) ✅ - Exceeded 80% target
- **Code Quality**: Pre-commit hooks, mypy type checking, comprehensive logging ✅
- **Monitoring**: Prometheus metrics and health check endpoints ✅
- **System Status**: Production-ready MVP + Post-MVP enhancements complete ✅

## Repository Structure

```
.
├── project/                    # Main application code
│   ├── app/                    # Application source code
│   │   ├── ingestion/          # Document ingestion pipeline
│   │   ├── rag/                # RAG chain implementation
│   │   ├── ui/                 # Streamlit frontend
│   │   ├── utils/              # Configuration management
│   │   └── vector_db/          # ChromaDB integration
│   ├── docs/                   # Documentation
│   │   ├── prd-phase1.md       # Phase 1 Product Requirements
│   │   ├── prd-phase2.md       # Phase 2 Planning Document
│   │   ├── deployment.md       # Deployment guide
│   │   └── edgar_integration.md # SEC EDGAR integration docs
│   ├── dev/                    # Development tasks and bugs
│   │   ├── tasks/              # Active tasks
│   │   └── archive/            # Completed tasks
│   ├── scripts/                # Utility scripts
│   ├── tests/                  # Test files
│   └── README.md               # Detailed project README
│
└── development_framework_v2/  # Development framework (internal)
    └── framework/              # Framework components
        ├── agents/             # AI agent definitions
        ├── commands/           # Command definitions
        ├── docs/               # Framework documentation
        └── workflows/          # Workflow definitions
```

## Documentation

- **[Project README](project/README.md)**: Comprehensive setup, usage, and architecture guide
- **[Phase 1 PRD](project/docs/prd-phase1.md)**: Complete Phase 1 MVP requirements and specifications
- **[Phase 2 PRD](project/docs/prd-phase2.md)**: Phase 2 enhancement planning
- **[Deployment Guide](project/docs/deployment.md)**: Deployment instructions for local, ngrok, and VPS
- **[SEC EDGAR Integration](project/docs/edgar_integration.md)**: SEC EDGAR data fetching documentation

## Deployment Options

1. **Local Deployment**: Development and testing
2. **ngrok Tunnel**: External access for demos
3. **VPS Deployment**: Production deployment (see [deployment guide](project/docs/deployment.md))

**Note**: Ollama requires self-hosting, so Streamlit Cloud is not an option.

## Development Roadmap

### Completed (Phase 1 - MVP)
- ✅ All 13 core tasks completed
- ✅ MVP fully functional
- ✅ Comprehensive documentation

### Completed (Post-MVP Enhancements)
- ✅ All 10 post-MVP enhancement tasks completed
- ✅ Code quality infrastructure (pre-commit, mypy, type checking)
- ✅ Test coverage enhanced to 82.75% (174 tests)
- ✅ Monitoring and observability (Prometheus metrics, health checks)
- ✅ Comprehensive logging infrastructure
- ✅ Pydantic-based configuration management
- ✅ Modern dependency management (pyproject.toml)
- ✅ API documentation generation (Sphinx)

### Planned (Phase 2)
- 📋 FastAPI backend
- 📋 Enhanced data sources (yfinance, FRED, IMF, World Bank)
- 📋 Advanced analytics (sentiment analysis, forward guidance extraction)
- 📋 Full conversation memory
- 📋 Additional performance optimizations

See [Phase 2 PRD](project/docs/prd-phase2.md) for detailed planning.

## Acknowledgments

- **LangChain**: RAG framework and chain orchestration
- **Ollama**: Local LLM deployment
- **ChromaDB**: Vector database
- **Streamlit**: Web frontend framework
- **SEC EDGAR**: Financial document data source

---

**Status**: 🟢 MVP + Post-MVP Enhancements Complete | **Version**: 1.0.0 | **Last Updated**: 2025-01-27

**Total Tasks Completed**: 23 (13 MVP + 10 Post-MVP Enhancements)
