"""Custom exceptions for ollama-sgpt."""


class OllamaSGPTError(Exception):
    """Base exception for ollama-sgpt."""

    pass


class OllamaConnectionError(OllamaSGPTError):
    """Raised when cannot connect to Ollama server."""

    pass


class OllamaModelError(OllamaSGPTError):
    """Raised when model is not available."""

    pass


class ConfigError(OllamaSGPTError):
    """Raised when configuration is invalid."""

    pass


class HistoryError(OllamaSGPTError):
    """Raised when history operations fail."""

    pass


class SessionError(OllamaSGPTError):
    """Raised when session operations fail."""

    pass
