"""
RAG Query System Implementation.

Retrieval-Augmented Generation system that accepts natural language queries,
retrieves top-k relevant document chunks from ChromaDB, and generates answers
using retrieved context with Ollama LLM via LangChain.
"""

from typing import List, Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from app.rag.llm_factory import get_llm
from app.rag.embedding_factory import EmbeddingGenerator, EmbeddingError
from app.vector_db import ChromaStore, ChromaStoreError
from app.utils.config import config
from app.utils.logger import get_logger

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
    ):
        """
        Initialize RAG query system.

        Args:
            collection_name: ChromaDB collection name (default: "documents")
            top_k: Number of top chunks to retrieve (default: 5)
            embedding_provider: Embedding provider ('openai' or 'ollama').
                If None, uses config.EMBEDDING_PROVIDER

        Raises:
            RAGQueryError: If initialization fails
        """
        logger.info(f"Initializing RAG query system: collection={collection_name}, top_k={top_k}")
        try:
            self.top_k = top_k
            logger.debug("Creating LLM instance")
            self.llm = get_llm()
            logger.debug(f"Creating embedding generator with provider={embedding_provider or config.EMBEDDING_PROVIDER}")
            self.embedding_generator = EmbeddingGenerator(provider=embedding_provider)
            logger.debug(f"Creating ChromaDB store with collection={collection_name}")
            self.chroma_store = ChromaStore(collection_name=collection_name)

            # Financial domain-optimized prompt template
            self.prompt_template = ChatPromptTemplate.from_template(
                """You are a helpful financial research assistant specializing in 
financial analysis, market research, and investment insights.

Use the following context from financial documents to answer the question. 
If the context doesn't contain enough information to answer the question, 
clearly state that you don't have sufficient information in the provided context.

Context:
{context}

Question: {question}

Provide a clear, accurate answer based on the context provided. If multiple 
sources are referenced, synthesize the information cohesively.

Answer:"""
            )

            # Create RAG chain using LCEL (LangChain Expression Language)
            # Chain: question -> embedding -> retrieval -> format -> prompt -> LLM -> answer
            self.chain = self._build_chain()
            logger.info("RAG query system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG query system: {str(e)}", exc_info=True)
            raise RAGQueryError(f"Failed to initialize RAG query system: {str(e)}") from e

    def _format_docs(self, docs: List[Document]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            docs: List of Document objects from retrieval

        Returns:
            Formatted context string
        """
        if not docs:
            return "No relevant context found."
        return "\n\n".join([f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs])

    def _retrieve_context(self, question: str) -> List[Document]:
        """
        Retrieve relevant context chunks from ChromaDB.

        Args:
            question: User's question

        Returns:
            List of Document objects with retrieved chunks

        Raises:
            RAGQueryError: If retrieval fails
        """
        logger.debug(f"Retrieving context for question: '{question[:50]}...'")
        try:
            # Generate query embedding
            logger.debug("Generating query embedding")
            query_embedding = self.embedding_generator.embed_query(question)

            # Search ChromaDB
            logger.debug(f"Querying ChromaDB with top_k={self.top_k}")
            results = self.chroma_store.query_by_embedding(
                query_embedding=query_embedding,
                n_results=self.top_k,
            )

            # Convert to Document objects
            documents = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, (doc_text, metadata) in enumerate(
                    zip(results["documents"], results["metadatas"])
                ):
                    doc = Document(
                        page_content=doc_text,
                        metadata=metadata or {},
                    )
                    documents.append(doc)

            logger.info(f"Retrieved {len(documents)} context documents")
            return documents

        except EmbeddingError as e:
            logger.error(f"Failed to generate query embedding: {str(e)}", exc_info=True)
            raise RAGQueryError(f"Failed to generate query embedding: {str(e)}") from e
        except ChromaStoreError as e:
            logger.error(f"Failed to retrieve context from ChromaDB: {str(e)}", exc_info=True)
            raise RAGQueryError(f"Failed to retrieve context from ChromaDB: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error during context retrieval: {str(e)}", exc_info=True)
            raise RAGQueryError(f"Unexpected error during context retrieval: {str(e)}") from e

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
    ) -> Dict[str, Any]:
        """
        Process a natural language query and generate an answer.

        Args:
            question: User's natural language question
            top_k: Override default top_k for this query (optional)
            timeout: Query timeout in seconds (optional)

        Returns:
            Dictionary with keys:
                - answer: Generated answer string
                - sources: List of source document metadata
                - chunks_used: Number of chunks used
                - error: Error message if query failed (optional)

        Raises:
            RAGQueryError: If query processing fails
        """
        if not question or not question.strip():
            logger.error("Empty question provided")
            raise RAGQueryError("Question cannot be empty")

        logger.info(f"Processing query: '{question[:50]}...'")
        try:
            # Use provided top_k or default
            current_top_k = top_k if top_k is not None else self.top_k

            # Retrieve context
            if top_k != self.top_k:
                logger.debug(f"Using custom top_k={current_top_k} for this query")
                # Temporarily override top_k
                original_top_k = self.top_k
                self.top_k = current_top_k
                retrieved_docs = self._retrieve_context(question)
                self.top_k = original_top_k
            else:
                retrieved_docs = self._retrieve_context(question)

            # Check if we have any relevant results
            if not retrieved_docs:
                logger.warning("No relevant documents found for query")
                return {
                    "answer": "I couldn't find any relevant information in the document database to answer your question. Please try rephrasing your question or ensure documents have been indexed.",
                    "sources": [],
                    "chunks_used": 0,
                }

            # Format context
            logger.debug("Formatting context documents")
            context = self._format_docs(retrieved_docs)

            # Generate answer using LLM
            logger.debug("Generating answer using LLM")
            try:
                response = self.chain.invoke({"question": question, "context": context})
                answer = response if isinstance(response, str) else str(response)
                logger.info(f"Successfully generated answer ({len(answer)} chars)")
            except Exception as e:
                # Handle LLM failures gracefully
                logger.error(f"LLM generation failed: {str(e)}", exc_info=True)
                return {
                    "answer": f"I encountered an error while generating an answer: {str(e)}. Please try again or check your Ollama configuration.",
                    "sources": [doc.metadata for doc in retrieved_docs],
                    "chunks_used": len(retrieved_docs),
                    "error": f"LLM generation failed: {str(e)}",
                }

            # Extract source metadata
            sources = [doc.metadata for doc in retrieved_docs]

            return {
                "answer": answer,
                "sources": sources,
                "chunks_used": len(retrieved_docs),
            }

        except RAGQueryError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing query: {str(e)}", exc_info=True)
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
) -> RAGQuerySystem:
    """
    Create a RAG query system instance.

    Args:
        collection_name: ChromaDB collection name (default: "documents")
        top_k: Number of top chunks to retrieve (default: 5)
        embedding_provider: Embedding provider ('openai' or 'ollama').
            If None, uses config.EMBEDDING_PROVIDER

    Returns:
        RAGQuerySystem instance
    """
    return RAGQuerySystem(
        collection_name=collection_name,
        top_k=top_k,
        embedding_provider=embedding_provider,
    )

