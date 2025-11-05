"""
Retrieval optimization module for RAG system.

Implements hybrid search (semantic + keyword/BM25), reranking,
and multi-stage retrieval for improved answer quality.
"""

from typing import Dict, List, Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.rag.embedding_factory import EmbeddingGenerator
from app.utils.logger import get_logger
from app.vector_db import ChromaStore, ChromaStoreError

logger = get_logger(__name__)


class RetrievalOptimizerError(Exception):
    """Custom exception for retrieval optimization errors."""

    pass


class RetrievalOptimizer:
    """
    Optimized retrieval system with hybrid search and reranking.

    Supports:
    - Hybrid search (semantic + BM25 keyword search)
    - Reciprocal Rank Fusion (RRF) for result merging
    - Cross-encoder reranking for relevance
    - Multi-stage retrieval (broad → refined)
    """

    def __init__(
        self,
        chroma_store: ChromaStore,
        embedding_generator: EmbeddingGenerator,
        use_hybrid_search: bool = True,
        use_reranking: bool = True,
        top_k_initial: int = 20,
        top_k_final: int = 5,
        rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        """
        Initialize retrieval optimizer.

        Args:
            chroma_store: ChromaDB store instance
            embedding_generator: Embedding generator for semantic search
            use_hybrid_search: Enable hybrid search (semantic + BM25)
            use_reranking: Enable reranking with cross-encoder
            top_k_initial: Initial retrieval count (before reranking)
            top_k_final: Final retrieval count (after reranking)
            rerank_model: Reranking model name
        """
        self.chroma_store = chroma_store
        self.embedding_generator = embedding_generator
        self.use_hybrid_search = use_hybrid_search
        self.use_reranking = use_reranking
        self.top_k_initial = top_k_initial
        self.top_k_final = top_k_final

        # Initialize reranker if enabled
        self.reranker: Optional[CrossEncoder] = None
        if self.use_reranking:
            try:
                logger.info(f"Loading reranking model: {rerank_model}")
                self.reranker = CrossEncoder(rerank_model)
                logger.info("Reranking model loaded successfully")
            except Exception as e:
                logger.warning(
                    f"Failed to load reranking model {rerank_model}: {str(e)}. "
                    "Reranking will be disabled."
                )
                self.use_reranking = False
                self.reranker = None

        # BM25 index (built from documents as needed)
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_documents: List[str] = []
        self.bm25_document_map: Dict[str, Document] = {}

        logger.info(
            f"RetrievalOptimizer initialized: hybrid_search={use_hybrid_search}, "
            f"reranking={use_reranking}, top_k_initial={top_k_initial}, "
            f"top_k_final={top_k_final}"
        )

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """
        Retrieve documents using optimized retrieval pipeline.

        Pipeline:
        1. Initial retrieval (semantic or hybrid)
        2. Reranking (if enabled)
        3. Return top-k results

        Args:
            query: User query
            top_k: Override final top_k (optional)

        Returns:
            List of retrieved Document objects

        Raises:
            RetrievalOptimizerError: If retrieval fails
        """
        final_top_k = top_k if top_k is not None else self.top_k_final

        logger.debug(
            f"Optimized retrieval: query='{query[:50]}...', final_top_k={final_top_k}"
        )

        try:
            # Stage 1: Initial retrieval (broad, high recall)
            if self.use_hybrid_search:
                initial_docs = self._hybrid_retrieve(query, self.top_k_initial)
            else:
                initial_docs = self._semantic_retrieve(query, self.top_k_initial)

            if not initial_docs:
                logger.warning("No documents retrieved in initial stage")
                return []

            logger.debug(f"Initial retrieval: {len(initial_docs)} documents")

            # Stage 2: Reranking (high precision)
            if self.use_reranking and self.reranker and len(initial_docs) > final_top_k:
                reranked_docs = self._rerank_documents(query, initial_docs)
                final_docs = reranked_docs[:final_top_k]
                logger.debug(f"After reranking: {len(final_docs)} documents")
            else:
                final_docs = initial_docs[:final_top_k]

            logger.info(f"Retrieved {len(final_docs)} documents for query")
            return final_docs

        except Exception as e:
            logger.error(f"Retrieval optimization failed: {str(e)}", exc_info=True)
            raise RetrievalOptimizerError(
                f"Retrieval optimization failed: {str(e)}"
            ) from e

    def _semantic_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        Semantic retrieval using vector similarity.

        Args:
            query: User query
            top_k: Number of results to retrieve

        Returns:
            List of Document objects
        """
        logger.debug(f"Semantic retrieval: top_k={top_k}")

        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.embed_query(query)

            # Query ChromaDB
            results = self.chroma_store.query_by_embedding(
                query_embedding=query_embedding,
                n_results=top_k,
            )

            # Convert to Document objects
            documents = []
            if results["documents"] and len(results["documents"]) > 0:
                for doc_text, metadata in zip(
                    results["documents"], results["metadatas"]
                ):
                    documents.append(
                        Document(
                            page_content=doc_text,
                            metadata=metadata or {},
                        )
                    )

            return documents

        except ChromaStoreError as e:
            logger.error(f"Semantic retrieval failed: {str(e)}", exc_info=True)
            raise RetrievalOptimizerError(f"Semantic retrieval failed: {str(e)}") from e

    def _build_bm25_index(self) -> None:
        """Build BM25 index from all documents in ChromaDB."""
        if self.bm25_index is not None:
            return  # Index already built

        logger.debug("Building BM25 index from ChromaDB documents")

        try:
            # Get all documents from ChromaDB
            all_docs = self.chroma_store.get_all()

            if not all_docs["documents"]:
                logger.warning("No documents in ChromaDB for BM25 index")
                return

            # Extract texts and metadata
            texts = []
            documents = []
            for doc_text, metadata in zip(all_docs["documents"], all_docs["metadatas"]):
                # Tokenize for BM25 (simple whitespace split)
                tokenized = doc_text.lower().split()
                texts.append(tokenized)
                documents.append(
                    Document(
                        page_content=doc_text,
                        metadata=metadata or {},
                    )
                )

            # Build BM25 index
            self.bm25_index = BM25Okapi(texts)
            self.bm25_documents = all_docs["documents"]
            self.bm25_document_map = dict(enumerate(documents))

            logger.info(f"BM25 index built with {len(texts)} documents")

        except Exception as e:
            logger.error(f"Failed to build BM25 index: {str(e)}", exc_info=True)
            raise RetrievalOptimizerError(
                f"Failed to build BM25 index: {str(e)}"
            ) from e

    def _bm25_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        BM25 keyword-based retrieval.

        Args:
            query: User query
            top_k: Number of results to retrieve

        Returns:
            List of Document objects
        """
        logger.debug(f"BM25 retrieval: top_k={top_k}")

        # Build index if not exists
        if self.bm25_index is None:
            self._build_bm25_index()

        if self.bm25_index is None:
            logger.warning("BM25 index not available, returning empty results")
            return []

        try:
            # Tokenize query
            query_tokens = query.lower().split()

            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)

            # Get top-k document indices
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True,
            )[:top_k]

            # Retrieve documents
            documents = [
                self.bm25_document_map[idx]
                for idx in top_indices
                if idx in self.bm25_document_map
            ]

            logger.debug(f"BM25 retrieved {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"BM25 retrieval failed: {str(e)}", exc_info=True)
            raise RetrievalOptimizerError(f"BM25 retrieval failed: {str(e)}") from e

    def _hybrid_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        Hybrid retrieval combining semantic and BM25 search.

        Uses Reciprocal Rank Fusion (RRF) to merge results.

        Args:
            query: User query
            top_k: Number of results to retrieve

        Returns:
            List of Document objects
        """
        logger.debug(f"Hybrid retrieval: top_k={top_k}")

        try:
            # Retrieve from both methods
            semantic_docs = self._semantic_retrieve(query, top_k)
            bm25_docs = self._bm25_retrieve(query, top_k)

            # Merge using Reciprocal Rank Fusion
            merged_docs = self._reciprocal_rank_fusion(semantic_docs, bm25_docs, top_k)

            logger.debug(
                f"Hybrid retrieval: semantic={len(semantic_docs)}, "
                f"bm25={len(bm25_docs)}, merged={len(merged_docs)}"
            )

            return merged_docs

        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {str(e)}", exc_info=True)
            # Fallback to semantic only
            logger.warning("Falling back to semantic retrieval only")
            return self._semantic_retrieve(query, top_k)

    def _reciprocal_rank_fusion(
        self,
        results1: List[Document],
        results2: List[Document],
        k: int = 60,
    ) -> List[Document]:
        """
        Merge ranked results using Reciprocal Rank Fusion (RRF).

        Args:
            results1: First ranked list of documents
            results2: Second ranked list of documents
            k: RRF constant (default: 60)

        Returns:
            Merged and re-ranked list of documents
        """
        # Create document ID mapping using content + metadata as key
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        def get_doc_key(doc: Document) -> str:
            """Generate unique key for document."""
            meta = doc.metadata or {}
            content_preview = doc.page_content[:100]
            source = meta.get("source", "")
            chunk_idx = meta.get("chunk_index", "")
            return f"{content_preview}_{source}_{chunk_idx}"

        # Score documents from first list
        for rank, doc in enumerate(results1, 1):
            doc_key = get_doc_key(doc)
            doc_map[doc_key] = doc
            doc_scores[doc_key] = doc_scores.get(doc_key, 0.0) + 1.0 / (k + rank)

        # Score documents from second list
        for rank, doc in enumerate(results2, 1):
            doc_key = get_doc_key(doc)
            doc_map[doc_key] = doc
            doc_scores[doc_key] = doc_scores.get(doc_key, 0.0) + 1.0 / (k + rank)

        # Sort by combined score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Return top-k documents
        merged = [doc_map[doc_key] for doc_key, score in sorted_docs[:k]]

        return merged

    def _rerank_documents(
        self, query: str, documents: List[Document]
    ) -> List[Document]:
        """
        Rerank documents using cross-encoder model.

        Args:
            query: User query
            documents: List of documents to rerank

        Returns:
            Reranked list of documents
        """
        if not self.reranker:
            return documents

        logger.debug(f"Reranking {len(documents)} documents")

        try:
            # Prepare query-document pairs for reranking
            pairs = [[query, doc.page_content] for doc in documents]

            # Get reranking scores
            scores = self.reranker.predict(pairs)

            # Sort documents by score
            scored_docs = list(zip(documents, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            # Return reranked documents
            reranked = [doc for doc, score in scored_docs]

            logger.debug(f"Reranking complete: {len(reranked)} documents")
            return reranked

        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}", exc_info=True)
            # Return original documents if reranking fails
            return documents
