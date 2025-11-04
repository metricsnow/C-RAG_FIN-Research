"""
Basic RAG chain implementation.

Simplified RAG chain for learning and testing LangChain integration.
This version does not include vector database - that will be added in Milestone 2.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.llm_factory import get_llm
from app.utils.config import config


class BasicRAGChain:
    """
    Basic RAG chain for processing queries with document context.

    This is a simplified version that works with in-memory documents
    for learning LangChain patterns. Vector database integration will
    be added in Milestone 2.
    """

    def __init__(self):
        """Initialize the RAG chain with LLM and text splitter."""
        self.llm = get_llm()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # Create prompt template for RAG
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful financial research assistant. 
Use the following context to answer the question. If the context doesn't contain 
enough information to answer the question, say so.

Context:
{context}

Question: {question}

Answer:""",
        )

        # Create RAG chain using LCEL (LangChain Expression Language)
        # The prompt template will receive the full input dict
        self.chain = self.prompt_template | self.llm

    def load_document(self, text: str) -> list[str]:
        """
        Load and split a document into chunks.

        Args:
            text: Document text content

        Returns:
            List of text chunks
        """
        chunks = self.text_splitter.split_text(text)
        return chunks

    def process_query(self, question: str, context: str) -> str:
        """
        Process a query with provided context.

        Args:
            question: User's question
            context: Document context to use for answering

        Returns:
            Generated answer from LLM
        """
        try:
            response = self.chain.invoke(
                {"context": context, "question": question}
            )
            # In LangChain 1.0+, LLM returns string directly
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def process_query_with_chunks(
        self, question: str, document_chunks: list[str]
    ) -> str:
        """
        Process a query with multiple document chunks.

        Args:
            question: User's question
            document_chunks: List of document chunks to use as context

        Returns:
            Generated answer from LLM
        """
        # Combine chunks into context (simplified - will use vector search in Milestone 2)
        context = "\n\n".join(document_chunks[:3])  # Use first 3 chunks for now

        return self.process_query(question, context)

