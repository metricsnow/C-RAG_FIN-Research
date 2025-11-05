"""
Shared pytest fixtures and configuration for test suite.

This module provides common fixtures used across all tests, including
configuration setup, production-like test data, and real embeddings.
All fixtures use production conditions - no demo or mock data.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root directory path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root_path):
    """Return the test data directory path, creating it if needed."""
    data_dir = project_root_path / "data" / "test"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def test_documents_dir(project_root_path):
    """Return the test documents directory path, creating it if needed."""
    docs_dir = project_root_path / "data" / "test" / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


@pytest.fixture(scope="session")
def embedding_generator():
    """Create real embedding generator for production testing."""
    from app.rag.embedding_factory import EmbeddingGenerator

    try:
        generator = EmbeddingGenerator()
        # Verify it works by getting dimensions
        _ = generator.get_embedding_dimensions()
        return generator
    except Exception as e:
        pytest.skip(f"Embedding generator not available: {e}")


@pytest.fixture
def production_financial_document_1():
    """Production-like financial document: SEC 10-K excerpt on revenue."""
    return """FORM 10-K
ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934

Item 1. Business

Revenue Recognition

Our revenue is primarily generated from product sales and service contracts. Revenue from product sales is recognized when control of the product is transferred to the customer, which typically occurs upon shipment or delivery. Service revenue is recognized over time as services are performed.

Revenue from licensing agreements is recognized when the license is delivered and the customer has the right to use the software. For multi-element arrangements, we allocate revenue to each element based on the relative standalone selling price.

Total revenue for the fiscal year ended December 31, 2023 was $394.3 billion, representing an increase of 7% compared to the prior year. Product revenue accounted for $245.8 billion, while service revenue was $148.5 billion.

Key revenue drivers include:
- Increased unit sales volume across all product categories
- Expansion into new geographic markets
- Growth in subscription-based service offerings
- Strategic partnerships and distribution channels

We expect revenue growth to continue in fiscal 2024, driven by product innovation, market expansion, and strategic investments in research and development."""


@pytest.fixture
def production_financial_document_2():
    """Production-like financial document: Risk factors from 10-K."""
    return """FORM 10-K
RISK FACTORS

Our business is subject to various risks and uncertainties. The following risk factors could materially and adversely affect our business, financial condition, and results of operations.

Market Risks

We operate in highly competitive markets with rapid technological change. Failure to compete effectively could result in loss of market share, reduced revenue, and lower profitability. Key competitive factors include product features, pricing, brand recognition, and customer service.

Economic downturns and market volatility can significantly impact consumer spending and business investment decisions. Reduced demand for our products and services during economic downturns could negatively affect our revenue and operating results.

Regulatory and Legal Risks

We are subject to extensive government regulation in the jurisdictions where we operate. Changes in regulations, including data privacy laws, trade policies, and tax regulations, could increase our costs, limit our ability to operate in certain markets, or require significant changes to our business practices.

We face potential legal claims and proceedings, including intellectual property disputes, product liability claims, and regulatory investigations. Unfavorable outcomes in legal proceedings could result in significant monetary damages, injunctive relief, or other penalties."""


@pytest.fixture
def production_financial_document_3():
    """Production-like financial document: Cash flow and liquidity."""
    return """FORM 10-K
MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS

Liquidity and Capital Resources

As of December 31, 2023, we had cash and cash equivalents of $29.4 billion and short-term investments of $24.8 billion. Our principal sources of liquidity are cash generated from operations, existing cash and investment balances, and available credit facilities.

Cash provided by operating activities was $110.5 billion for fiscal 2023, compared to $104.4 billion for fiscal 2022. The increase was primarily due to higher net income and improved working capital management.

Cash used in investing activities was $22.3 billion for fiscal 2023, primarily for capital expenditures, acquisitions, and strategic investments. We invested $15.8 billion in property, plant, and equipment, including data centers and manufacturing facilities.

Cash used in financing activities was $77.6 billion for fiscal 2023, primarily for share repurchases of $75.0 billion and dividend payments of $14.9 billion, partially offset by proceeds from stock option exercises.

