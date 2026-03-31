"""Unit tests for ollama_client module."""

import pytest
from ollama_sgpt.ollama_client import (
    check_ollama_health,
    validate_model,
    list_models,
    stream_chat,
)
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


def test_health_check_http_error_raises(mocker):
    """Non-200 health checks should raise a connection error."""
    import requests.exceptions
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("503 Server Error")

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


def test_validate_model_no_models_installed(mocker):
    """An empty model list should produce a first-run setup error."""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {"models": []}
    mock_get.return_value.status_code = 200

    with pytest.raises(OllamaModelError) as exc_info:
        validate_model("http://localhost:11434/api/chat", "llama3")

    assert "No local Ollama models are installed yet" in str(exc_info.value)
    assert "ollama pull llama3" in str(exc_info.value)


def test_validate_model_connection_error(mocker):
    """Test model validation when connection fails."""
    import requests.exceptions
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.RequestException("Connection refused")

    with pytest.raises(OllamaConnectionError):
        validate_model("http://localhost:11434/api/chat", "llama3")


def test_stream_chat_echoes_chunks_to_console(mocker):
    """Streaming chat should print streamed chunks when echo is enabled."""

    class MockStreamResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_lines(self):
            yield b'{"message":{"content":"hello"},"done":false}'
            yield b'{"message":{"content":" world"},"done":true}'

    mock_post = mocker.patch("requests.post", return_value=MockStreamResponse())
    mock_print = mocker.patch("ollama_sgpt.ollama_client.console.print")

    result = stream_chat(
        "http://localhost:11434/api/chat",
        {"model": "llama3", "messages": []},
        echo=True,
    )

    assert result == "hello world"
    mock_post.assert_called_once()
    assert mock_print.call_count == 3
