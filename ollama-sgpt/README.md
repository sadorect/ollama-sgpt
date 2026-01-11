# ollama-sgpt

A powerful ShellGPT alternative powered by Ollama for local, private AI assistance.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Interactive mode
sgpt

# One-shot query
sgpt "your question here"

# Shell mode
sgpt --shell "list all files"

# Code mode
sgpt --code "fibonacci in python"

# Different model
sgpt --model mistral "hello"
```

## Configuration

Create `~/.ollama_sgpt.yaml`:

```yaml
model: llama3
ollama_url: http://localhost:11434/api/chat
stream: true
```

For more details, see the [main README](../README.md).
