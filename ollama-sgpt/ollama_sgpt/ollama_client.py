import json
import requests
from rich.console import Console
from typing import Dict, List
from .exceptions import OllamaConnectionError, OllamaModelError

console = Console()


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
    try:
        base_url = url.replace('/api/chat', '')
        response = requests.get(f"{base_url}/api/version", timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Cannot connect to Ollama at {url}: {e}")


def list_models(url: str) -> List[Dict[str, str]]:
    """List available Ollama models.
    
    Args:
        url: The Ollama API URL
        
    Returns:
        List of available models
        
    Raises:
        OllamaConnectionError: If cannot connect to server
    """
    try:
        base_url = url.replace('/api/chat', '')
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        return response.json().get("models", [])
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Failed to list models: {e}")


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
    try:
        models = list_models(url)
        available = [m["name"] for m in models]
        if model_name not in available:
            raise OllamaModelError(
                f"Model '{model_name}' not found. Available: {', '.join(available)}"
            )
        return True
    except OllamaConnectionError:
        # If we can't connect, skip validation (server might not be running yet)
        console.print("[yellow]Warning: Could not validate model (Ollama might not be running)[/]")
        return True


def stream_chat(url: str, payload: Dict) -> str:
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
        with requests.post(url, json=payload, stream=True, timeout=120) as r:
            r.raise_for_status()
            output = ""
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode())
                    if "message" in data:
                        content = data["message"].get("content", "")
                        output += content
                        console.print(content, end="", soft_wrap=True)
                    if data.get("done"):
                        console.print()
                        break
                except json.JSONDecodeError:
                    continue
            return output
    except requests.exceptions.Timeout:
        raise OllamaConnectionError("Request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Request failed: {e}")


def chat(url: str, payload: Dict) -> str:
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
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.Timeout:
        raise OllamaConnectionError("Request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Request failed: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise OllamaConnectionError(f"Invalid response format: {e}")
