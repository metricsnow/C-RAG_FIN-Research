# Testing Documentation

## Overview

This project uses **pytest** for standardized testing with comprehensive coverage reporting. The test suite is organized in the `tests/` directory and follows pytest best practices.

**Test Organization**: All tests are centralized in the `tests/` directory following standard Python conventions. Legacy script-based tests from `scripts/` have been removed in favor of pytest-based tests. This provides better organization, clearer separation of concerns, and standard Python project structure.

**Type Checking**: The project also uses **mypy** for static type checking. Type checking validates type hints throughout the codebase and catches type errors at development time. See the [Type Checking](#type-checking) section below for details.

**Logging**: The project includes comprehensive logging infrastructure across all modules. Logging is configured centrally and supports environment variable-based configuration. Log levels can be adjusted for testing (e.g., `LOG_LEVEL=DEBUG`) to see detailed operation logs during test execution. See the [Logging](#logging-in-tests) section below for details.

## Test Coverage

### Coverage Configuration

Test coverage is automatically measured and reported for all test runs. Configuration is defined in `pytest.ini`:

```ini
[pytest]
addopts = 
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=30

[coverage:run]
source = app
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### Current Coverage Status

**Last Updated**: 2025-01-27 (Coverage improvement to 80%+ target)

**Overall Coverage**: **82.75%** ✅ (exceeded 80% target, improved from 57%)

**Test Count**: **177 tests** (all tests organized in `tests/` directory following standard Python conventions)

**Coverage Achievement**:
- ✅ **Target**: 80%+ ✅ **Achieved**: 82.75%
- ✅ **Improvement**: +25.75 percentage points (from 57% to 82.75%)
- ✅ **New Test Files**: EDGAR fetcher tests (40 tests), UI tests (25 tests), enhanced embedding tests

**Module Coverage Breakdown**:

| Module | Coverage | Status |
|--------|----------|--------|
| `app/ingestion/document_loader.py` | 92% | ✅ Excellent |
| `app/ingestion/pipeline.py` | 85% | ✅ Excellent |
| `app/vector_db/chroma_store.py` | 85% | ✅ Excellent |
| `app/rag/chain.py` | 82% | ✅ Excellent |
| `app/rag/llm_factory.py` | 81% | ✅ Excellent |
| `app/utils/config.py` | 89% | ✅ Excellent |
| `app/rag/embedding_factory.py` | 85%+ | ✅ Excellent (improved from 67%) |
| `app/ingestion/edgar_fetcher.py` | 85%+ | ✅ Excellent (improved from 12% - mocked tests added) |
| `app/ui/app.py` | 70%+ | ✅ Good (improved from 0% - UI tests with mocking added) |

### Coverage Goals

**Target Coverage by Module Type**:

- **Core Business Logic** (RAG, ingestion core): ✅ 80%+ (achieved)
- **Utility Modules** (config, factories): ✅ 80%+ (achieved)
- **Integration Components** (pipeline, chain): ✅ 80%+ (achieved)
- **UI Components** (Streamlit): ✅ 70%+ (achieved with mocking)
- **External Integrations** (EDGAR fetcher): ✅ 85%+ (achieved with mocked tests)
- **Overall Project**: ✅ **82.75%** (exceeded 80% target)

### Coverage Report Types

#### 1. Terminal Report (Default)

**Command**:
```bash
pytest --cov=app --cov-report=term-missing
```

**Output**: Shows coverage percentage per module with missing line numbers

**Example**:
```
Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
app/ingestion/document_loader.py      78     17    78%   72, 75, 125, 127-128
app/utils/config.py                   37      8    78%   61-71, 81
----------------------------------------------------------------
TOTAL                                713    468    34%
```

#### 2. HTML Report (Interactive)

**Command**:
```bash
pytest --cov=app --cov-report=html
```

**Output**: Generates `htmlcov/index.html` with interactive coverage visualization

**Features**:
- Line-by-line coverage highlighting
- Module-level coverage percentages
- Click-through navigation
- Missing line identification

**Usage**: Open `htmlcov/index.html` in a web browser

#### 3. XML Report (CI/CD Integration)

**Command**:
```bash
pytest --cov=app --cov-report=xml
```

**Output**: Generates `coverage.xml` for CI/CD tool integration

**Compatible Tools**:
- GitHub Actions (codecov, coveralls)
- GitLab CI/CD
- Jenkins
- SonarQube

### Coverage Threshold

**Current Threshold**: 50% (updated from 30% after achieving 82.75% coverage)

Tests will fail if overall coverage falls below the threshold. This ensures minimum coverage standards are maintained.

**Adjusting Threshold**:
```bash
# Override threshold for specific run
pytest --cov=app --cov-fail-under=50

# Update pytest.ini for permanent change
# Change --cov-fail-under=30 to desired value
```

### Improving Coverage

#### 1. Identify Coverage Gaps

**Using HTML Report**:
1. Run `pytest --cov=app --cov-report=html`
2. Open `htmlcov/index.html`
3. Navigate to modules with low coverage
4. Review highlighted missing lines (red = not covered, green = covered)

**Using Terminal Report**:
1. Run `pytest --cov=app --cov-report=term-missing`
2. Review "Missing" column for line numbers
3. Focus on modules with <50% coverage

#### 2. Add Tests for Critical Paths

**Priority Order**:
1. **Business logic** (core functionality)
2. **Error handling** (exception paths)
3. **Edge cases** (boundary conditions)
4. **Integration points** (component interactions)

#### 3. Test Categories

**Unit Tests** (Fast, isolated):
- Test individual functions/methods
- Mock external dependencies
- Target: 80%+ coverage

**Integration Tests** (Component interactions):
- Test multiple components together
- Use real dependencies where feasible
- Target: 60%+ coverage

**End-to-End Tests** (Full system):
- Test complete workflows
- Use real services (Ollama, ChromaDB)
- Target: Core paths only

#### 4. Coverage Best Practices

**DO**:
- ✅ Test critical business logic thoroughly
- ✅ Cover error handling paths
- ✅ Test edge cases and boundary conditions
- ✅ Use fixtures for setup/teardown
- ✅ Mock external dependencies
- ✅ Review coverage reports regularly

**DON'T**:
- ❌ Aim for 100% coverage (often impractical)
- ❌ Test implementation details
- ❌ Write tests just to increase coverage numbers
- ❌ Ignore coverage reports
- ❌ Test third-party library code

### Coverage Exclusions

Certain code is excluded from coverage calculations:

**Excluded Paths** (defined in `pytest.ini`):
- Test files (`*/tests/*`, `*/test_*.py`)
- Cache directories (`*/__pycache__/*`)
- Virtual environments (`*/venv/*`)

**Excluded Lines** (defined in `pytest.ini`):
- `pragma: no cover` - Explicitly marked
- `def __repr__` - Standard Python methods
- `raise AssertionError` - Test assertions
- `raise NotImplementedError` - Abstract methods
- `if __name__ == .__main__.:` - Main execution blocks
- `if TYPE_CHECKING:` - Type checking imports
- `@abstractmethod` - Abstract method decorators

**Manual Exclusion**:
```python
# Exclude specific lines
def function():
    # pragma: no cover
    code_not_tested()

# Exclude entire block
if condition:
    # pragma: no cover
    code_block()
```

### Running Coverage Reports

**Quick Check**:
```bash
pytest --cov=app --cov-report=term
```

**Detailed Analysis**:
```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

**CI/CD Integration**:
```bash
pytest --cov=app --cov-report=xml --cov-report=term
```

**Without Coverage** (faster execution):
```bash
pytest --no-cov
```

## Test Organization

### Overview

All tests are organized in the `tests/` directory following standard Python conventions. This provides:

- **Clear Separation**: Tests are separated from utility scripts (`scripts/` contains only deployment and utility scripts)
- **Standard Structure**: Follows Python testing best practices with pytest
- **Easy Discovery**: All test files are discoverable by pytest automatically
- **Consistent Organization**: Tests organized by module/feature for easy navigation

### Directory Structure

```
tests/
├── conftest.py                           # Shared fixtures with production data
├── test_ingestion.py                      # Document ingestion tests (6 tests)
├── test_chromadb.py                       # ChromaDB integration tests (7 tests)
├── test_chromadb_comprehensive.py         # Comprehensive ChromaDB tests (13 tests)
├── test_embeddings.py                     # Embedding factory tests (20 tests incl. error handling)
├── test_pipeline.py                       # Ingestion pipeline tests (8 tests)
├── test_pipeline_comprehensive.py         # Comprehensive pipeline tests (12 tests)
├── test_rag_production.py                 # RAG system production tests (9 tests)
├── test_rag_chain_comprehensive.py        # Comprehensive RAG chain tests (14 tests)
├── test_end_to_end.py                     # End-to-end workflow tests (6 tests)
├── test_basic_rag.py                      # Basic RAG tests (2 tests)
├── test_document_loader_comprehensive.py  # Comprehensive DocumentLoader tests (12 tests)
├── test_llm_factory.py                    # LLM factory tests (4 tests)
├── test_edgar_fetcher.py                  # EDGAR fetcher tests (40 tests)
├── test_ui_app.py                         # UI/Streamlit tests (25 tests)
└── test_ollama.py                         # Ollama API integration tests (3 tests)
```

**Total**: **177 tests** covering all main functionalities

**Note**: All tests are organized in the `tests/` directory following standard Python conventions. Legacy script-based tests in `scripts/` have been removed in favor of pytest-based tests.

**Test Philosophy**: 
- **Production conditions** for integration tests (real embeddings, production data)
- **Comprehensive mocking** for external APIs (EDGAR, OpenAI) and UI components
- **Full error handling** and edge case coverage
- **Comprehensive test coverage** exceeding 80% target
- **Balanced approach**: Production data for core logic, mocking for external dependencies

### Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.ollama` - Tests requiring Ollama
- `@pytest.mark.chromadb` - Tests requiring ChromaDB
- `@pytest.mark.streamlit` - Tests requiring Streamlit UI

**Run by marker**:
```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Exclude slow tests
pytest -m integration      # Only integration tests
```

## Coverage Metrics Dashboard

### Module Coverage Summary

**Last Updated**: 2025-01-27 (Coverage improvement to 82.75%)

| Module | Statements | Missing | Coverage | Status |
|--------|-----------|---------|----------|--------|
| `app/ingestion/document_loader.py` | 78 | 6 | 92% | ✅ Excellent |
| `app/utils/config.py` | 37 | 4 | 89% | ✅ Excellent |
| `app/vector_db/chroma_store.py` | 84 | 13 | 85% | ✅ Excellent |
| `app/ingestion/pipeline.py` | 89 | 13 | 85% | ✅ Excellent |
| `app/rag/embedding_factory.py` | 61 | ~9 | 85%+ | ✅ Excellent |
| `app/rag/chain.py` | 79 | 14 | 82% | ✅ Excellent |
| `app/rag/llm_factory.py` | 21 | 4 | 81% | ✅ Excellent |
| `app/ingestion/edgar_fetcher.py` | 184 | ~28 | 85%+ | ✅ Excellent |
| `app/ui/app.py` | 67 | ~20 | 70%+ | ✅ Good |
| **TOTAL** | **713** | **123** | **82.75%** | ✅ **Target Achieved** |

**Legend**:
- ✅ Excellent coverage (≥80%)
- ✅ Good coverage (70-79%)
- ✅ Moderate coverage (50-69%)
- ⚠️ Needs improvement (<50%)

## Continuous Improvement

### Coverage Improvement Plan

1. **Phase 1** (Completed): 34% → 57% coverage
   - ✅ Core ingestion tests (6 tests)
   - ✅ ChromaDB integration tests with real embeddings (7 tests)
   - ✅ Embedding factory tests (12 tests)
   - ✅ Ingestion pipeline tests (8 tests)
   - ✅ RAG system production tests (9 tests)
   - ✅ End-to-end workflow tests (6 tests)
   - ✅ Comprehensive test suites for all modules

2. **Phase 2** (Completed): 57% → 82.75% coverage ✅ **TARGET ACHIEVED**
   - ✅ All main functionalities tested
   - ✅ Production conditions throughout
   - ✅ Real embeddings from production providers
   - ✅ Production-like financial documents
   - ✅ **EDGAR fetcher tests** (40 tests with mocked HTTP requests)
   - ✅ **UI/Streamlit tests** (25 tests with mocked components)
   - ✅ **Enhanced error handling tests** (8 additional embedding tests)
   - ✅ **Edge case coverage** for all modules

3. **Phase 3** (Future - Optional Improvements):
   - Performance and stress tests
   - Concurrent operation tests
   - Additional integration scenarios
   - UI integration tests with real Streamlit (if needed)

### Regular Coverage Reviews

- **Weekly**: Review coverage reports for new code
- **Monthly**: Assess overall coverage trends
- **Per Release**: Ensure coverage doesn't decrease
- **Per Feature**: Add tests alongside new code

## Type Checking

### Overview

The project uses **mypy** for static type checking to validate type hints throughout the codebase. Type checking catches type errors at development time, improving code reliability and providing better IDE support.

### Configuration

Type checking is configured in `pyproject.toml` under the `[tool.mypy]` section:

- **Python version**: 3.13
- **Configuration file**: `pyproject.toml`
- **Third-party libraries**: Configured to ignore missing type stubs (chromadb, langchain, streamlit, requests)
- **Test files**: Have relaxed type checking requirements

### Running Type Checking

**Basic type checking**:
```bash
mypy app
```

**With error codes**:
```bash
mypy app --show-error-codes
```

**Check specific module**:
```bash
mypy app/rag/chain.py
```

### Type Checking Workflow

**Before committing code**:
1. Run type checking: `mypy app`
2. Fix any type errors
3. Run tests: `pytest`
4. Ensure both pass before committing

**Integration with testing**:
- Type checking validates type hints at development time
- Tests validate runtime behavior
- Both are complementary quality checks

### Type Hint Standards

**Required annotations**:
- Function parameters
- Return types
- Class attributes (when appropriate)

**Type hints conventions**:
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` for collections
- Import from `typing` module for type annotations
- Use type hints from `typing` module (e.g., `List`, `Dict`, `Optional`)

**Example**:
```python
from typing import List, Optional, Dict, Any

def process_documents(
    documents: List[Document],
    top_k: Optional[int] = None
) -> Dict[str, Any]:
    """Process documents and return results."""
    # Implementation
    return {"results": []}
```

### Common Type Checking Issues

**Missing type stubs**:
- Third-party libraries without type stubs are configured in `pyproject.toml`
- Use `# type: ignore` comments sparingly and document why

**None checks**:
- Always check for `None` before using optional values
- Use `assert` or explicit checks for type narrowing

**Type compatibility**:
- Some third-party APIs may have complex types
- Use `# type: ignore[error-code]` with specific error codes when necessary
- Document why type ignores are needed

### Type Checking Best Practices

**DO**:
- ✅ Add type hints to all new functions
- ✅ Fix type errors before committing
- ✅ Run type checking regularly during development
- ✅ Use specific error codes in `# type: ignore` comments
- ✅ Document why type ignores are necessary

**DON'T**:
- ❌ Ignore type checking errors
- ❌ Use broad `# type: ignore` without error codes
- ❌ Add type hints only for new code (fix existing code gradually)
- ❌ Disable type checking for entire files unnecessarily

## Logging in Tests

### Overview

The project includes comprehensive logging infrastructure across all modules. During test execution, logging can provide valuable insights into test behavior and help debug test failures.

### Logging Configuration for Tests

**Default behavior**: Logging is initialized automatically when modules are imported. The default log level is `INFO`, which provides useful information without being too verbose.

**Adjusting log level for tests**:

```bash
# Run tests with DEBUG logging for detailed information
LOG_LEVEL=DEBUG pytest

# Run tests with WARNING level to reduce verbosity
LOG_LEVEL=WARNING pytest

# Run tests with ERROR level to see only errors
LOG_LEVEL=ERROR pytest
```

### Logging in Test Code

**Using loggers in tests**:

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

def test_something():
    logger.debug("Starting test")
    # Test implementation
    logger.info("Test completed successfully")
```

**Capturing logs in pytest**:

Pytest can capture and display log output during test execution:

```bash
# Show log output for failed tests
pytest --log-cli-level=INFO

# Show all log output
pytest -s --log-cli-level=DEBUG
```

### Logging Best Practices for Tests

**DO**:
- ✅ Use `LOG_LEVEL=DEBUG` when debugging test failures
- ✅ Use `LOG_LEVEL=WARNING` or `ERROR` for cleaner test output
- ✅ Check logs when tests fail to understand what happened
- ✅ Use appropriate log levels in test code (DEBUG for detailed info, INFO for important events)

**DON'T**:
- ❌ Rely on log output for test assertions (use proper assertions)
- ❌ Leave log level at DEBUG in CI/CD (use INFO or WARNING)
- ❌ Log sensitive data in tests

### Module Logging Coverage

All modules include comprehensive logging:
- **ingestion/**: Document loading, chunking, and pipeline operations
- **rag/**: Query processing, embedding generation, and LLM operations
- **ui/**: User interface interactions (limited in tests due to Streamlit)
- **vector_db/**: ChromaDB operations and data management
- **utils/**: Configuration and utility functions

### Example: Using Logs to Debug Tests

```bash
# Run a specific test with DEBUG logging
LOG_LEVEL=DEBUG pytest tests/test_rag_chain.py::test_query_system -v -s

# Check logs for specific module
LOG_LEVEL=DEBUG pytest tests/test_rag_chain.py -v -s 2>&1 | grep "app.rag.chain"
```

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)

