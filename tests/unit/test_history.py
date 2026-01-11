"""Unit tests for history module."""

import pytest
from ollama_sgpt.history import load_history, save_history


def test_load_nonexistent_history(temp_dir):
    """Test loading history when file doesn't exist."""
    history_file = temp_dir / "history.json"
    history = load_history(str(history_file))
    assert history == []


def test_save_and_load_history(temp_dir):
    """Test saving and loading history."""
    history_file = temp_dir / "history.json"
    test_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    
    save_history(str(history_file), test_history)
    loaded = load_history(str(history_file))
    
    assert loaded == test_history


def test_history_persistence(temp_dir):
    """Test that history persists across sessions."""
    history_file = temp_dir / "history.json"
    
    # First session
    history1 = [{"role": "user", "content": "First message"}]
    save_history(str(history_file), history1)
    
    # Second session
    loaded = load_history(str(history_file))
    loaded.append({"role": "user", "content": "Second message"})
    save_history(str(history_file), loaded)
    
    # Verify
    final = load_history(str(history_file))
    assert len(final) == 2
    assert final[0]["content"] == "First message"
    assert final[1]["content"] == "Second message"
