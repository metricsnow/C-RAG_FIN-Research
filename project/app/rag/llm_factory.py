"""
LLM factory module.

Creates and configures LLM instances based on configuration.
"""

import warnings

# Try to use langchain-ollama (recommended), fallback to langchain-community
try:
    from langchain_ollama import OllamaLLM

    OLLAMA_AVAILABLE = True
    OLLAMA_CLASS = OllamaLLM
except ImportError:
    # Fallback to deprecated langchain-community
    from langchain_community.llms import Ollama

    OLLAMA_AVAILABLE = False
    OLLAMA_CLASS = Ollama
    # Suppress deprecation warning for compatibility
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module="langchain_community.llms"
    )

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_ollama_llm():
    """
    Create and configure Ollama LLM instance.

    Returns:
        OllamaLLM or Ollama: Configured Ollama LLM instance
    """
    ollama_config = config.get_ollama_config()
    logger.debug(f"Creating Ollama LLM with config: {ollama_config}")

    if OLLAMA_AVAILABLE:
        # Use langchain-ollama (recommended)
        logger.debug("Using langchain-ollama (recommended)")
        llm = OLLAMA_CLASS(
            base_url=ollama_config["base_url"],
            model=ollama_config["model"],
            temperature=ollama_config["temperature"],
            timeout=ollama_config["timeout"],
        )
    else:
        # Fallback to deprecated langchain-community
        logger.warning("Using deprecated langchain-community (fallback)")
        llm = OLLAMA_CLASS(
            base_url=ollama_config["base_url"],
            model=ollama_config["model"],
            temperature=ollama_config["temperature"],
            timeout=ollama_config["timeout"],
        )

    logger.info(f"Ollama LLM created successfully: model={ollama_config['model']}")
    return llm


def get_llm():
    """
    Get LLM instance based on configured provider.

    Returns:
        LLM instance (Ollama or other)
    """
    logger.debug(f"Getting LLM instance with provider: {config.LLM_PROVIDER}")
    if config.LLM_PROVIDER == "ollama":
        return create_ollama_llm()
    else:
        logger.error(f"Unsupported LLM provider: {config.LLM_PROVIDER}")
        raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")
