"""Unit tests for config module."""

import pytest
from pathlib import Path
from ollama_sgpt.config import load_config, DEFAULT_CONFIG


def test_load_default_config(temp_dir, monkeypatch):
    """Test loading default configuration."""
    monkeypatch.setenv("HOME", str(temp_dir))
    config = load_config()
    assert config["model"] == DEFAULT_CONFIG["model"]
    assert config["stream"] == DEFAULT_CONFIG["stream"]


def test_load_custom_config(temp_dir, monkeypatch):
    """Test loading custom configuration from file."""
    monkeypatch.setenv("HOME", str(temp_dir))
    config_file = temp_dir / ".ollama_sgpt.yaml"
    config_file.write_text("model: mistral\nstream: false\n")
    
    config = load_config()
    assert config["model"] == "mistral"
    assert config["stream"] is False


def test_config_merge(temp_dir, monkeypatch):
    """Test that custom config merges with defaults."""
    monkeypatch.setenv("HOME", str(temp_dir))
    config_file = temp_dir / ".ollama_sgpt.yaml"
    config_file.write_text("model: codellama\n")
    
    config = load_config()
    assert config["model"] == "codellama"
    assert "ollama_url" in config  # From defaults
