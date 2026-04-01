import json
import time
import requests
from typing import Dict, List
from rich.console import Console
from .exceptions import OllamaConnectionError, OllamaModelError


console = Console()


def _base_url(url: str) -> str:
    """Return the Ollama base URL from the configured chat endpoint."""
    return url[:-9] if url.endswith("/api/chat") else url.rstrip("/")


def check_ollama_health(url: str, timeout: int = 5) -> bool:
    """Check if Ollama server is accessible.
    
    Args:
        url: The Ollama API URL
        timeout: Request timeout in seconds
        
    Returns:
        True if server is accessible
        
    Raises:
        OllamaConnectionError: If cannot connect to server
    """
    version_url = f"{_base_url(url)}/api/version"
    try:
        response = requests.get(version_url, timeout=timeout)
        response.raise_for_status()
        return True
    except requests.exceptions.Timeout as e:
        raise OllamaConnectionError(
            f"Timed out reaching Ollama at {version_url}: {e}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(
            f"Cannot reach Ollama at {version_url}: {e}"
        ) from e


def list_models(url: str) -> List[Dict[str, str]]:
    """List available Ollama models.
    
    Args:
        url: The Ollama API URL
        
    Returns:
        List of available models
        
    Raises:
        OllamaConnectionError: If cannot connect to server
    """
    tags_url = f"{_base_url(url)}/api/tags"
    try:
        response = requests.get(tags_url, timeout=10)
        response.raise_for_status()
        return response.json().get("models", [])
    except requests.exceptions.Timeout as e:
        raise OllamaConnectionError(
            f"Timed out listing Ollama models at {tags_url}: {e}"
        ) from e
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise OllamaConnectionError(
            f"Invalid response from Ollama model list endpoint {tags_url}: {e}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(
            f"Failed to list Ollama models at {tags_url}: {e}"
        ) from e


def validate_model(url: str, model_name: str) -> bool:
    """Validate that a model exists.
    
    Args:
        url: The Ollama API URL
        model_name: Name of the model to validate
        
    Returns:
        True if model exists
        
    Raises:
        OllamaModelError: If model not found
        OllamaConnectionError: If cannot connect to server
    """
    models = list_models(url)
    available = sorted(
        model["name"]
        for model in models
        if isinstance(model, dict) and model.get("name")
    )

    if not available:
        raise OllamaModelError(
            "No local Ollama models are installed yet. Pull one with "
            "`ollama pull llama3` and retry."
        )

    if model_name not in available:
        raise OllamaModelError(
            f"Model '{model_name}' is not installed locally. Pull it with "
            f"`ollama pull {model_name}` or rerun with one of: {', '.join(available)}"
        )

    return True


def stream_chat(
    url: str,
    payload: Dict,
    request_timeout: int = 120,
    idle_timeout: int = 60,
    echo: bool = True,
) -> str:
    """Stream chat response from Ollama.
    
    Args:
        url: The Ollama API URL
        payload: Request payload with model, messages, etc.
        
    Returns:
        Complete response text
        
    Raises:
        OllamaConnectionError: If request fails or times out
    """
    try:
        with requests.post(url, json=payload, stream=True, timeout=request_timeout) as r:
            r.raise_for_status()
            output = ""
            last_chunk_time = time.monotonic()
            for line in r.iter_lines():
                if not line:
                    if time.monotonic() - last_chunk_time > idle_timeout:
                        raise OllamaConnectionError(
                            f"No response received for {idle_timeout}s. Try a smaller model or increase stream_idle_timeout.")
                    continue
                try:
                    data = json.loads(line.decode())
                    if "message" in data:
                        content = data["message"].get("content", "")
                        output += content
                        if echo:
                            console.print(content, end="", soft_wrap=True)
                        last_chunk_time = time.monotonic()
                    if data.get("done"):
                        if echo:
                            console.print()
                        break
                except json.JSONDecodeError:
                    continue
            return output
    except requests.exceptions.Timeout:
        raise OllamaConnectionError("Request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Request failed: {e}")


def chat(url: str, payload: Dict, request_timeout: int = 120) -> str:
    """Non-streaming chat request to Ollama.
    
    Args:
        url: The Ollama API URL
        payload: Request payload with model, messages, etc.
        
    Returns:
        Response text
        
    Raises:
        OllamaConnectionError: If request fails
    """
    try:
        r = requests.post(url, json=payload, timeout=request_timeout)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.Timeout:
        raise OllamaConnectionError("Request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Request failed: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise OllamaConnectionError(f"Invalid response format: {e}")
