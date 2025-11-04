"""
LLM factory module.

Creates and configures LLM instances based on configuration.
"""

import warnings
from langchain_community.llms import Ollama
from app.utils.config import config

# Suppress deprecation warning for now (will migrate to langchain-ollama in future)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community.llms")


def create_ollama_llm() -> Ollama:
    """
    Create and configure Ollama LLM instance.

    Returns:
        Ollama: Configured Ollama LLM instance
    """
    ollama_config = config.get_ollama_config()

    llm = Ollama(
        base_url=ollama_config["base_url"],
        model=ollama_config["model"],
        temperature=ollama_config["temperature"],
        timeout=ollama_config["timeout"],
    )

    return llm


def get_llm():
    """
    Get LLM instance based on configured provider.

    Returns:
        LLM instance (Ollama or other)
    """
    if config.LLM_PROVIDER == "ollama":
        return create_ollama_llm()
    else:
        raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")

