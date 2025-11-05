# Contextual RAG-Powered Financial Research Assistant

A production-ready RAG (Retrieval-Augmented Generation) system for semantic search across financial documents, featuring local LLM deployment with Ollama and comprehensive citation tracking.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-green.svg)](https://python.langchain.com/)
[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success.svg)](https://github.com/metricsnow/C-RAG_FIN-Research)

**Full documentation**: See [`project/README.md`](project/README.md) for comprehensive setup and usage instructions.

## 📋 Project Status

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

## 🏗️ Repository Structure

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

## ✨ Key Features

### Core Capabilities
- **Semantic Document Search**: Natural language queries across financial documents
- **Local LLM Deployment**: Privacy-first approach using Ollama
- **Citation Tracking**: Automatic source attribution for every answer
- **SEC EDGAR Integration**: Automated fetching and indexing of SEC filings
- **Financial Domain Specialization**: Optimized for financial terminology

### Technical Features
- **Dual Embedding Support**: OpenAI or Ollama embeddings
- **LangChain Integration**: Built on LangChain 1.0+ with Expression Language (LCEL)
- **Vector Database**: Persistent ChromaDB storage
- **Streamlit UI**: Modern, interactive chat interface
- **Performance Optimized**: Average query response time <5 seconds
- **Monitoring & Observability**: Prometheus metrics and health check endpoints
- **Code Quality**: Pre-commit hooks, static type checking, comprehensive logging

## 📚 Documentation

- **[Project README](project/README.md)**: Comprehensive setup, usage, and architecture guide
- **[Phase 1 PRD](project/docs/prd-phase1.md)**: Complete Phase 1 MVP requirements and specifications
- **[Phase 2 PRD](project/docs/prd-phase2.md)**: Phase 2 enhancement planning
- **[Deployment Guide](project/docs/deployment.md)**: Deployment instructions for local, ngrok, and VPS
- **[SEC EDGAR Integration](project/docs/edgar_integration.md)**: SEC EDGAR data fetching documentation

## 🛠️ Technology Stack

- **Python 3.11+**: Core language
- **LangChain**: RAG framework and chain orchestration
- **Ollama**: Local LLM deployment
- **ChromaDB**: Vector database for embeddings
- **Streamlit**: Web frontend
- **OpenAI API**: Embedding generation (optional)
- **SEC EDGAR API**: Financial document fetching

## 📊 Performance Metrics

- **Query Response Time**: 3.46s average (target: <5s) ✅
- **Documents Indexed**: 50 documents, 511 chunks
- **Test Coverage**: **82.75%** (174 tests) ✅ - Exceeded 80% target
- **Code Quality**: Pre-commit hooks, mypy type checking, comprehensive logging ✅
- **Monitoring**: Prometheus metrics and health check endpoints ✅
- **System Status**: Production-ready MVP + Post-MVP enhancements complete ✅

## 🚢 Deployment Options

1. **Local Deployment**: Development and testing
2. **ngrok Tunnel**: External access for demos
3. **VPS Deployment**: Production deployment (see [deployment guide](project/docs/deployment.md))

**Note**: Ollama requires self-hosting, so Streamlit Cloud is not an option.

## 📈 Development Roadmap

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


## 🙏 Acknowledgments

- **LangChain**: RAG framework and chain orchestration
- **Ollama**: Local LLM deployment
- **ChromaDB**: Vector database
- **Streamlit**: Web frontend framework
- **SEC EDGAR**: Financial document data source


---

**Status**: 🟢 MVP + Post-MVP Enhancements Complete | **Version**: 1.0.0 | **Last Updated**: 2025-01-27

**Total Tasks Completed**: 23 (13 MVP + 10 Post-MVP Enhancements)
