"""
RAG Query System Implementation.

Retrieval-Augmented Generation system that accepts natural language queries,
retrieves top-k relevant document chunks from ChromaDB, and generates answers
using retrieved context with Ollama LLM via LangChain.
"""

from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.rag.embedding_factory import EmbeddingError, EmbeddingGenerator
from app.rag.filter_builder import FilterBuilder
from app.rag.llm_factory import get_llm
from app.rag.prompt_engineering import PromptEngineer
from app.rag.query_parser import QueryParseError, QueryParser
from app.rag.query_refinement import QueryRefiner
from app.rag.retrieval_optimizer import RetrievalOptimizer, RetrievalOptimizerError
from app.utils.config import config
from app.utils.conversation_memory import get_conversation_context
from app.utils.langchain_memory import ConversationBufferMemory
from app.utils.logger import get_logger
from app.utils.metrics import (
    rag_context_chunks_retrieved,
    rag_queries_total,
    rag_query_duration_seconds,
    track_duration,
    track_error,
    track_success,
)
from app.vector_db import ChromaStore, ChromaStoreError

logger = get_logger(__name__)


class RAGQueryError(Exception):
    """Custom exception for RAG query system errors."""

    pass


class RAGQuerySystem:
    """
    RAG Query System for processing natural language queries.

    Implements full RAG pipeline:
    1. Query embedding generation
    2. Vector similarity search in ChromaDB
    3. Context retrieval (top-k chunks)
    4. Prompt construction with context
    5. LLM answer generation (Ollama)
    """

    def __init__(
        self,
        collection_name: str = "documents",
        top_k: int = 5,
        embedding_provider: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        memory: Optional[ConversationBufferMemory] = None,
    ):
        """
        Initialize RAG query system.

        Args:
            collection_name: ChromaDB collection name (default: "documents")
            top_k: Number of top chunks to retrieve (default: 5)
            embedding_provider: Embedding provider ('openai' or 'ollama').
                If None, uses config.EMBEDDING_PROVIDER
            llm_provider: LLM provider ('ollama' or 'openai').
                If None, uses config.LLM_PROVIDER
            llm_model: LLM model name. If None, uses default for provider
            memory: Optional ConversationBufferMemory instance for conversation
                history management. If None and LangChain memory is enabled,
                creates a new instance.

        Raises:
            RAGQueryError: If initialization fails
        """
        logger.info(
            f"Initializing RAG query system: "
            f"collection={collection_name}, top_k={top_k}"
        )
        try:
            self.top_k = top_k
            provider = llm_provider or config.LLM_PROVIDER
            logger.debug(f"Creating LLM instance with provider={provider}")
            self.llm = get_llm(provider=llm_provider, model=llm_model)
            emb_provider = embedding_provider or config.EMBEDDING_PROVIDER
            logger.debug(f"Creating embedding generator with provider={emb_provider}")
            self.embedding_generator = EmbeddingGenerator(provider=embedding_provider)
            logger.debug(f"Creating ChromaDB store with collection={collection_name}")
            self.chroma_store = ChromaStore(collection_name=collection_name)

            # Initialize optimization components
            self.query_refiner = QueryRefiner(
                enable_expansion=config.rag_query_expansion,
                enable_multi_query=False,  # Can be enabled later if needed
            )
            self.prompt_engineer = PromptEngineer(
                include_few_shot=config.rag_few_shot_examples
            )

            # Initialize advanced query features
            self.query_parser = QueryParser()
            self.filter_builder = FilterBuilder()

            # Initialize retrieval optimizer if optimizations are enabled
            self.use_optimizations = (
                config.rag_use_hybrid_search or config.rag_use_reranking
            )
            if self.use_optimizations:
                logger.info("Initializing RAG optimizations")
                self.retrieval_optimizer = RetrievalOptimizer(
                    chroma_store=self.chroma_store,
                    embedding_generator=self.embedding_generator,
                    use_hybrid_search=config.rag_use_hybrid_search,
                    use_reranking=config.rag_use_reranking,
                    top_k_initial=config.rag_top_k_initial,
                    top_k_final=self.top_k,
                    rerank_model=config.rag_rerank_model,
                )
            else:
                self.retrieval_optimizer = None
                logger.info("RAG optimizations disabled, using basic retrieval")

            # Financial domain-optimized prompt template
            try:
                self.prompt_template = self.prompt_engineer.get_optimized_prompt()
            except Exception as e:
                logger.warning(
                    f"Failed to load optimized prompt, using fallback: {str(e)}"
                )
                # Fallback to original template
                self.prompt_template = ChatPromptTemplate.from_template(
                    """You are a helpful financial research assistant specializing in
financial analysis, market research, and investment insights.

Use the following context from financial documents to answer the question.
Each document includes source information in the format:
[Document N - Company: Company Name (TICKER), Form: FORM_TYPE]

IMPORTANT: When answering questions about which companies have specific documents:
1. Look at the document headers (the [Document N - Company: ...] lines)
2. Extract ALL unique company names and ticker symbols from these headers
3. List ALL companies found, not just one or two
4. Use the company names from the headers
   (e.g., "Apple Inc. (AAPL)", "Microsoft Corporation (MSFT)")
5. Do NOT try to parse document content to find company names
   - use the headers only
6. If multiple documents from the same company are found,
   list the company only once

If the context doesn't contain enough information to answer the question,
clearly state that you don't have sufficient information in the provided context.

{conversation_history}

Context:
{context}

Question: {question}

Provide a clear, accurate answer. When listing companies,
extract ALL unique companies from the document headers.
Use the format "Company Name (TICKER)" for each company.
List all companies found, not just a subset.

Answer:"""
                )

            # Initialize LangChain memory if enabled
            if config.conversation_use_langchain_memory:
                if memory is None:
                    from app.utils.langchain_memory import StreamlitChatMessageHistory

                    # Create empty memory (will be populated from conversation_history)
                    chat_history = StreamlitChatMessageHistory()
                    self.memory = ConversationBufferMemory(
                        chat_memory=chat_history,
                        max_token_limit=config.conversation_max_tokens,
                        max_history=config.conversation_max_history,
                    )
                else:
                    self.memory = memory
                logger.info("LangChain memory initialized")
            else:
                self.memory = None
                logger.info(
                    "LangChain memory disabled, using legacy conversation memory"
                )

            # Create RAG chain using LCEL (LangChain Expression Language)
            # Chain: question -> embedding -> retrieval -> format ->
            # prompt -> LLM -> answer
            self.chain = self._build_chain()
            logger.info("RAG query system initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize RAG query system: {str(e)}", exc_info=True
            )
            raise RAGQueryError(
                f"Failed to initialize RAG query system: {str(e)}"
            ) from e

    def _format_docs(self, docs: List[Document]) -> str:
        """
        Format retrieved documents into context string with metadata.

        Uses enhanced formatting from prompt engineer if available.

        Args:
            docs: List of Document objects from retrieval

        Returns:
            Formatted context string with source information
        """
        if not docs:
            return "No relevant context found."

        # Use enhanced formatting if prompt engineer is available
        try:
            if hasattr(self, "prompt_engineer") and self.prompt_engineer:
                return self.prompt_engineer.format_context_enhanced(docs)
        except Exception as e:
            logger.warning(f"Enhanced formatting failed, using basic: {str(e)}")

        # Fallback to basic formatting
        formatted_parts = []
        for i, doc in enumerate(docs, 1):
            # Extract metadata
            meta = doc.metadata or {}
            ticker = meta.get("ticker", "")
            company_name = meta.get("company_name", "")
            filename = meta.get("filename", "")
            source = meta.get("source", "")
            form_type = meta.get("form_type", "")

            # Build source identifier
            source_info = []
            if company_name:
                source_info.append(f"Company: {company_name}")
            elif ticker:
                # Map ticker to company name for better readability
                ticker_to_company = {
                    "AAPL": "Apple Inc.",
                    "MSFT": "Microsoft Corporation",
                    "GOOGL": "Alphabet Inc.",
                    "AMZN": "Amazon.com Inc.",
                    "META": "Meta Platforms Inc.",
                    "TSLA": "Tesla, Inc.",
                    "NVDA": "NVIDIA Corporation",
                    "JPM": "JPMorgan Chase & Co.",
                    "V": "Visa Inc.",
                    "JNJ": "Johnson & Johnson",
                }
                company = ticker_to_company.get(ticker, ticker)
                source_info.append(f"Company: {company} ({ticker})")
            elif filename:
                source_info.append(f"Source: {filename}")
            elif source:
                source_info.append(f"Source: {source}")

            if form_type:
                source_info.append(f"Form: {form_type}")

            # Format document with source info
            source_header = (
                f"[Document {i}"
                + (f" - {', '.join(source_info)}" if source_info else "")
                + "]"
            )
            formatted_parts.append(f"{source_header}\n{doc.page_content}")

        return "\n\n".join(formatted_parts)

    def _retrieve_context(
        self,
        question: str,
        sentiment_filter: Optional[str] = None,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Retrieve relevant context chunks from ChromaDB.

        Uses optimized retrieval if available, otherwise falls back to basic retrieval.

        Args:
            question: User's question
            sentiment_filter: Optional sentiment filter
                ('positive', 'negative', 'neutral').
                If provided, only retrieves documents with matching sentiment.
            where_filter: Optional ChromaDB where clause dictionary for
                metadata filtering. If provided, will be combined with
                sentiment filter.

        Returns:
            List of Document objects with retrieved chunks

        Raises:
            RAGQueryError: If retrieval fails
        """
        logger.debug(
            f"Retrieving context for question: '{question[:50]}...'"
            + (f" (sentiment_filter={sentiment_filter})" if sentiment_filter else "")
            + (f" (where_filter={where_filter})" if where_filter else "")
        )

        # Build combined where filter
        combined_where_filter = where_filter.copy() if where_filter else {}
        if sentiment_filter:
            combined_where_filter["sentiment"] = sentiment_filter
            logger.debug(f"Applying sentiment filter: {sentiment_filter}")

        # Use combined filter (or None if empty)
        final_where_filter = combined_where_filter if combined_where_filter else None

        # Use optimized retrieval if available
        if self.use_optimizations and self.retrieval_optimizer:
            try:
                # Refine query first
                refined_query = self.query_refiner.refine_query(question)
                logger.debug(f"Refined query: '{refined_query[:50]}...'")

                # Use optimized retrieval
                documents = self.retrieval_optimizer.retrieve(
                    refined_query, top_k=self.top_k
                )
                logger.info(
                    f"Retrieved {len(documents)} documents using optimized retrieval"
                )
                return documents

            except RetrievalOptimizerError as e:
                logger.warning(
                    f"Optimized retrieval failed, falling back to basic: {str(e)}"
                )
                # Fall through to basic retrieval
            except Exception as e:
                logger.warning(f"Unexpected error in optimized retrieval: {str(e)}")
                # Fall through to basic retrieval

        # Fallback to basic retrieval
        try:
            # Refine query for better retrieval
            refined_query = self.query_refiner.refine_query(question)
            question_lower = refined_query.lower()
            enhanced_question = refined_query

            # If question is about companies, add SEC filing context
            if any(
                word in question_lower
                for word in [
                    "company",
                    "companies",
                    "which",
                    "who",
                    "balance sheet",
                    "financial statement",
                ]
            ):
                enhanced_question = (
                    f"{refined_query} SEC EDGAR filing financial document"
                )

            # Generate query embedding
            logger.debug("Generating query embedding")
            query_embedding = self.embedding_generator.embed_query(enhanced_question)

            # Search ChromaDB - retrieve more results to find SEC EDGAR docs
            retrieval_count = min(self.top_k * 3, 30)
            logger.debug(
                f"Querying ChromaDB: retrieval_count={retrieval_count}, "
                f"top_k={self.top_k}"
            )
            results = self.chroma_store.query_by_embedding(
                query_embedding=query_embedding,
                n_results=retrieval_count,
                where=final_where_filter,
            )

            # Convert to Document objects and prioritize SEC EDGAR documents
            documents = []
            edgar_docs = []
            other_docs = []

            if results["documents"] and len(results["documents"]) > 0:
                for doc_text, metadata in zip(
                    results["documents"], results["metadatas"]
                ):
                    doc = Document(
                        page_content=doc_text,
                        metadata=metadata or {},
                    )
                    # Prioritize SEC EDGAR filings (they have ticker metadata)
                    if metadata.get("type") == "edgar_filing" or metadata.get("ticker"):
                        edgar_docs.append(doc)
                    else:
                        other_docs.append(doc)

            # Combine: SEC EDGAR docs first, then others, limit to top_k
            documents = (
                edgar_docs[: self.top_k]
                + other_docs[: max(0, self.top_k - len(edgar_docs))]
            )
            documents = documents[: self.top_k]  # Ensure we don't exceed top_k

            logger.info(
                f"Retrieved {len(documents)} context documents "
                f"({len(edgar_docs)} SEC EDGAR, {len(other_docs)} others)"
            )
            return documents

        except EmbeddingError as e:
            logger.error(f"Failed to generate query embedding: {str(e)}", exc_info=True)
            raise RAGQueryError(f"Failed to generate query embedding: {str(e)}") from e
        except ChromaStoreError as e:
            logger.error(
                f"Failed to retrieve context from ChromaDB: {str(e)}", exc_info=True
            )
            raise RAGQueryError(
                f"Failed to retrieve context from ChromaDB: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error during context retrieval: {str(e)}", exc_info=True
            )
            raise RAGQueryError(
                f"Unexpected error during context retrieval: {str(e)}"
            ) from e

    def _build_chain(self):
        """
        Build RAG chain using LangChain Expression Language.

        Returns:
            Configured RAG chain
        """

        # Build chain using RunnablePassthrough.assign for context retrieval
        # The lambda captures self to access retrieval methods
        def format_context(x: Dict[str, Any]) -> str:
            """Retrieve and format context for the question."""
            question = x["question"]
            docs = self._retrieve_context(question)
            return self._format_docs(docs)

        chain = (
            RunnablePassthrough.assign(context=format_context)
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )

        return chain

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        timeout: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        sentiment_filter: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        enable_query_parsing: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a natural language query and generate an answer.

        Args:
            question: User's natural language question
            top_k: Override default top_k for this query (optional)
            timeout: Query timeout in seconds (optional)
            conversation_history: List of previous conversation messages (optional).
                Each message should be a dict with 'role' and 'content' keys.
            sentiment_filter: Optional sentiment filter
                ('positive', 'negative', 'neutral').
                If provided, only retrieves documents with matching sentiment.
            filters: Optional filter specifications dictionary with keys:
                - date_from: Start date (ISO format string)
                - date_to: End date (ISO format string)
                - document_type: Document type filter
                - ticker: Ticker symbol filter
                - form_type: Form type filter (e.g., "10-K", "10-Q")
                - source: Source identifier filter
                - metadata: Custom metadata filters
            enable_query_parsing: Whether to parse query for filters and
                Boolean operators

        Returns:
            Dictionary with keys:
                - answer: Generated answer string
                - sources: List of source document metadata
                - chunks_used: Number of chunks used
                - error: Error message if query failed (optional)
                - parsed_query: Parsed query information (if parsing enabled)

        Raises:
            RAGQueryError: If query processing fails
        """
        if not question or not question.strip():
            logger.error("Empty question provided")
            raise RAGQueryError("Question cannot be empty")

        logger.info(f"Processing query: '{question[:50]}...'")
        try:
            # Parse query and extract filters if enabled
            parsed_query_info = None
            where_filter = None

            if enable_query_parsing:
                try:
                    parsed = self.query_parser.parse(question, extract_filters=True)
                    parsed_query_info = parsed
                    question = parsed["query_text"]  # Use cleaned query text

                    # Build where clause from extracted filters
                    if parsed["filters"]:
                        where_filter = self.filter_builder.build_where_clause(
                            parsed["filters"]
                        )
                        logger.debug(f"Extracted filters: {parsed['filters']}")

                except QueryParseError as e:
                    logger.warning(
                        f"Query parsing failed, using original query: {str(e)}"
                    )
                    # Continue with original query if parsing fails

            # Apply explicit filters if provided
            if filters:
                explicit_where = self.filter_builder.build_where_clause(filters)
                if explicit_where:
                    # Combine with parsed filters
                    if where_filter:
                        # Combine filters using $and
                        where_filter = {"$and": [where_filter, explicit_where]}
                    else:
                        where_filter = explicit_where
                    logger.debug(f"Applied explicit filters: {filters}")
            # Use provided top_k or default
            current_top_k = top_k if top_k is not None else self.top_k

            # Track query duration
            with track_duration(
                rag_query_duration_seconds,
                {"provider": self.embedding_generator.provider},
            ):
                # Retrieve context
                if top_k != self.top_k:
                    logger.debug(f"Using custom top_k={current_top_k} for this query")
                    # Temporarily override top_k
                    original_top_k = self.top_k
                    self.top_k = current_top_k
                    retrieved_docs = self._retrieve_context(
                        question,
                        sentiment_filter=sentiment_filter,
                        where_filter=where_filter,
                    )
                    self.top_k = original_top_k
                else:
                    retrieved_docs = self._retrieve_context(
                        question,
                        sentiment_filter=sentiment_filter,
                        where_filter=where_filter,
                    )

            # Track chunks retrieved
            rag_context_chunks_retrieved.observe(len(retrieved_docs))

            # Check if we have any relevant results
            if not retrieved_docs:
                logger.warning("No relevant documents found for query")
                track_success(rag_queries_total)
                result = {
                    "answer": (
                        "I couldn't find any relevant information in the "
                        "document database to answer your question. Please try "
                        "rephrasing your question or ensure documents have "
                        "been indexed."
                    ),
                    "sources": [],
                    "chunks_used": 0,
                }
                if parsed_query_info:
                    result["parsed_query"] = parsed_query_info
                return result

            # Format context
            logger.debug("Formatting context documents")
            context = self._format_docs(retrieved_docs)

            # Get conversation context - use LangChain memory if enabled
            conversation_context = None
            conversation_history_str = ""

            if config.conversation_use_langchain_memory and self.memory:
                # Use LangChain memory
                if conversation_history:
                    # Load conversation history into memory
                    from app.utils.langchain_memory import StreamlitChatMessageHistory

                    chat_history = StreamlitChatMessageHistory(
                        messages=conversation_history
                    )
                    self.memory.chat_memory = chat_history

                # Load memory variables
                memory_vars = self.memory.load_memory_variables({})
                if isinstance(memory_vars.get("history"), str):
                    conversation_history_str = memory_vars.get("history", "")
                    if conversation_history_str:
                        conversation_history_str = (
                            f"Previous conversation:\n{conversation_history_str}\n\n"
                        )
                elif memory_vars.get("history"):
                    # If it's a list of messages, format them
                    history_msgs = memory_vars.get("history", [])
                    if history_msgs:
                        formatted = []
                        for msg in history_msgs:
                            if hasattr(msg, "content"):
                                role = (
                                    "User"
                                    if hasattr(msg, "__class__")
                                    and "Human" in str(type(msg))
                                    else "Assistant"
                                )
                                formatted.append(f"{role}: {msg.content}")
                        conversation_history_str = (
                            "Previous conversation:\n" + "\n".join(formatted) + "\n\n"
                        )

                logger.debug(
                    f"Using LangChain memory: "
                    f"{len(self.memory.chat_memory.messages)} messages"
                )
            elif conversation_history:
                # Fallback to legacy conversation memory
                conversation_context = get_conversation_context(
                    messages=conversation_history,
                    current_question=question,
                    enabled=config.conversation_enabled,
                )
                if conversation_context:
                    conversation_history_str = conversation_context + "\n\n"
                    logger.debug(
                        f"Including conversation context "
                        f"({len(conversation_context)} chars)"
                    )
                else:
                    logger.debug("No conversation context to include")

            # Generate answer using LLM
            logger.debug("Generating answer using LLM")
            try:
                response = self.chain.invoke(
                    {
                        "question": question,
                        "context": context,
                        "conversation_history": conversation_history_str,
                    }
                )
                answer = response if isinstance(response, str) else str(response)
                logger.info(f"Successfully generated answer ({len(answer)} chars)")

                # Save to LangChain memory if enabled
                if config.conversation_use_langchain_memory and self.memory:
                    self.memory.save_context(
                        inputs={"input": question}, outputs={"output": answer}
                    )
                    logger.debug("Saved conversation to LangChain memory")
            except Exception as e:
                # Handle LLM failures gracefully
                logger.error(f"LLM generation failed: {str(e)}", exc_info=True)
                result = {
                    "answer": (
                        f"I encountered an error while generating an answer: "
                        f"{str(e)}. Please try again or check your LLM "
                        f"configuration."
                    ),
                    "sources": [doc.metadata for doc in retrieved_docs],
                    "chunks_used": len(retrieved_docs),
                    "error": f"LLM generation failed: {str(e)}",
                }
                if parsed_query_info:
                    result["parsed_query"] = parsed_query_info
                return result

            # Extract source metadata
            sources = [doc.metadata for doc in retrieved_docs]

            # Track successful query
            track_success(rag_queries_total)

            result = {
                "answer": answer,
                "sources": sources,
                "chunks_used": len(retrieved_docs),
            }
            if parsed_query_info:
                result["parsed_query"] = parsed_query_info
            return result

        except RAGQueryError:
            track_error(rag_queries_total)
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing query: {str(e)}", exc_info=True)
            track_error(rag_queries_total)
            raise RAGQueryError(f"Unexpected error processing query: {str(e)}") from e

    def query_simple(self, question: str) -> str:
        """
        Simple query interface that returns only the answer string.

        Args:
            question: User's natural language question

        Returns:
            Generated answer string

        Raises:
            RAGQueryError: If query processing fails
        """
        result = self.query(question)
        return result["answer"]


def create_rag_system(
    collection_name: str = "documents",
    top_k: int = 5,
    embedding_provider: Optional[str] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> RAGQuerySystem:
    """
    Create a RAG query system instance.

    Args:
        collection_name: ChromaDB collection name (default: "documents")
        top_k: Number of top chunks to retrieve (default: 5)
        embedding_provider: Embedding provider ('openai' or 'ollama').
            If None, uses config.EMBEDDING_PROVIDER
        llm_provider: LLM provider ('ollama' or 'openai').
            If None, uses config.LLM_PROVIDER
        llm_model: LLM model name. If None, uses default for provider

    Returns:
        RAGQuerySystem instance
    """
    return RAGQuerySystem(
        collection_name=collection_name,
        top_k=top_k,
        embedding_provider=embedding_provider,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
