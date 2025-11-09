API Reference
=============

This section contains the automatically generated API documentation for all modules.

.. automodule:: app
   :noindex:

Ingestion Modules
-----------------

.. automodule:: app.ingestion.document_loader
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.edgar_fetcher
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.pipeline
   :members:
   :show-inheritance:

Ingestion Processors
-------------------

The ingestion pipeline uses a modular processor architecture where each data source type has its own specialized processor class.

.. automodule:: app.ingestion.processors.base_processor
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.processors.document_processor
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.processors.stock_processor
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.processors.transcript_processor
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.processors.news_processor
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.processors.economic_data_processor
   :members:
   :show-inheritance:

.. automodule:: app.ingestion.processors.alternative_data_processor
   :members:
   :show-inheritance:

RAG Modules
-----------

.. automodule:: app.rag.chain
   :members:
   :show-inheritance:

.. automodule:: app.rag.embedding_factory
   :members:
   :show-inheritance:

.. automodule:: app.rag.llm_factory
   :members:
   :show-inheritance:

Vector Database Modules
-----------------------

.. automodule:: app.vector_db.chroma_store
   :members:
   :show-inheritance:

UI Modules
----------

.. automodule:: app.ui.app
   :members:
   :show-inheritance:

Utility Modules
---------------

.. automodule:: app.utils.config
   :members:
   :show-inheritance:

.. automodule:: app.utils.logger
   :members:
   :show-inheritance:

.. automodule:: app.utils.document_processors
   :members:
   :show-inheritance:
