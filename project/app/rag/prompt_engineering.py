"""
Prompt engineering module for optimized RAG prompts.

Implements financial domain-optimized prompts with few-shot examples
and improved context formatting.
"""

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.utils.logger import get_logger

logger = get_logger(__name__)


class PromptEngineer:
    """
    Financial domain-optimized prompt engineering.

    Provides optimized prompt templates for RAG question-answering
    with financial domain specialization.
    """

    def __init__(self, include_few_shot: bool = True):
        """
        Initialize prompt engineer.

        Args:
            include_few_shot: Include few-shot examples in prompts
        """
        self.include_few_shot = include_few_shot
        logger.debug(f"PromptEngineer initialized: few_shot={include_few_shot}")

    def get_optimized_prompt(self) -> ChatPromptTemplate:
        """
        Get optimized prompt template for financial RAG.

        Returns:
            Optimized ChatPromptTemplate
        """
        prompt_text = self._build_prompt_text()
        return ChatPromptTemplate.from_template(prompt_text)

    def _build_prompt_text(self) -> str:
        """
        Build optimized prompt text.

        Returns:
            Prompt template string
        """
        prompt = (
            "You are an expert financial research assistant specializing in "
            "financial analysis, market research, and investment insights.\n\n"
            "Your task is to answer questions based ONLY on the provided "
            "context from financial documents. Each document includes source "
            "information in the format:\n"
            "[Document N - Company: Company Name (TICKER), Form: FORM_TYPE]\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "1. Answer based ONLY on the provided context - do not use "
            "external knowledge\n"
            "2. If the context doesn't contain enough information, clearly "
            "state that\n"
            "3. Cite specific documents when possible using the "
            "[Document N] format\n"
            "4. Use accurate financial terminology\n"
            "5. Be precise and factual - avoid speculation\n"
            "6. When listing companies, extract ALL unique companies from "
            "document headers\n"
            '7. Use the format "Company Name (TICKER)" for each company\n'
            "8. List all companies found, not just a subset"
        )

        if self.include_few_shot:
            prompt += (
                "\n\nFEW-SHOT EXAMPLES:\n\n"
                "Example 1:\n"
                "Context:\n"
                "[Document 1 - Company: Apple Inc. (AAPL), Form: 10-K]\n"
                "Revenue for fiscal year 2023 was $394.3 billion.\n\n"
                "Question: What was Apple's revenue in 2023?\n"
                "Answer: According to Document 1, Apple Inc. (AAPL) reported "
                "revenue of $394.3 billion for fiscal year 2023.\n\n"
                "Example 2:\n"
                "Context:\n"
                "[Document 1 - Company: Microsoft Corporation (MSFT), "
                "Form: 10-K]\n"
                "[Document 2 - Company: Apple Inc. (AAPL), Form: 10-K]\n\n"
                "Question: Which companies have 10-K filings?\n"
                "Answer: Based on the provided documents, the following "
                "companies have 10-K filings:\n"
                "- Microsoft Corporation (MSFT)\n"
                "- Apple Inc. (AAPL)\n\n"
                "Example 3:\n"
                "Context:\n"
                "[Document 1 - Company: Apple Inc. (AAPL), Form: 10-K]\n"
                "The document discusses product development and innovation.\n\n"
                "Question: What is the weather today?\n"
                "Answer: I cannot answer this question as the provided context "
                "does not contain information about current weather conditions."
            )

        prompt += (
            "\n\nContext:\n{context}\n\n"
            "Question: {question}\n\n"
            "Provide a clear, accurate answer based on the context. When "
            "listing companies, extract ALL unique companies from the "
            'document headers. Use the format "Company Name (TICKER)" for '
            "each company. List all companies found, not just a subset.\n\n"
            "Answer:"
        )

        return prompt

    def format_context_enhanced(
        self, documents: list, max_length: Optional[int] = None
    ) -> str:
        """
        Format context with enhanced structure information.

        Args:
            documents: List of Document objects
            max_length: Maximum context length (optional)

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant context found."

        formatted_parts = []
        for i, doc in enumerate(documents, 1):
            # Extract metadata
            meta = doc.metadata or {}
            ticker = meta.get("ticker", "")
            company_name = meta.get("company_name", "")
            form_type = meta.get("form_type", "")
            section = meta.get("section", "")
            chunk_index = meta.get("chunk_index", "")

            # Build source identifier
            source_info = []
            if company_name:
                source_info.append(f"Company: {company_name}")
            elif ticker:
                source_info.append(f"Company: {ticker}")

            if ticker and company_name:
                source_info[-1] = f"Company: {company_name} ({ticker})"

            if form_type:
                source_info.append(f"Form: {form_type}")

            if section:
                source_info.append(f"Section: {section}")

            if chunk_index is not None:
                source_info.append(f"Chunk: {chunk_index}")

            # Format document with enhanced structure
            source_header = (
                f"[Document {i}"
                + (f" - {', '.join(source_info)}" if source_info else "")
                + "]"
            )

            # Add section heading if available
            content = doc.page_content
            if section:
                content = f"Section: {section}\n{content}"

            formatted_parts.append(f"{source_header}\n{content}")

        context = "\n\n".join(formatted_parts)

        # Apply length limit if specified
        if max_length and len(context) > max_length:
            context = context[:max_length] + "..."
            logger.warning(f"Context truncated to {max_length} characters")

        return context
