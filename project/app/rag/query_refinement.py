"""
Query refinement and enhancement module for RAG optimization.

Implements query rewriting, expansion, and multi-query generation
to improve retrieval accuracy.
"""

import re
from typing import List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryRefinementError(Exception):
    """Custom exception for query refinement errors."""

    pass


class QueryRefiner:
    """
    Query refinement and enhancement for improved retrieval.

    Supports:
    - Query rewriting for better semantic search alignment
    - Financial domain-specific query expansion
    - Multi-query generation for complex questions
    - Query decomposition for compound questions
    """

    # Financial domain terms for query expansion
    FINANCIAL_TERMS = {
        "revenue": ["revenue", "income", "sales", "earnings", "top line"],
        "profit": ["profit", "earnings", "net income", "bottom line", "margin"],
        "assets": ["assets", "balance sheet", "equity", "liabilities"],
        "cash": ["cash", "cash flow", "liquidity", "working capital"],
        "company": ["company", "corporation", "firm", "enterprise", "business"],
        "financial": ["financial", "fiscal", "accounting", "economic"],
        "statement": ["statement", "report", "filing", "document", "form"],
        "quarter": ["quarter", "Q1", "Q2", "Q3", "Q4", "quarterly"],
        "year": ["year", "annual", "fiscal year", "FY"],
    }

    def __init__(self, enable_expansion: bool = True, enable_multi_query: bool = False):
        """
        Initialize query refiner.

        Args:
            enable_expansion: Enable financial domain query expansion
            enable_multi_query: Enable multi-query generation (for complex queries)
        """
        self.enable_expansion = enable_expansion
        self.enable_multi_query = enable_multi_query
        logger.debug(
            f"QueryRefiner initialized: expansion={enable_expansion}, "
            f"multi_query={enable_multi_query}"
        )

    def refine_query(self, query: str, context: Optional[str] = None) -> str:
        """
        Refine a query for better retrieval.

        Applies query rewriting and financial domain expansion.

        Args:
            query: Original user query
            context: Optional context (e.g., conversation history)

        Returns:
            Refined query string
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for refinement")
            return query

        logger.debug(f"Refining query: '{query[:50]}...'")

        # Normalize query
        refined = self._normalize_query(query)

        # Apply financial domain expansion if enabled
        if self.enable_expansion:
            refined = self._expand_financial_terms(refined)

        # Add context if provided
        if context:
            refined = self._add_context_to_query(refined, context)

        logger.debug(f"Refined query: '{refined[:50]}...'")
        return refined

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text.

        Args:
            query: Original query

        Returns:
            Normalized query
        """
        # Remove extra whitespace
        normalized = " ".join(query.split())

        # Fix common typos/abbreviations
        normalized = re.sub(r"\bwhat's\b", "what is", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\bwho's\b", "who is", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\bthat's\b", "that is", normalized, flags=re.IGNORECASE)

        return normalized.strip()

    def _expand_financial_terms(self, query: str) -> str:
        """
        Expand financial domain terms in query.

        Args:
            query: Original query

        Returns:
            Query with expanded financial terms
        """
        query_lower = query.lower()
        expanded_terms = []

        # Check for financial terms and add synonyms
        for term, synonyms in self.FINANCIAL_TERMS.items():
            if term in query_lower:
                # Add synonyms that aren't already in query
                for synonym in synonyms[:2]:  # Limit to 2 synonyms per term
                    if synonym not in query_lower:
                        expanded_terms.append(synonym)

        # Append expanded terms if any found
        if expanded_terms:
            expanded_query = f"{query} {' '.join(expanded_terms)}"
            logger.debug(f"Expanded query with financial terms: {expanded_terms}")
            return expanded_query

        return query

    def _add_context_to_query(self, query: str, context: str) -> str:
        """
        Add context information to query.

        Args:
            query: Original query
            context: Context string (e.g., conversation history)

        Returns:
            Query with context
        """
        # Simple context addition - can be enhanced with LLM-based rewriting
        if len(context) > 200:
            context = context[:200] + "..."
        return f"{query} {context}"

    def generate_multi_queries(self, query: str, max_queries: int = 3) -> List[str]:
        """
        Generate multiple query variations for complex questions.

        Args:
            query: Original query
            max_queries: Maximum number of query variations to generate

        Returns:
            List of query variations
        """
        if not self.enable_multi_query:
            return [query]

        logger.debug(f"Generating multi-queries for: '{query[:50]}...'")

        queries = [query]  # Original query always included

        # Generate variations based on query patterns
        query_lower = query.lower()

        # If query contains "and" or ",", split into sub-queries
        if " and " in query_lower or ", " in query_lower:
            # Split compound queries
            parts = re.split(r"\s+and\s+|\s*,\s*", query, flags=re.IGNORECASE)
            if len(parts) > 1:
                queries.extend(
                    [part.strip() for part in parts if part.strip()][:max_queries]
                )

        # If query is about companies, add SEC filing context
        if any(
            word in query_lower for word in ["company", "companies", "which", "who"]
        ):
            queries.append(f"{query} SEC EDGAR filing financial document")

        # Limit to max_queries
        queries = queries[:max_queries]

        logger.debug(f"Generated {len(queries)} query variations")
        return queries

    def decompose_query(self, query: str) -> List[str]:
        """
        Decompose compound query into sub-queries.

        Args:
            query: Original query

        Returns:
            List of sub-queries
        """
        logger.debug(f"Decomposing query: '{query[:50]}...'")

        # Simple decomposition based on conjunctions
        sub_queries = []

        # Split on common conjunctions
        parts = re.split(r"\s+(and|or|but)\s+", query, flags=re.IGNORECASE)
        if len(parts) > 1:
            # Filter out conjunctions and clean up
            sub_queries = [
                part.strip()
                for part in parts
                if part.strip() and part.lower() not in ["and", "or", "but"]
            ]
        else:
            # Single query, no decomposition needed
            sub_queries = [query]

        logger.debug(f"Decomposed into {len(sub_queries)} sub-queries")
        return sub_queries
