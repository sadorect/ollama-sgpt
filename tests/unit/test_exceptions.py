"""Unit tests for exceptions module."""

from ollama_sgpt.exceptions import (
    OllamaSGPTError,
    OllamaConnectionError,
    OllamaModelError,
    ConfigError,
    HistoryError,
    SessionError,
)


def test_base_exception():
    """Test base exception."""
    error = OllamaSGPTError("test error")
    assert str(error) == "test error"
    assert isinstance(error, Exception)


def test_connection_error():
    """Test connection error."""
    error = OllamaConnectionError("cannot connect")
    assert str(error) == "cannot connect"
    assert isinstance(error, OllamaSGPTError)


def test_model_error():
    """Test model error."""
    error = OllamaModelError("model not found")
    assert str(error) == "model not found"
    assert isinstance(error, OllamaSGPTError)


def test_config_error():
    """Test config error."""
    error = ConfigError("invalid config")
    assert str(error) == "invalid config"
    assert isinstance(error, OllamaSGPTError)


def test_history_error():
    """Test history error."""
    error = HistoryError("history issue")
    assert str(error) == "history issue"
    assert isinstance(error, OllamaSGPTError)


def test_session_error():
    """Test session error."""
    error = SessionError("session problem")
    assert str(error) == "session problem"
    assert isinstance(error, OllamaSGPTError)
