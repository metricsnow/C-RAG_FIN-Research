# Financial Sentiment Analysis Integration (TASK-039)

## Overview

The Financial Research Assistant integrates comprehensive sentiment analysis capabilities to analyze financial documents including earnings call transcripts, MD&A sections, and news articles. The system uses multiple sentiment analysis models (FinBERT, TextBlob, VADER) to provide accurate financial sentiment analysis with forward guidance and risk factor extraction.

## Implementation Status

**Status**: ✅ Complete (2025-01-27)
**Models Supported**: FinBERT, TextBlob, VADER
**Integration**: Automatic during document ingestion

## Sentiment Analysis Models

### FinBERT

**Model**: `ProsusAI/finbert`
**Type**: Financial domain-specific BERT model
**Accuracy**: Highest for financial text
**Speed**: Slower (requires model download ~400MB)
**Recommended**: Yes, for production use

**Features**:
- Trained specifically on financial text
- Three-class classification: positive, negative, neutral
- Provides confidence scores
- Best accuracy for earnings calls and financial filings

**Usage**:
```python
from app.ingestion.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer(use_finbert=True)
result = analyzer.analyze_sentiment("We expect strong revenue growth in Q4.")
print(result["finbert"]["sentiment"])  # positive
print(result["finbert"]["score"])  # 0.85
```

### TextBlob

**Type**: Rule-based sentiment scoring
**Accuracy**: Good for general text
**Speed**: Fast
**Recommended**: Yes, as fallback or for general sentiment

**Features**:
- Polarity score (-1.0 to 1.0)
- Subjectivity score (0.0 to 1.0)
- Fast processing
- No model download required

**Usage**:
```python
analyzer = SentimentAnalyzer(use_textblob=True)
result = analyzer.analyze_sentiment("This is great news for investors!")
print(result["textblob"]["sentiment"])  # positive
print(result["textblob"]["polarity"])  # 0.5
```

### VADER

**Type**: Financial text-optimized sentiment analyzer
**Accuracy**: Good for financial text
**Speed**: Fast
**Recommended**: Yes, as fallback or for balanced speed/accuracy

**Features**:
- Compound score (-1.0 to 1.0)
- Positive, neutral, negative scores
- Optimized for financial text
- Fast processing
- No model download required

**Usage**:
```python
analyzer = SentimentAnalyzer(use_vader=True)
result = analyzer.analyze_sentiment("Market volatility concerns investors.")
print(result["vader"]["sentiment"])  # negative
print(result["vader"]["compound"])  # -0.6
```

## Automatic Integration

Sentiment analysis is automatically applied during document ingestion through the `IngestionPipeline`. No manual intervention is required.

**How It Works**:
1. Document is processed through ingestion pipeline
2. Sentiment analyzer enriches document metadata
3. Sentiment scores and extracted information stored as metadata
4. Document chunks inherit sentiment metadata

**Example**:
```python
from app.ingestion.pipeline import IngestionPipeline
from langchain_core.documents import Document

pipeline = IngestionPipeline()

# Create document
doc = Document(
    page_content="We expect revenue growth of 15% in the next quarter.",
    metadata={"source": "earnings_call", "ticker": "AAPL"}
)

# Process document (sentiment analysis applied automatically)
chunk_ids = pipeline.process_document_objects([doc])

# Sentiment metadata is now in document chunks
```

## Forward Guidance Extraction

The system automatically extracts forward guidance statements from documents using keyword-based detection.

**Keywords Detected**:
- guidance, outlook, forecast, expect, anticipate, project, target, estimate, believe, plan, intend, should, will, may, could
- fiscal year, quarter, revenue, earnings, growth, margin, profit

**Example**:
```python
from app.ingestion.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
text = """
We expect strong growth in the next quarter.
Our guidance for fiscal year 2025 is positive.
We anticipate revenue of $100M.
"""

guidance = analyzer.extract_forward_guidance(text)
print(len(guidance))  # 3
print(guidance[0])  # "We expect strong growth in the next quarter."
```

**Metadata**:
- `forward_guidance_count`: Number of forward guidance statements
- `has_forward_guidance`: Boolean flag

## Risk Factor Extraction

The system automatically extracts risk factors from documents using keyword-based detection.

**Keywords Detected**:
- risk, uncertainty, volatility, challenge, concern, threat, adverse, negative, decline, decrease, loss, failure
- litigation, regulation, competition, market conditions

**Example**:
```python
from app.ingestion.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
text = """
There are significant risks in the market.
Uncertainty about future regulations may impact results.
Competition poses a threat to our business.
"""

risks = analyzer.extract_risk_factors(text)
print(len(risks))  # 3
print(risks[0])  # "There are significant risks in the market."
```

