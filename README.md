# Contextual RAG-Powered Financial Research Assistant

A production-ready RAG (Retrieval-Augmented Generation) system for semantic search across financial documents, featuring flexible LLM deployment (Ollama or OpenAI) and comprehensive citation tracking.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-green.svg)](https://python.langchain.com/)
[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success.svg)](https://github.com/metricsnow/C-RAG_FIN-Research)

**Full documentation**: See [`project/README.md`](project/README.md) for comprehensive setup and usage instructions.

## Project Overview

This project demonstrates a production-ready RAG (Retrieval-Augmented Generation) system for financial research, implementing state-of-the-art techniques for semantic search across financial documents including SEC filings, research papers, market reports, and news articles.

The system serves as a hands-on demonstration of modern RAG architecture, exploring practical implementations of advanced techniques including hybrid search, query refinement, and multi-provider LLM integration. It provides a working example of how these components integrate in a production environment.

### System Components

The project is organized into several key modules, each implementing specific state-of-the-art techniques:

- **Document Ingestion Pipeline**: Implements intelligent chunking strategies, batch embedding generation, and metadata extraction for financial documents
- **RAG Chain**: Advanced retrieval with hybrid search (semantic + BM25), query expansion, reranking capabilities, and citation tracking
- **Vector Database Integration**: ChromaDB implementation with persistent storage, similarity search optimization, and metadata filtering (including sentiment-based filtering)
- **LLM Factory Pattern**: Dual-provider support (Ollama/OpenAI) with seamless switching, demonstrating provider abstraction patterns
- **Query Processing**: Query refinement, prompt engineering for financial domain, context-aware retrieval optimization, and sentiment-aware query filtering
- **Monitoring & Observability**: Prometheus metrics integration, health check endpoints, and comprehensive logging infrastructure

### State-of-the-Art Techniques Implemented

- **Hybrid Search**: Combines semantic similarity search with BM25 keyword matching for improved retrieval accuracy
- **Query Expansion**: Automatic query refinement and expansion to improve retrieval relevance
- **Reranking**: Cross-encoder reranking for optimal document ordering
- **Sentiment-Aware Filtering**: Filter query results by sentiment (positive/negative/neutral) for targeted document retrieval
- **Dual-Provider Architecture**: Flexible LLM and embedding provider switching without code changes
- **Financial Domain Optimization**: Custom prompt engineering and domain-specific embeddings for financial terminology
- **Production-Grade Architecture**: Type-safe configuration (Pydantic), comprehensive testing (82.75% coverage), and monitoring integration

## Technology Stack

### Core Technologies
- **Python 3.11+**: Modern Python with type hints, pattern matching, and performance optimizations
- **LangChain 1.0+**: RAG framework using Expression Language (LCEL) for declarative chain composition and streaming support
- **ChromaDB**: Vector database with persistent storage, metadata filtering (including sentiment-based filtering), and optimized similarity search
- **Streamlit**: Interactive web frontend with real-time streaming and state management

### LLM & Embeddings Architecture
- **Ollama**: Local LLM deployment (Llama 3.2) enabling privacy-preserving inference
- **OpenAI API**: Cloud-based embeddings (text-embedding-3-small) and LLM (gpt-4o-mini) support
- **Factory Pattern**: Provider abstraction layer enabling seamless switching between LLM and embedding providers
- **Multi-Provider Support**: Unified interface supporting multiple providers with runtime switching

### Advanced RAG Components
- **Hybrid Search**: Semantic vector search combined with BM25 keyword matching
- **Query Refinement**: Automatic query expansion and refinement techniques
- **Reranking**: Cross-encoder reranking for optimal document ordering
- **Sentiment-Aware Filtering**: Filter query results by document sentiment for targeted retrieval
- **Intelligent Chunking**: Recursive character text splitting with overlap strategies and metadata preservation

### Data Sources & Integration
- **SEC EDGAR API**: Automated document fetching pipeline for SEC filings (10-K, 10-Q, 8-K)
- **Stock Data Integration**: Comprehensive stock market data via yfinance (company info, financial metrics, historical prices, dividends, earnings, analyst recommendations)
- **Earnings Call Transcripts**: Fetch and index earnings call transcripts with speaker annotation, Q&A sections, and forward guidance extraction
- **Financial News Aggregation**: RSS feeds and web scraping for financial news from Reuters, CNBC, Bloomberg with ticker detection and categorization
- **Economic Calendar Integration**: Macroeconomic indicators and events via Trading Economics API
- **FRED API Integration**: 840,000+ economic time series including interest rates, exchange rates, inflation, employment, GDP
- **IMF and World Bank Data Integration**: Global economic data from IMF Data Portal and World Bank Open Data APIs for 188+ countries
- **Central Bank Data Integration**: FOMC statements, meeting minutes, press conference transcripts, and forward guidance extraction
- **Financial Sentiment Analysis**: Comprehensive sentiment analysis using FinBERT, TextBlob, and VADER with forward guidance and risk factor extraction, plus sentiment-aware query filtering
- **Document Processing**: Multi-format support (text, Markdown) with intelligent chunking and metadata extraction
- **Batch Processing**: Optimized batch embedding generation for efficient document indexing

### Development & Quality Infrastructure
- **Pydantic**: Type-safe configuration management with runtime validation
- **pytest**: Comprehensive test suite with 174 tests achieving 82.75% coverage
- **mypy**: Static type checking for enhanced code quality and maintainability
- **Pre-commit Hooks**: Automated code formatting (black, isort) and linting (flake8)
- **Prometheus**: Metrics collection and monitoring for observability
- **Sphinx**: API documentation generation with automated docstring processing

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
    │                  │  Optional: Sentiment filtering (positive/negative/neutral)
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
- **Semantic Document Search**: Natural language queries across financial documents using vector similarity search
- **Multi-Provider LLM Architecture**: Factory pattern implementation supporting Ollama (local) and OpenAI (cloud) providers
- **Citation Tracking**: Automatic source attribution with document references and metadata for traceability
- **SEC EDGAR Integration**: Automated document fetching and indexing pipeline for SEC filings (10-K, 10-Q, 8-K forms)
- **Financial Domain Optimization**: Domain-specific prompt engineering and embedding strategies for financial terminology
- **FastAPI Backend**: Production-ready RESTful API with OpenAPI documentation, authentication, and rate limiting
- **Document Management**: Comprehensive UI for managing indexed documents with search, filtering, and deletion
- **Conversation Memory**: Multi-turn conversations with context preservation and LangChain memory integration
- **Financial Sentiment Analysis**: Automatic sentiment analysis for all documents using FinBERT, TextBlob, and VADER with sentiment-aware query filtering

### Advanced RAG Techniques
- **Hybrid Search**: Combines semantic vector search with BM25 keyword matching for improved retrieval precision
- **Query Refinement**: Automatic query expansion and refinement to enhance retrieval relevance
- **Reranking**: Cross-encoder reranking implementation for optimal document ordering
- **Sentiment-Aware Filtering**: Filter query results by document sentiment (positive/negative/neutral) for targeted retrieval
- **Dual Embedding Support**: OpenAI (text-embedding-3-small) or Ollama embeddings with provider abstraction
- **Intelligent Chunking**: Recursive character text splitting with overlap strategies for optimal context preservation

### Infrastructure & Architecture
- **Vector Database**: ChromaDB with persistent storage, metadata filtering (including sentiment-based filtering), and similarity search optimization
- **Streamlit UI**: Interactive chat interface with real-time model switching and query processing
- **FastAPI Backend**: RESTful API with OpenAPI/Swagger documentation, authentication, and rate limiting
- **Performance Metrics**: Average query response time 3.46s with comprehensive performance monitoring
- **Observability**: Prometheus metrics integration, health check endpoints, and structured logging
- **Code Quality**: Pre-commit hooks (black, isort, flake8), static type checking (mypy), and comprehensive test coverage

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
│   │   ├── api/                # FastAPI backend
│   │   │   ├── auth.py              # Authentication middleware
│   │   │   ├── main.py              # FastAPI application entry point
│   │   │   ├── middleware.py        # Request middleware
│   │   │   ├── models/              # API data models
│   │   │   │   ├── documents.py     # Document models
│   │   │   │   ├── ingestion.py     # Ingestion models
│   │   │   │   └── query.py         # Query models
│   │   │   └── routes/              # API route handlers
│   │   │       ├── documents.py     # Document endpoints
│   │   │       ├── health.py        # Health check endpoints
│   │   │       ├── ingestion.py     # Ingestion endpoints
│   │   │       └── query.py         # Query endpoints
│   │   ├── ingestion/          # Document ingestion pipeline
│   │   │   ├── document_loader.py    # Multi-format document loading
│   │   │   ├── edgar_fetcher.py      # SEC EDGAR API integration
│   │   │   ├── yfinance_fetcher.py   # Stock data integration
│   │   │   ├── transcript_fetcher.py  # Earnings call transcripts
│   │   │   ├── news_fetcher.py        # Financial news aggregation
│   │   │   ├── economic_calendar_fetcher.py # Economic calendar
│   │   │   ├── fred_fetcher.py       # FRED API integration
│   │   │   ├── imf_fetcher.py        # IMF Data Portal integration
│   │   │   ├── world_bank_fetcher.py  # World Bank API integration
│   │   │   ├── central_bank_fetcher.py # Central bank data
│   │   │   ├── sentiment_analyzer.py # Financial sentiment analysis
│   │   │   └── pipeline.py           # End-to-end ingestion orchestration
│   │   ├── rag/                # RAG chain implementation
│   │   │   ├── chain.py              # LCEL-based RAG chain with streaming
│   │   │   ├── llm_factory.py        # Multi-provider LLM abstraction
│   │   │   ├── embedding_factory.py  # Multi-provider embedding abstraction
│   │   │   ├── prompt_engineering.py # Financial domain prompts
│   │   │   ├── query_refinement.py   # Query expansion and refinement
│   │   │   └── retrieval_optimizer.py # Hybrid search and reranking
│   │   ├── ui/                 # Streamlit frontend
│   │   │   ├── app.py                # Interactive chat interface
│   │   │   └── document_management.py # Document management UI
│   │   ├── utils/              # Configuration and utilities
│   │   │   ├── config.py            # Pydantic-based configuration
│   │   │   ├── conversation_export.py # Conversation export utilities
│   │   │   ├── conversation_memory.py # Conversation state management
│   │   │   ├── document_manager.py   # Document management utilities
│   │   │   ├── health.py            # Health check utilities
│   │   │   ├── logger.py            # Structured logging
│   │   │   └── metrics.py           # Prometheus metrics
│   │   └── vector_db/          # ChromaDB integration
│   │       └── chroma_store.py      # Vector store operations
│   ├── docs/                   # Documentation
│   │   ├── api.md              # API documentation
│   │   ├── configuration.md   # Configuration guide
│   │   ├── deployment.md       # Deployment guide
│   │   ├── edgar_integration.md # SEC EDGAR integration docs
│   │   ├── prd-phase1.md       # Phase 1 Product Requirements
│   │   ├── prd-phase2.md       # Phase 2 Planning Document
│   │   ├── testing.md          # Testing documentation
│   │   └── sphinx/             # Sphinx documentation build
│   ├── dev/                    # Development tasks and bugs
│   │   ├── archive/            # Completed tasks and bugs
│   │   │   ├── bugs_done/      # Completed bug reports
│   │   │   └── tasks_done/     # Completed tasks
│   │   ├── bugs/               # Active bug reports
│   │   └── tasks/              # Active tasks
│   ├── scripts/                # Utility scripts
│   │   ├── deploy_local.sh          # Local deployment script
│   │   ├── deploy_with_ngrok.sh     # ngrok deployment script
│   │   ├── example_chromadb_usage.py # ChromaDB usage examples
│   │   ├── fetch_edgar_data.py       # SEC data fetching utilities
│   │   ├── fetch_stock_data.py       # Stock data fetching
│   │   ├── fetch_transcripts.py     # Earnings call transcripts
│   │   ├── fetch_news.py             # News aggregation
│   │   ├── fetch_economic_calendar.py # Economic calendar
│   │   ├── fetch_fred_data.py        # FRED API data
│   │   ├── fetch_imf_data.py         # IMF data
│   │   ├── fetch_world_bank_data.py  # World Bank data
│   │   ├── fetch_central_bank_data.py # Central bank data
│   │   ├── run_streamlit.py         # Streamlit application launcher
│   │   ├── start_api.py              # API server launcher
│   │   ├── start_streamlit.sh       # Streamlit startup script
│   │   ├── validate_chromadb_comprehensive.py # Comprehensive DB validation
│   │   ├── validate_chromadb_data.py # Database data validation
│   │   ├── validate_setup.py        # Setup validation
│   │   └── verify_document_indexing.py # Document indexing verification
│   ├── tests/                  # Comprehensive test suite
│   │   ├── test_rag_chain_comprehensive.py  # RAG chain tests
│   │   ├── test_chromadb_comprehensive.py   # Vector DB tests
│   │   ├── test_pipeline_comprehensive.py   # Ingestion tests
│   │   └── test_end_to_end.py               # Integration tests
│   ├── pyproject.toml          # Project configuration and dependencies
│   ├── pytest.ini              # pytest configuration
│   ├── requirements.txt        # Python dependencies
│   ├── streamlit_app.py        # Streamlit application entry point
│   ├── START_STREAMLIT.sh      # Streamlit startup script
│   └── README.md               # Detailed project README
```

## Documentation

- **[Project README](project/README.md)**: Comprehensive setup, usage, and architecture guide
- **[API Documentation](project/docs/api.md)**: FastAPI endpoints and usage
- **[Configuration Guide](project/docs/reference/configuration.md)**: Configuration options and environment variables
- **[Phase 1 PRD](project/docs/prd-phase1.md)**: Complete Phase 1 MVP requirements and specifications
- **[Phase 2 PRD](project/docs/prd-phase2.md)**: Phase 2 enhancement planning
- **[Deployment Guide](project/docs/reference/deployment.md)**: Deployment instructions for local, ngrok, and VPS
- **[Integration Guides](project/docs/integrations/)**: Comprehensive integration documentation
  - [Sentiment Analysis](project/docs/integrations/sentiment_analysis.md)
  - [News Aggregation](project/docs/integrations/news_aggregation.md)
  - [Stock Data](project/docs/integrations/yfinance_integration.md)
  - [FRED API](project/docs/integrations/fred_integration.md)
  - [IMF & World Bank](project/docs/integrations/imf_world_bank_integration.md)
  - [Central Bank Data](project/docs/integrations/central_bank_integration.md)
- **[Testing Documentation](project/docs/testing.md)**: Testing guidelines and test suite information

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
- ✅ Conversation memory context usage

### Completed (Phase 2)
- ✅ FastAPI backend with OpenAPI documentation, authentication, and rate limiting
- ✅ Enhanced data sources (yfinance, FRED, IMF, World Bank, Economic Calendar)
- ✅ Advanced analytics (sentiment analysis with FinBERT/TextBlob/VADER, forward guidance extraction, risk factor identification, sentiment-aware query filtering)
- ✅ Conversation history management UI (clear/export features)
- ✅ Earnings call transcripts integration
- ✅ Financial news aggregation with RSS feeds and web scraping
- ✅ Central bank data integration (FOMC statements, minutes, press conferences)
- ✅ Document management UI with search, filtering, and deletion
- ✅ RAG optimization (hybrid search, reranking, query refinement)

### Planned (Future Enhancements)
- ✅ News article summarization
- ✅ News trend analysis
- ✅ Automated news monitoring
- 📋 News alert system
- 📋 Additional performance optimizations

See [Phase 2 PRD](project/docs/prd-phase2.md) for detailed planning.

## Acknowledgments

- **LangChain**: RAG framework and chain orchestration
- **Ollama**: Local LLM deployment
- **ChromaDB**: Vector database
- **Streamlit**: Web frontend framework
- **SEC EDGAR**: Financial document data source

## Technical Development

This project utilizes a self-developed Cursor AI framework to optimize coding speed and maintainability. The framework provides specialized AI personas (Mission Analyst, Mission Planner, Mission Executor, Mission-QA, Mission Challenger, etc.) through slash commands, enabling sequential persona switching and orchestrated multi-agent workflows for complex technical tasks. The framework uses BPMN workflows, quality gates, and state persistence to ensure consistent code quality, comprehensive testing, and efficient project progress while maintaining complete autonomy from the project codebase.
