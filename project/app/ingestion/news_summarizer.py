"""
News summarization module.

Generates concise summaries of financial news articles using LLM-based
summarization with prompt engineering for financial domain.
"""

from typing import Dict, List, Optional

from app.rag.llm_factory import get_llm
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NewsSummarizerError(Exception):
    """Custom exception for news summarizer errors."""

    pass


class NewsSummarizer:
    """
    News article summarizer using LLM-based summarization.

    Generates concise summaries (50-200 words) of financial news articles,
    preserving key financial information like tickers, events, and numbers.
    """

    # Default summarization prompt template
    SUMMARY_PROMPT_TEMPLATE = (
        """Summarize the following financial news article in """
        """{target_words} words or less.

Focus on:
- Key financial information (tickers, numbers, percentages, dates)
- Main events or developments
- Market impact or significance
- Company or sector information

Article:
{article_content}

Summary:"""
    )

    def __init__(
        self,
        enabled: bool = True,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        target_words: int = 150,
        min_words: int = 50,
        max_words: int = 200,
    ):
        """
        Initialize news summarizer.

        Args:
            enabled: Whether summarization is enabled (default: True)
            llm_provider: LLM provider ('ollama' or 'openai'). If None, uses config
            llm_model: Model name. If None, uses default for provider
            target_words: Target summary length in words (default: 150)
            min_words: Minimum summary length in words (default: 50)
            max_words: Maximum summary length in words (default: 200)

        Raises:
            NewsSummarizerError: If initialization fails
        """
        self.enabled = enabled
        self.target_words = target_words
        self.min_words = min_words
        self.max_words = max_words

        if not enabled:
            logger.info("News summarization is disabled")
            self.llm = None
            return

        try:
            provider = llm_provider or config.LLM_PROVIDER
            logger.debug(
                f"Initializing NewsSummarizer with provider={provider}, "
                f"model={llm_model}, target_words={target_words}"
            )
            self.llm = get_llm(provider=provider, model=llm_model)
            logger.info(
                f"NewsSummarizer initialized: provider={provider}, "
                f"target_words={target_words}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize NewsSummarizer: {str(e)}")
            raise NewsSummarizerError(
                f"Failed to initialize NewsSummarizer: {str(e)}"
            ) from e

    def summarize_article(self, article: Dict) -> Optional[str]:
        """
        Summarize a single news article.

        Args:
            article: Article dictionary with 'title' and 'content' keys

        Returns:
            Summary string (50-200 words) or None if summarization fails

        Raises:
            NewsSummarizerError: If summarization fails critically
        """
        if not self.enabled or self.llm is None:
            logger.debug("Summarization is disabled, skipping")
            return None

        try:
            # Extract article content
            title = article.get("title", "")
            content = article.get("content", "")

            if not content:
                logger.warning("Article has no content, cannot summarize")
                return None

            # Combine title and content
            article_content = f"{title}\n\n{content}".strip()

            if not article_content:
                logger.warning("Article content is empty, cannot summarize")
                return None

            # Truncate very long articles to avoid token limits
            # Keep first 4000 characters (roughly 800-1000 words)
            if len(article_content) > 4000:
                logger.debug(
                    f"Article is long ({len(article_content)} chars), "
                    "truncating to 4000 chars"
                )
                article_content = article_content[:4000] + "..."

            # Build prompt
            prompt = self.SUMMARY_PROMPT_TEMPLATE.format(
                target_words=self.target_words,
                article_content=article_content,
            )

            # Generate summary
            logger.debug(f"Generating summary for article: {title[:50]}...")
            summary = self.llm.invoke(prompt)

            # Extract summary text (handle different LLM response formats)
            if hasattr(summary, "content"):
                summary_text = summary.content
            elif isinstance(summary, str):
                summary_text = summary
            else:
                summary_text = str(summary)

            # Clean and validate summary
            summary_text = summary_text.strip()

            if not summary_text:
                logger.warning("Generated summary is empty")
                return None

            # Validate word count
            word_count = len(summary_text.split())
            if word_count < self.min_words:
                logger.warning(
                    f"Summary is too short ({word_count} words, "
                    f"minimum {self.min_words}), but returning it"
                )
            elif word_count > self.max_words:
                logger.warning(
                    f"Summary is too long ({word_count} words, "
                    f"maximum {self.max_words}), truncating"
                )
                # Truncate to max_words
                words = summary_text.split()
                summary_text = " ".join(words[: self.max_words])

            logger.debug(
                f"Generated summary: {len(summary_text)} chars, " f"{word_count} words"
            )
            return summary_text

        except Exception as e:
            logger.error(f"Failed to summarize article: {str(e)}")
            # Don't raise exception - return None to allow pipeline to continue
            return None

    def summarize_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Summarize multiple news articles.

        Args:
            articles: List of article dictionaries

        Returns:
            List of article dictionaries with 'summary' key added to metadata
        """
        if not self.enabled:
            logger.debug("Summarization is disabled, skipping batch")
            return articles

        logger.info(f"Summarizing {len(articles)} articles")
        summarized_articles = []

        for i, article in enumerate(articles, 1):
            try:
                summary = self.summarize_article(article)
                if summary:
                    article["summary"] = summary
                    logger.debug(
                        f"Article {i}/{len(articles)} summarized: "
                        f"{article.get('title', 'Unknown')[:50]}..."
                    )
                else:
                    logger.debug(
                        f"Article {i}/{len(articles)} summary failed: "
                        f"{article.get('title', 'Unknown')[:50]}..."
                    )
                summarized_articles.append(article)
            except Exception as e:
                logger.error(f"Error summarizing article {i}/{len(articles)}: {str(e)}")
                # Continue with next article even if one fails
                summarized_articles.append(article)

        successful = sum(1 for a in summarized_articles if a.get("summary"))
        logger.info(
            f"Summarization complete: {successful}/{len(articles)} "
            "articles summarized"
        )
        return summarized_articles