**Metadata**:
- `risk_factors_count`: Number of risk factors identified
- `has_risk_factors`: Boolean flag

## Comprehensive Document Analysis

The `analyze_document()` method provides comprehensive analysis including sentiment, forward guidance, and risk factors.

**Example**:
```python
from app.ingestion.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
text = """
We expect strong growth in the next quarter.
Our guidance is positive for revenue.
However, there are risks in market conditions.
"""

result = analyzer.analyze_document(
    text,
    extract_guidance=True,
    extract_risks=True
)

print(result["sentiment"]["overall_sentiment"])  # positive
print(result["forward_guidance_count"])  # 2
print(result["risk_factors_count"])  # 1
```

## Configuration

See [Configuration Documentation](../reference/configuration.md#financial-sentiment-analysis-configuration-task-039) for all sentiment analysis settings.

**Key Settings**:
```bash
# Enable sentiment analysis
SENTIMENT_ENABLED=true

# Select models
SENTIMENT_USE_FINBERT=true
SENTIMENT_USE_TEXTBLOB=true
SENTIMENT_USE_VADER=true

# Enable extraction features
SENTIMENT_EXTRACT_GUIDANCE=true
SENTIMENT_EXTRACT_RISKS=true
```

## Querying with Sentiment Metadata

Sentiment metadata enables sentiment-aware queries through the RAG system.

**Example Queries**:
```python
# Query for positive sentiment documents
"Find documents with positive sentiment about revenue growth"

# Query for forward guidance
"Show me forward guidance statements from earnings calls"

# Query for risk factors
"What are the risk factors mentioned in recent filings?"
```

**Metadata Filtering**:
```python
from app.vector_db import ChromaStore

store = ChromaStore()

# Query with sentiment filter
results = store.query_by_embedding(
    query_embedding=embedding,
    n_results=10,
    where={"sentiment": "positive"}
)

# Query for documents with forward guidance
results = store.query_by_embedding(
    query_embedding=embedding,
    n_results=10,
    where={"has_forward_guidance": True}
)
```

## Integration with Other Features

### Earnings Call Transcripts (TASK-033)

Sentiment analysis is automatically applied to earnings call transcripts:
- Management commentary sentiment
- Q&A section sentiment
- Forward guidance extraction
- Risk factor identification

### Financial News (TASK-034)

Sentiment analysis is automatically applied to news articles:
- Article sentiment scoring
- Ticker-specific sentiment
- Category-based sentiment analysis

### MD&A Sections

Sentiment analysis is automatically applied to MD&A sections from SEC filings:
- Management discussion sentiment
- Forward guidance extraction
- Risk factor analysis

## Performance Considerations

**Model Performance**:
- FinBERT: ~2-5 seconds per document (first run slower due to model download)
- TextBlob: ~0.1 seconds per document
- VADER: ~0.1 seconds per document

**Optimization Tips**:
- Use FinBERT for production (best accuracy)
- Use TextBlob/VADER for faster processing
- Disable extraction features if not needed
- Process documents in batches for efficiency

## Dependencies

**Required Libraries**:
- `transformers>=4.40.0` (for FinBERT)
- `torch>=2.0.0` (for transformers)
- `textblob>=0.17.1` (for TextBlob)
- `vaderSentiment>=3.3.2` (for VADER)

**Installation**:
```bash
pip install transformers torch textblob vaderSentiment
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Error Handling

The sentiment analyzer includes comprehensive error handling:
- Graceful fallback if models fail to load
- Continues processing if sentiment analysis fails
- Logs warnings for debugging
- Returns neutral sentiment if all models fail

**Example**:
```python
# If FinBERT fails to load, falls back to VADER/TextBlob
# If all models fail, returns neutral sentiment
result = analyzer.analyze_sentiment(text)
# Always returns valid result
```

## Testing

Comprehensive test suite available in `tests/test_sentiment_analyzer.py`:
- Model initialization tests
- Sentiment analysis tests
- Forward guidance extraction tests
- Risk factor extraction tests
- Error handling tests

**Run Tests**:
```bash
pytest tests/test_sentiment_analyzer.py -v
```

## Future Enhancements

Potential future improvements:
- Custom FinBERT fine-tuning on domain-specific data
- Sentiment trend analysis over time
- Multi-language sentiment support
- Sentiment-based document ranking
- Sentiment visualization in UI

## References

- **FinBERT**: [ProsusAI/finbert on Hugging Face](https://huggingface.co/ProsusAI/finbert)
- **TextBlob**: [TextBlob Documentation](https://textblob.readthedocs.io/)
- **VADER**: [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment)
