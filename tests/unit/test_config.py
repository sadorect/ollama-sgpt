"""Unit tests for config module."""

import pytest
import ollama_sgpt.config as config_module
from ollama_sgpt.config import load_config, DEFAULT_CONFIG


def _patch_home(monkeypatch, temp_dir):
    """Patch config module home directory resolution."""
    monkeypatch.setattr(config_module.Path, "home", staticmethod(lambda: temp_dir))


def test_load_default_config(temp_dir, monkeypatch):
    """Test loading default configuration."""
    _patch_home(monkeypatch, temp_dir)
    config = load_config()
    assert config["model"] == DEFAULT_CONFIG["model"]
    assert config["stream"] == DEFAULT_CONFIG["stream"]
    assert config["tools_enabled"] is False


def test_load_custom_config(temp_dir, monkeypatch):
    """Test loading custom configuration from file."""
    _patch_home(monkeypatch, temp_dir)
    config_file = temp_dir / ".ollama_sgpt.yaml"
    config_file.write_text("model: mistral\nstream: false\n")
    
    config = load_config()
    assert config["model"] == "mistral"
    assert config["stream"] is False


def test_config_merge(temp_dir, monkeypatch):
    """Test that custom config merges with defaults."""
    _patch_home(monkeypatch, temp_dir)
    config_file = temp_dir / ".ollama_sgpt.yaml"
    config_file.write_text("model: codellama\n")
    
    config = load_config()
    assert config["model"] == "codellama"
    assert "ollama_url" in config  # From defaults


def test_load_config_handles_empty_file(temp_dir, monkeypatch):
    """An empty config file should fall back to defaults instead of crashing."""
    _patch_home(monkeypatch, temp_dir)
    config_file = temp_dir / ".ollama_sgpt.yaml"
    config_file.write_text("", encoding="utf-8")

    config = load_config()
    assert config["model"] == DEFAULT_CONFIG["model"]
    assert config["shell"] == DEFAULT_CONFIG["shell"]


def test_load_config_rejects_non_mapping_yaml(temp_dir, monkeypatch):
    """Top-level config content must be a YAML mapping."""
    _patch_home(monkeypatch, temp_dir)
    config_file = temp_dir / ".ollama_sgpt.yaml"
    config_file.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_config()


def test_default_shell_is_windows_powershell(monkeypatch):
    """Windows should default to PowerShell."""
    monkeypatch.setattr(config_module.platform, "system", lambda: "Windows")
    assert config_module._default_shell() == "powershell"


def test_default_shell_is_bash_on_unix(monkeypatch):
    """Non-Windows should default to bash."""
    monkeypatch.setattr(config_module.platform, "system", lambda: "Linux")
    assert config_module._default_shell() == "bash"
