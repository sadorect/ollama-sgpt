"""Unit tests for ollama_client module."""

import pytest
from ollama_sgpt.ollama_client import check_ollama_health, validate_model, list_models
from ollama_sgpt.exceptions import OllamaConnectionError, OllamaModelError


def test_health_check_success(mocker):
    """Test successful health check."""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    
    result = check_ollama_health("http://localhost:11434/api/chat")
    assert result is True


def test_health_check_failure(mocker):
    """Test health check failure."""
    import requests.exceptions
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.RequestException("Connection refused")
    
    with pytest.raises(OllamaConnectionError):
        check_ollama_health("http://localhost:11434/api/chat")


def test_list_models_success(mocker):
    """Test listing models successfully."""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {
        "models": [{"name": "llama3"}, {"name": "mistral"}]
    }
    mock_get.return_value.status_code = 200
    
    models = list_models("http://localhost:11434/api/chat")
    assert len(models) == 2
    assert models[0]["name"] == "llama3"


def test_validate_model_exists(mocker):
    """Test model validation when model exists."""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {
        "models": [{"name": "llama3"}, {"name": "mistral"}]
    }
    mock_get.return_value.status_code = 200
    
    result = validate_model("http://localhost:11434/api/chat", "llama3")
    assert result is True


def test_validate_model_not_found(mocker):
    """Test model validation when model doesn't exist."""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {
        "models": [{"name": "llama3"}]
    }
    mock_get.return_value.status_code = 200
    
    with pytest.raises(OllamaModelError):
        validate_model("http://localhost:11434/api/chat", "nonexistent")


def test_validate_model_connection_error(mocker):
    """Test model validation when connection fails."""
    import requests.exceptions
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.RequestException("Connection refused")
    
    # Should not raise exception, just print warning and return True
    result = validate_model("http://localhost:11434/api/chat", "llama3")
    assert result is True
