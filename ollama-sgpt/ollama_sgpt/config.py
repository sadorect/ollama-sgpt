from pathlib import Path
import platform
import yaml


def _default_shell() -> str:
    if platform.system().lower() == "windows":
        return "powershell"
    return "bash"

DEFAULT_CONFIG = {
    "model": "llama3",
    "ollama_url": "http://localhost:11434/api/chat",
    "history_file": str(Path.home() / ".ollama_sgpt_history.json"),
    "stream": True,
    "shell": _default_shell(),
    "tools_enabled": False,
    "default_session": None,
    "request_timeout": 120,
    "stream_idle_timeout": 60
}


def _config_path() -> Path:
    """Return the canonical user config path."""
    return Path.home() / ".ollama_sgpt.yaml"


def _read_user_config(config_path: Path) -> dict:
    """Read and validate user config content."""
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Could not parse YAML config at {config_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a YAML mapping of key/value settings.")

    return data


def load_config():
    config_path = _config_path()
    if config_path.exists():
        return {**DEFAULT_CONFIG, **_read_user_config(config_path)}
    return DEFAULT_CONFIG.copy()


def update_config(updates: dict) -> dict:
    config_path = _config_path()
    current = {}
    if config_path.exists():
        current = _read_user_config(config_path)

    merged = {**DEFAULT_CONFIG, **current, **updates}
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(merged, f, sort_keys=False)
    return merged
