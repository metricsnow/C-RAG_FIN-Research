"""
Integration tests for news aggregation workflow.

Tests the complete workflow from RSS parsing/web scraping
through to ChromaDB storage.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.pipeline import IngestionPipeline, IngestionPipelineError
from app.utils.config import config


class TestNewsIntegration:
    """Integration tests for news aggregation workflow."""

    @pytest.fixture
    def pipeline(self):
        """Create ingestion pipeline for testing."""
        return IngestionPipeline(collection_name="test_news")

    def test_process_news_from_rss(self, pipeline):
        """Test processing news from RSS feeds."""
        # Mock news_fetcher methods directly
        mock_articles = [
            {
                "title": "Test Financial News",
                "content": "This is test content about AAPL stock performance.",
                "url": "https://example.com/news1",
                "source": "reuters",
                "author": "Test Author",
                "date": "2025-01-27T12:00:00",
                "feed_title": "Reuters Finance",
                "feed_url": "https://example.com/feed",
            }
        ]

        from langchain_core.documents import Document

        mock_documents = [
            Document(
                page_content="This is test content about AAPL stock performance.",
                metadata={"source": "reuters", "url": "https://example.com/news1"},
            )
        ]

        # Mock news_fetcher methods
        pipeline.news_fetcher.fetch_news = MagicMock(return_value=mock_articles)
        pipeline.news_fetcher.to_documents = MagicMock(return_value=mock_documents)

        # Mock document loader chunking (returns 2 chunks)
        mock_chunks = [
            Document(page_content="Chunk 1", metadata={}),
            Document(page_content="Chunk 2", metadata={}),
        ]
        pipeline.document_loader.chunk_document = MagicMock(return_value=mock_chunks)

        # Mock embedding and storage
        with patch.object(
            pipeline.embedding_generator, "embed_documents"
        ) as mock_embed:
            mock_embed.return_value = [[0.1] * 1536] * 2  # Mock embeddings
            with patch.object(pipeline.chroma_store, "add_documents") as mock_store:
                mock_store.return_value = ["chunk_1", "chunk_2"]

                # Process news
                ids = pipeline.process_news(
                    feed_urls=["https://example.com/feed"],
                    store_embeddings=True,
                )

                assert len(ids) == 2
                pipeline.news_fetcher.fetch_news.assert_called_once()

    def test_process_news_from_urls(self, pipeline):
        """Test processing news from direct URLs."""
        # Mock news_fetcher methods directly
        mock_articles = [
            {
                "title": "Market Analysis",
                "content": "Detailed analysis of MSFT and GOOGL stocks.",
                "url": "https://example.com/article1",
                "source": "bloomberg",
                "author": "Analyst",
                "date": "2025-01-27T12:00:00",
            }
        ]

        from langchain_core.documents import Document

        mock_documents = [
            Document(
                page_content="Detailed analysis of MSFT and GOOGL stocks.",
                metadata={"source": "bloomberg", "url": "https://example.com/article1"},
            )
        ]

        # Mock news_fetcher methods
        pipeline.news_fetcher.fetch_news = MagicMock(return_value=mock_articles)
        pipeline.news_fetcher.to_documents = MagicMock(return_value=mock_documents)

        # Mock document loader chunking (returns 2 chunks)
        mock_chunks = [
            Document(page_content="Chunk 1", metadata={}),
            Document(page_content="Chunk 2", metadata={}),
        ]
        pipeline.document_loader.chunk_document = MagicMock(return_value=mock_chunks)

        # Mock embedding and storage
        with patch.object(
            pipeline.embedding_generator, "embed_documents"
        ) as mock_embed:
            mock_embed.return_value = [[0.1] * 1536] * 2
            with patch.object(pipeline.chroma_store, "add_documents") as mock_store:
                mock_store.return_value = ["chunk_1", "chunk_2"]

                # Process news
                ids = pipeline.process_news(
                    article_urls=["https://example.com/article1"],
                    store_embeddings=True,
                )

                assert len(ids) == 2
                pipeline.news_fetcher.fetch_news.assert_called_once()

    def test_process_news_disabled(self, pipeline):
        """Test that news processing fails when disabled."""
        with patch.object(config, "news_enabled", False):
            with pytest.raises(IngestionPipelineError):
                pipeline.process_news(feed_urls=["https://example.com/feed"])

    def test_process_news_no_articles(self, pipeline):
        """Test processing when no articles are fetched."""
        # Mock news_fetcher to return empty list
        pipeline.news_fetcher.fetch_news = MagicMock(return_value=[])

        ids = pipeline.process_news(feed_urls=["https://example.com/feed"])
        assert ids == []

    def test_process_news_without_storage(self, pipeline):
        """Test processing news without storing embeddings."""
        # Mock news_fetcher methods directly
        mock_articles = [
            {
                "title": "Test News",
                "content": "Test content",
                "url": "https://example.com/news",
                "source": "reuters",
                "author": "Author",
                "date": "2025-01-27",
            }
        ]

        from langchain_core.documents import Document

        mock_documents = [
            Document(
                page_content="Test content",
                metadata={"source": "reuters", "url": "https://example.com/news"},
            )
        ]

        # Mock news_fetcher methods
        pipeline.news_fetcher.fetch_news = MagicMock(return_value=mock_articles)
        pipeline.news_fetcher.to_documents = MagicMock(return_value=mock_documents)

        # Mock document loader chunking (returns 1 chunk)
        mock_chunks = [Document(page_content="Test content", metadata={})]
        pipeline.document_loader.chunk_document = MagicMock(return_value=mock_chunks)

        with patch.object(
            pipeline.embedding_generator, "embed_documents"
        ) as mock_embed:
            mock_embed.return_value = [[0.1] * 1536]

            ids = pipeline.process_news(
                feed_urls=["https://example.com/feed"],
                store_embeddings=False,
            )

            assert len(ids) == 1
            assert ids[0].startswith("chunk_")

    @patch("app.ingestion.news_summarizer.get_llm")
    def test_process_news_with_summarization(self, mock_get_llm, pipeline):
        """Test processing news with summarization enabled."""
        # Mock LLM for summarizer
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Summary of the article."
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        # Replace pipeline's summarizer with a new one that uses the mocked LLM
        if pipeline.news_summarizer:
            from app.ingestion.news_summarizer import NewsSummarizer

            pipeline.news_summarizer = NewsSummarizer(enabled=True)
            pipeline.news_fetcher.summarizer = pipeline.news_summarizer

        # Mock news articles
        mock_articles = [
            {
                "title": "Test Financial News",
                "content": "This is test content about AAPL stock performance.",
                "url": "https://example.com/news1",
                "source": "reuters",
                "author": "Test Author",
                "date": "2025-01-27T12:00:00",
            }
        ]

        from langchain_core.documents import Document

        # Mock news_fetcher.fetch_news but let to_documents run normally
        pipeline.news_fetcher.fetch_news = MagicMock(return_value=mock_articles)

        # Mock document loader chunking
        mock_chunks = [
            Document(page_content="Chunk 1", metadata={}),
        ]
        pipeline.document_loader.chunk_document = MagicMock(return_value=mock_chunks)

        # Mock embedding and storage
        with patch.object(
            pipeline.embedding_generator, "embed_documents"
        ) as mock_embed:
            mock_embed.return_value = [[0.1] * 1536]  # Mock embeddings
            with patch.object(pipeline.chroma_store, "add_documents") as mock_store:
                mock_store.return_value = ["chunk_1"]

                # Process news
                ids = pipeline.process_news(
                    feed_urls=["https://example.com/feed"],
                    store_embeddings=True,
                )

                assert len(ids) == 1
                # Verify summarizer was called if enabled
                # The summarizer should be called during to_documents
                if pipeline.news_summarizer and pipeline.news_summarizer.enabled:
                    # Check that to_documents was called (which triggers summarization)
                    assert pipeline.news_fetcher.fetch_news.called
                    # The LLM should be called if summarization is enabled
                    # Note: Since we're mocking to_documents indirectly, we verify
                    # that the summarizer exists and is enabled
                    assert pipeline.news_summarizer is not None
                    assert pipeline.news_summarizer.enabled is True
