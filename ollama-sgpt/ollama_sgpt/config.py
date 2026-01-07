from pathlib import Path
import yaml

DEFAULT_CONFIG = {
    "model": "llama3",
    "ollama_url": "http://localhost:11434/api/chat",
    "history_file": str(Path.home() / ".ollama_sgpt_history.json"),
    "stream": True
}

def load_config():
    config_path = Path.home() / ".ollama_sgpt.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return {**DEFAULT_CONFIG, **yaml.safe_load(f)}
    return DEFAULT_CONFIG
