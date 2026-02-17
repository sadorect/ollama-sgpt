# Installation Guide

Welcome to **ollama-sgpt**! This guide will help you install and set up the tool on your system.

---

## Prerequisites

### 1. Ollama

ollama-sgpt requires [Ollama](https://ollama.ai) to be installed and running on your system.

**Install Ollama:**

```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

**Start Ollama server:**

```bash
ollama serve
```

**Download a model:**

```bash
# Download the default model (llama2)
ollama pull llama2

# Or use other models
ollama pull mistral
ollama pull codellama
```

### 2. Python

- **Python 3.9 or higher** is required
- Check your version: `python --version`

---

## Installation Methods

### Option 1: Install from PyPI (Recommended)

```bash
pip install ollama-sgpt
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/sadorect/ollama-sgpt.git
cd ollama-sgpt

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Option 3: Install from Git

```bash
pip install git+https://github.com/sadorect/ollama-sgpt.git
```

---

## Verify Installation

### Check Version

```bash
ollama-sgpt --version
```

### Test Basic Functionality

```bash
# Simple query
ollama-sgpt "what is the meaning of life?"

# Check Ollama connection
ollama-sgpt "hello" --model llama2
```

### Run Tests (From Source)

```bash
cd ollama-sgpt
pytest
```

---

## Configuration

### Default Configuration

ollama-sgpt works out of the box with sensible defaults:

- **Ollama URL**: `http://localhost:11434`
- **Model**: `llama2`
- **Config Location**: `~/.ollama-sgpt/config.yaml`

### Create Custom Configuration

```bash
mkdir -p ~/.ollama-sgpt
cat > ~/.ollama-sgpt/config.yaml << EOF
ollama_url: http://localhost:11434
model: llama2
stream: true
history_file: ~/.ollama-sgpt/history.json
EOF
```

See [Configuration Guide](configuration.md) for more options.

---

## Platform-Specific Notes

### macOS

- Install via Homebrew: `brew install ollama`
- Ollama runs as a service automatically
- Config location: `~/.ollama-sgpt/`

### Linux

- Ollama typically runs on port 11434
- Start manually: `ollama serve`
- Or use systemd: `systemctl start ollama`
- Config location: `~/.ollama-sgpt/`

### Windows

- Download Ollama installer from official website
- Ollama runs as Windows service
- Config location: `%USERPROFILE%\.ollama-sgpt\`
- Use `pip install ollama-sgpt` in PowerShell or CMD

---

## Troubleshooting Installation

### Issue: "ollama-sgpt: command not found"

**Solution:**

```bash
# Ensure Python's bin directory is in PATH
export PATH="$PATH:$HOME/.local/bin"

# Or use pip's user installation flag
pip install --user ollama-sgpt
```

### Issue: "Connection refused to localhost:11434"

**Solution:**

1. Check if Ollama is running: `curl http://localhost:11434/api/version`
2. Start Ollama: `ollama serve`
3. Check firewall settings

### Issue: "Model not found"

**Solution:**

```bash
# Pull the model first
ollama pull llama2

# Or specify a different model
ollama-sgpt "hello" --model mistral
```

### Issue: "Permission denied"

**Solution:**

```bash
# Install without sudo (recommended)
pip install --user ollama-sgpt

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install ollama-sgpt
```

---

## Upgrading

### Upgrade from PyPI

```bash
pip install --upgrade ollama-sgpt
```

### Upgrade from Source

```bash
cd ollama-sgpt
git pull
pip install -e .
```

---

## Uninstallation

```bash
# Uninstall package
pip uninstall ollama-sgpt

# Remove configuration (optional)
rm -rf ~/.ollama-sgpt
```

---

## Next Steps

- Read the [Usage Guide](usage.md) to learn how to use ollama-sgpt
- Explore [Configuration Options](configuration.md)
- Check out [Example Workflows](../examples/workflows/)
- Learn about [Safe Code Execution](execution.md)

---

## Getting Help

- **Documentation**: https://github.com/sadorect/ollama-sgpt/docs
- **Issues**: https://github.com/sadorect/ollama-sgpt/issues
- **Discussions**: https://github.com/sadorect/ollama-sgpt/discussions

---

**Congratulations! You're ready to use ollama-sgpt! 🎉**
