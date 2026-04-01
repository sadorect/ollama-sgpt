# Installation Guide

This guide covers the current installation paths for **ollama-sgpt** and aligns with the runtime defaults in the repository.

---

## Prerequisites

### 1. Python

- Python `3.9+`

Check your version:

```bash
python --version
```

### 2. Ollama

Install Ollama from [https://ollama.ai/download](https://ollama.ai/download) or your platform package manager, then start it:

```bash
ollama serve
```

Pull at least one model before first use:

```bash
ollama pull llama3
```

Other good options:

- `mistral`
- `codellama`

---

## Recommended Install Path

### Install with `pipx`

```bash
pipx install git+https://github.com/sadorect/ollama-sgpt.git
```

Why this is recommended:

- isolated CLI environment
- simple upgrades
- no manual virtualenv management

---

## 5-Minute Quickstart

### Linux or macOS

```bash
# 1) Install pipx if needed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# 2) Install ollama-sgpt
pipx install git+https://github.com/sadorect/ollama-sgpt.git

# 3) Start Ollama and pull a model
ollama serve
ollama pull llama3

# 4) Verify
ollama-sgpt --version
ollama-sgpt "hello"
ollama-sgpt --shell "list python files recursively"
```

### Windows PowerShell

```powershell
# 1) Install pipx if needed
py -m pip install --user pipx
py -m pipx ensurepath

# 2) Install ollama-sgpt
pipx install git+https://github.com/sadorect/ollama-sgpt.git

# 3) Start Ollama and pull a model
ollama serve
ollama pull llama3

# 4) Verify
ollama-sgpt --version
ollama-sgpt "hello"
ollama-sgpt --shell "list python files recursively"
```

---

## Other Installation Methods

### Install with `pip`

```bash
pip install git+https://github.com/sadorect/ollama-sgpt.git
```

### Install From Source

From the repository root:

```bash
git clone https://github.com/sadorect/ollama-sgpt.git
cd ollama-sgpt
pip install -e .
```

With dev dependencies:

```bash
pip install -e ".[dev]"
```

### Install Directly From Git

```bash
pip install git+https://github.com/sadorect/ollama-sgpt.git
```

---

## Verify Installation

### Check Version

```bash
ollama-sgpt --version
```

### Confirm Ollama Connectivity

```bash
ollama --version
ollama list
ollama-sgpt "hello" --model llama3
```

### Check The Default Shell Behavior

On Linux/macOS:

- default shell family is `bash`

On Windows:

- default shell family is `powershell`

If you want `cmd`, set it explicitly in your config file:

```yaml
shell: cmd
```

Then try:

```bash
ollama-sgpt --shell "list python files recursively"
```

---

## Current Runtime Paths

These locations reflect the current codebase:

- Config file: `~/.ollama_sgpt.yaml`
- History file: `~/.ollama_sgpt_history.json`
- Session directory: `~/.ollama-sgpt/sessions/`

Example config:

```yaml
model: llama3
ollama_url: http://localhost:11434/api/chat
stream: true
shell: bash
```

On Windows, use:

```yaml
shell: powershell
```

---

## Troubleshooting Installation

### `ollama-sgpt: command not found`

If installed with `pipx`, refresh the path:

```bash
python -m pipx ensurepath
```

If installed with `pip`, confirm your Python scripts directory is on `PATH`.

### Cannot connect to `localhost:11434`

Check whether Ollama is up:

```bash
curl http://localhost:11434/api/version
```

```powershell
Invoke-WebRequest http://localhost:11434/api/version
```

Then start it if needed:

```bash
ollama serve
```

### Model not found

Pull the model first:

```bash
ollama pull llama3
```

If no local models are installed yet, this is also the first recovery step. Verify with:

```bash
ollama list
```

### Need Command Prompt output instead of PowerShell

Set the shell in the config file:

```yaml
shell: cmd
```

---

## Upgrade

### Upgrade a `pipx` install

```bash
pipx upgrade ollama-sgpt
```

### Upgrade a `pip` install

```bash
pip install --upgrade git+https://github.com/sadorect/ollama-sgpt.git
```

### Upgrade a source install

```bash
cd ollama-sgpt
git pull
pip install -e .
```

---

## Uninstall

Remove the package:

```bash
pip uninstall ollama-sgpt
```

Optional cleanup:

- delete `~/.ollama_sgpt.yaml`
- delete `~/.ollama_sgpt_history.json`
- delete `~/.ollama-sgpt/`

---

## Related Documentation

- [Configuration Guide](configuration.md)
- [Usage Guide](usage.md)
- [Execution Safety Guide](execution.md)
- [Troubleshooting](troubleshooting.md)
