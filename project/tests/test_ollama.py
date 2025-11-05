"""
Pytest tests for Ollama API integration.

Tests Ollama installation and model inference functionality.
"""

from typing import Any, Dict

import pytest
import requests


@pytest.fixture
def ollama_base_url():
    """Ollama API base URL."""
    return "http://localhost:11434"


@pytest.fixture
def ollama_model():
    """Default Ollama model for testing."""
    return "llama3.2"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_ollama_api_accessibility(ollama_base_url):
    """Test Ollama API endpoint accessibility."""
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama not running - skipping Ollama API tests")
    except requests.exceptions.Timeout:
        pytest.skip("Ollama API timeout - skipping Ollama API tests")


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_ollama_model_inference(ollama_base_url, ollama_model):
    """Test Ollama model inference."""
    # Skip if API is not accessible
    try:
        requests.get(f"{ollama_base_url}/api/tags", timeout=5)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip("Ollama not accessible - skipping inference test")

    test_prompt = "What is 2+2? Answer in one sentence."

    response = requests.post(
        f"{ollama_base_url}/api/generate",
        json={"model": ollama_model, "prompt": test_prompt, "stream": False},
        timeout=30,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "response" in data, "Response should contain 'response' field"
    assert len(data["response"]) > 0, "Response should not be empty"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_ollama_model_list(ollama_base_url):
    """Test retrieving list of available Ollama models."""
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "models" in data, "Response should contain 'models' field"
        assert isinstance(data["models"], list), "Models should be a list"
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip("Ollama not accessible - skipping model list test")
