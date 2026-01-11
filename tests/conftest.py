"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from unittest.mock import Mock
import tempfile


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Mock configuration."""
    return {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "history_file": str(temp_dir / "history.json"),
        "stream": True,
    }


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    return {
        "message": {"role": "assistant", "content": "Test response"},
        "done": True,
    }


@pytest.fixture
def mock_requests(mocker, mock_ollama_response):
    """Mock requests library."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ollama_response
    mock_response.iter_lines.return_value = [
        b'{"message": {"content": "Test"}, "done": false}',
        b'{"message": {"content": " response"}, "done": true}',
    ]
    
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.__enter__.return_value = mock_response
    return mock_post
