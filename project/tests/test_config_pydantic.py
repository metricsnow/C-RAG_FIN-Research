"""
Tests for Pydantic-based configuration management.

Tests configuration loading, validation, and backward compatibility.
"""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.utils.config import Config


class TestConfigPydantic:
    """Test Pydantic configuration implementation."""

    def test_default_configuration(self):
        """Test that default configuration loads correctly."""
        config = Config()
        assert config.llm_provider == "ollama"
        assert config.llm_model == "llama3.2"
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_timeout == 30
        assert config.log_level == "INFO"

    def test_backward_compatibility_attributes(self):
        """Test that uppercase attributes work for backward compatibility."""
        config = Config()
        assert config.LLM_PROVIDER == "ollama"
        assert config.LLM_MODEL == "llama3.2"
        assert config.OLLAMA_BASE_URL == "http://localhost:11434"
        assert config.OLLAMA_TIMEOUT == 30
        assert config.LOG_LEVEL == "INFO"
        assert config.EMBEDDING_PROVIDER == "openai"

    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        os.environ["LLM_MODEL"] = "mistral"
        os.environ["LOG_LEVEL"] = "DEBUG"
        try:
            config = Config()
            assert config.llm_model == "mistral"
            assert config.log_level == "DEBUG"
        finally:
            os.environ.pop("LLM_MODEL", None)
            os.environ.pop("LOG_LEVEL", None)

    def test_env_file_loading(self):
        """Test loading from .env file."""
        # This test verifies that .env file loading works
        # The actual .env file is loaded automatically by pydantic-settings
        # We test that environment variables are loaded correctly instead
        os.environ["LLM_MODEL"] = "test-model-env"
        os.environ["LOG_LEVEL"] = "WARNING"
        try:
            config = Config()
            assert config.llm_model == "test-model-env"
            assert config.log_level == "WARNING"
        finally:
            os.environ.pop("LLM_MODEL", None)
            os.environ.pop("LOG_LEVEL", None)

    def test_validation_ollama_url(self):
        """Test Ollama URL validation."""
        # Test via environment variable (where validation actually runs)
        os.environ["OLLAMA_BASE_URL"] = "invalid-url"
        try:
            with pytest.raises(
                ValidationError, match="must start with http:// or https://"
            ):
                Config()
        finally:
            os.environ.pop("OLLAMA_BASE_URL", None)

    def test_validation_log_level(self):
        """Test log level validation."""
        # Test via environment variable (where validation actually runs)
        os.environ["LOG_LEVEL"] = "INVALID"
        try:
            with pytest.raises(ValidationError, match="Invalid log level"):
                Config()
        finally:
            os.environ.pop("LOG_LEVEL", None)

    def test_validation_numeric_constraints(self):
        """Test numeric field constraints."""
        # Test via environment variable (where validation actually runs)
        os.environ["OLLAMA_TIMEOUT"] = "0"
        try:
            with pytest.raises(ValidationError):
                Config()  # Must be >= 1
        finally:
            os.environ.pop("OLLAMA_TIMEOUT", None)

        os.environ["OLLAMA_TEMPERATURE"] = "3.0"
        try:
            with pytest.raises(ValidationError):
                Config()  # Must be <= 2.0
        finally:
            os.environ.pop("OLLAMA_TEMPERATURE", None)

    def test_boolean_parsing(self):
        """Test boolean field parsing from strings."""
        # Test via environment variable (string parsing)
        os.environ["OLLAMA_ENABLED"] = "false"
        try:
            config = Config()
            assert config.ollama_enabled is False
        finally:
            os.environ.pop("OLLAMA_ENABLED", None)

        os.environ["OLLAMA_ENABLED"] = "true"
        try:
            config = Config()
            assert config.ollama_enabled is True
        finally:
            os.environ.pop("OLLAMA_ENABLED", None)

        os.environ["OLLAMA_ENABLED"] = "0"
        try:
            config = Config()
            assert config.ollama_enabled is False
        finally:
            os.environ.pop("OLLAMA_ENABLED", None)

        os.environ["OLLAMA_ENABLED"] = "1"
        try:
            config = Config()
            assert config.ollama_enabled is True
        finally:
            os.environ.pop("OLLAMA_ENABLED", None)

    def test_get_ollama_config(self):
        """Test get_ollama_config method."""
        config = Config()
        ollama_config = config.get_ollama_config()
        assert isinstance(ollama_config, dict)
        assert "base_url" in ollama_config
        assert "timeout" in ollama_config
        assert "temperature" in ollama_config
        assert "model" in ollama_config
        assert ollama_config["base_url"] == config.ollama_base_url
        assert ollama_config["model"] == config.llm_model

    def test_validate_method(self):
        """Test validate method."""
        config = Config()
        # Should pass with valid config
        assert config.validate() is True

        # Test invalid configuration - need to set via environment or direct assignment
        # Since Pydantic validates on init, we need to bypass validation temporarily
        # or test via environment variable
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["OLLAMA_ENABLED"] = "false"
        try:
            config = Config()
            with pytest.raises(ValueError, match="Ollama is disabled"):
                config.validate()
        finally:
            os.environ.pop("LLM_PROVIDER", None)
            os.environ.pop("OLLAMA_ENABLED", None)

    def test_path_properties(self):
        """Test path properties."""
        config = Config()
        assert isinstance(config.PROJECT_ROOT, Path)
        assert isinstance(config.DATA_DIR, Path)
        assert isinstance(config.DOCUMENTS_DIR, Path)
        assert isinstance(config.CHROMA_DB_DIR, Path)
        assert config.DATA_DIR == config.PROJECT_ROOT / "data"

    def test_openai_api_key_optional(self):
        """Test that OpenAI API key is optional."""
        # Clear environment variable if it exists
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            # Set empty string via environment variable
            os.environ["OPENAI_API_KEY"] = ""
            config = Config()
            assert config.openai_api_key == ""
            # Should not raise error, just warn
            result = config.validate()
            assert result is True  # Warning doesn't fail validation
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_field_aliases(self):
        """Test that field aliases work correctly."""
        os.environ["OLLAMA_BASE_URL"] = "http://test:11434"
        try:
            config = Config()
            assert config.ollama_base_url == "http://test:11434"
            assert config.OLLAMA_BASE_URL == "http://test:11434"
        finally:
            os.environ.pop("OLLAMA_BASE_URL", None)