We believe our current cash, cash equivalents, and short-term investments, together with cash generated from operations and available credit facilities, will be sufficient to meet our anticipated cash needs for at least the next 12 months."""


@pytest.fixture
def production_financial_document_4():
    """Production-like financial document: Investment strategies and portfolio management."""
    return """INVESTMENT MANAGEMENT REPORT

Portfolio Construction and Asset Allocation

Our investment strategy focuses on long-term wealth creation through diversified asset allocation across equities, fixed income, and alternative investments. The target allocation for a moderate risk portfolio is 60% equities, 30% fixed income, and 10% alternatives.

Equity investments are allocated across multiple sectors including technology, healthcare, financial services, and consumer goods. Geographic diversification includes domestic (60%), developed international markets (30%), and emerging markets (10%).

Fixed income allocation emphasizes high-quality bonds with varying maturities. The portfolio includes government securities, investment-grade corporate bonds, and municipal bonds. Duration is managed to balance income generation with interest rate risk.

Risk Management

We employ multiple risk management techniques including diversification, hedging strategies, and position sizing. Portfolio risk is monitored through value-at-risk (VaR) calculations, stress testing, and scenario analysis.

Diversification reduces portfolio volatility by spreading risk across uncorrelated assets. We target a portfolio correlation of less than 0.7 to ensure effective diversification benefits.

Hedging strategies include options contracts, futures, and currency hedges to protect against adverse market movements. Hedging costs are balanced against potential downside protection benefits."""


@pytest.fixture
def production_financial_document_5():
    """Production-like financial document: Market analysis and economic outlook."""
    return """MARKET ANALYSIS REPORT
Q4 2023 Economic and Financial Market Outlook

Executive Summary

Global financial markets experienced significant volatility in 2023, driven by inflation concerns, central bank policy shifts, and geopolitical tensions. Equity markets showed resilience despite early-year declines, with the S&P 500 gaining 24% for the year.

Interest Rate Environment

The Federal Reserve raised the federal funds rate to 5.25-5.50% by mid-2023, representing the highest level in over 20 years. Inflation has moderated from peak levels of 9.1% in June 2022 to 3.2% by December 2023, approaching the Fed's 2% target.

Bond markets experienced negative returns in early 2023 as rates rose, but recovered as rate increases slowed. The 10-year Treasury yield peaked at 4.99% in October before declining to 3.88% by year-end.

Equity Market Performance

Technology stocks led market gains, with the Nasdaq Composite rising 43% for the year. The artificial intelligence sector attracted significant investment, driving valuations for AI-related companies. Energy and utilities underperformed as oil prices declined from 2022 highs.

Small-cap stocks lagged large-cap performance, with the Russell 2000 gaining 16% compared to the S&P 500's 24% gain. International markets showed mixed results, with developed markets up 18% and emerging markets up 8%."""


@pytest.fixture
def sample_text_content():
    """Return sample text content for basic testing."""
    return """This is a sample text document for testing the ingestion pipeline.

It contains multiple paragraphs to test chunking functionality.

The document loader should be able to process this file and split it into chunks
with appropriate metadata. Each chunk should have information about the source,
date, type, and chunk index.

This is the final paragraph of the sample text document.
"""


@pytest.fixture
def sample_markdown_content():
    """Return sample Markdown content for testing."""
    return """# Sample Markdown Document

This is a sample Markdown document for testing the ingestion pipeline.

## Features

- Text extraction
- Chunking with overlap
- Metadata management

## Content

The document loader should process Markdown files correctly and maintain
the structure while chunking the content appropriately.

### Subsection

This is a subsection to test how Markdown content is handled during chunking.
"""


@pytest.fixture
def sample_financial_content():
    """Return sample financial document content for testing."""
    return """
Financial Markets Overview

The stock market is a financial market where shares of publicly traded companies are bought and sold.
Stock prices fluctuate based on supply and demand, company performance, economic indicators, and market sentiment.

Bonds are debt securities issued by governments or corporations to raise capital.
Bond prices are inversely related to interest rates - when rates rise, bond prices fall.

Investment strategies include diversification, asset allocation, and risk management.
Diversification helps reduce portfolio risk by spreading investments across different assets.
"""


@pytest.fixture(autouse=True)
def reset_paths():
    """Ensure project root is in sys.path for each test."""
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup if needed
