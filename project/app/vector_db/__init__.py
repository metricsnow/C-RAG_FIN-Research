"""
Vector database integration module.

Handles ChromaDB setup, storage, and retrieval of document embeddings.
"""

from app.vector_db.chroma_store import ChromaStore, ChromaStoreError

__all__ = ["ChromaStore", "ChromaStoreError"]

