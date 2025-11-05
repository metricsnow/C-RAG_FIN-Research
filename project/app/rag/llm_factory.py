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

# Try to use langchain-openai (recommended), fallback to langchain-community
try:
    from langchain_openai import ChatOpenAI

    OPENAI_AVAILABLE = True
    OPENAI_CLASS = ChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI

        OPENAI_AVAILABLE = True
        OPENAI_CLASS = ChatOpenAI
    except ImportError:
        OPENAI_AVAILABLE = False
        OPENAI_CLASS = None

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


def create_openai_llm(model: str = "gpt-4o-mini", temperature: float = 0.7):
    """
    Create and configure OpenAI LLM instance.

    Args:
        model: OpenAI model name (default: "gpt-4o-mini" - cheapest)
        temperature: Temperature for generation (default: 0.7)

    Returns:
        ChatOpenAI: Configured OpenAI LLM instance

    Raises:
        ValueError: If OpenAI is not available or API key is missing
    """
    if not OPENAI_AVAILABLE:
        raise ValueError(
            "OpenAI LLM not available. Please install langchain-openai "
            "or langchain-community"
        )

    if not config.OPENAI_API_KEY:
        raise ValueError(
            "OpenAI API key not found. Please set OPENAI_API_KEY in .env file"
        )

    logger.debug(f"Creating OpenAI LLM with model={model}, temperature={temperature}")
    try:
        llm = OPENAI_CLASS(
            model=model,
            temperature=temperature,
            openai_api_key=config.OPENAI_API_KEY,
            timeout=30,
            max_retries=3,
        )
        logger.info(f"OpenAI LLM created successfully: model={model}")
        return llm
    except Exception as e:
        logger.error(f"Failed to create OpenAI LLM: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to create OpenAI LLM: {str(e)}") from e


def get_llm(provider: str = None, model: str = None):
    """
    Get LLM instance based on provider.

    Args:
        provider: LLM provider ('ollama' or 'openai'). If None, uses config.LLM_PROVIDER
        model: Model name. If None, uses default for provider

    Returns:
        LLM instance (Ollama or OpenAI)
    """
    if provider is None:
        provider = config.LLM_PROVIDER

    logger.debug(f"Getting LLM instance with provider: {provider}")

    if provider == "ollama":
        return create_ollama_llm()
    elif provider == "openai":
        # Use cheapest model by default (gpt-4o-mini)
        openai_model = model or "gpt-4o-mini"
        return create_openai_llm(
            model=openai_model, temperature=config.OLLAMA_TEMPERATURE
        )
    else:
        logger.error(f"Unsupported LLM provider: {provider}")
        raise ValueError(f"Unsupported LLM provider: {provider}")
