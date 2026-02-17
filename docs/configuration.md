# Configuration Guide

Complete guide to configuring **ollama-sgpt**.

---

## Table of Contents

- [Configuration File](#configuration-file)
- [Configuration Options](#configuration-options)
- [Environment Variables](#environment-variables)
- [Configuration Priority](#configuration-priority)
- [Example Configurations](#example-configurations)
- [Advanced Configuration](#advanced-configuration)

---

## Configuration File

### Location

**ollama-sgpt** reads configuration from:

```
~/.ollama_sgpt.yaml
```

On Linux/macOS: `/home/username/.ollama_sgpt.yaml`
On Windows: `C:\Users\username\.ollama_sgpt.yaml`

### Creating a Config File

Create the file if it doesn't exist:

```bash
# Linux/macOS
touch ~/.ollama_sgpt.yaml

# Windows (PowerShell)
New-Item -Path $env:USERPROFILE\.ollama_sgpt.yaml -ItemType File
```

---

## Configuration Options

### Complete Reference

| Option         | Type    | Default                           | Description                   |
| -------------- | ------- | --------------------------------- | ----------------------------- |
| `model`        | string  | `llama3`                          | Ollama model to use           |
| `ollama_url`   | string  | `http://localhost:11434/api/chat` | Ollama API endpoint           |
| `history_file` | string  | `~/.ollama_sgpt_history.json`     | Conversation history location |
| `stream`       | boolean | `true`                            | Enable streaming responses    |

### Default Configuration

If no config file exists, these defaults are used:

```yaml
model: llama3
ollama_url: http://localhost:11434/api/chat
history_file: ~/.ollama_sgpt_history.json
stream: true
```

---

## Configuration Options Explained

### Model

Specifies which Ollama model to use for queries.

```yaml
model: llama3
```

**Available Models:**

- `llama2` - General purpose
- `llama3` - Latest, improved model
- `mistral` - Faster, good for quick queries
- `codellama` - Optimized for code
- `mixtral` - High quality, larger model

**Check installed models:**

```bash
ollama list
```

**Install a model:**

```bash
ollama pull mistral
```

### Ollama URL

The API endpoint for your Ollama instance.

```yaml
ollama_url: http://localhost:11434/api/chat
```

**Use cases:**

- **Local**: `http://localhost:11434/api/chat` (default)
- **Remote server**: `http://192.168.1.100:11434/api/chat`
- **Custom port**: `http://localhost:8080/api/chat`

**Testing connection:**

```bash
curl http://localhost:11434/api/tags
```

### History File

Location where conversation history is stored.

```yaml
history_file: ~/.ollama_sgpt_history.json
```

**Custom locations:**

```yaml
# Project-specific history
history_file: ~/projects/myproject/.sgpt_history.json

# Dropbox sync
history_file: ~/Dropbox/.ollama_sgpt_history.json

# Temporary history
history_file: /tmp/.ollama_sgpt_history.json
```

### Streaming

Enable/disable response streaming.

```yaml
stream: true
```

**When to disable:**

- Slow network connections
- Batch processing scripts
- Output parsing requirements

```yaml
stream: false
```

---

## Environment Variables

Environment variables override configuration file settings.

### Available Variables

| Variable       | Purpose        | Example                                 |
| -------------- | -------------- | --------------------------------------- |
| `OLLAMA_MODEL` | Override model | `export OLLAMA_MODEL=mistral`           |
| `OLLAMA_URL`   | Override URL   | `export OLLAMA_URL=http://remote:11434` |

### Setting Environment Variables

**Linux/macOS (bash/zsh):**

```bash
export OLLAMA_MODEL=mistral
export OLLAMA_URL=http://192.168.1.100:11434
```

**Windows (PowerShell):**

```powershell
$env:OLLAMA_MODEL = "mistral"
$env:OLLAMA_URL = "http://192.168.1.100:11434"
```

**Windows (Command Prompt):**

```cmd
set OLLAMA_MODEL=mistral
set OLLAMA_URL=http://192.168.1.100:11434
```

### Persistent Environment Variables

**Linux/macOS (~/.bashrc or ~/.zshrc):**

```bash
# Add to end of file
export OLLAMA_MODEL=llama3
export OLLAMA_URL=http://localhost:11434
```

**Windows (System Properties):**

1. Open System Properties → Environment Variables
2. Add User Variables:
   - `OLLAMA_MODEL` = `llama3`
   - `OLLAMA_URL` = `http://localhost:11434`

---

## Configuration Priority

Settings are applied in this order (highest to lowest priority):

1. **Command-line flags**
2. **Environment variables**
3. **Configuration file** (`~/.ollama_sgpt.yaml`)
4. **Default values**

### Example Priority

```yaml
# ~/.ollama_sgpt.yaml
model: llama2
```

```bash
export OLLAMA_MODEL=mistral

# This uses codellama (CLI flag overrides all)
ollama-sgpt --model codellama "hello"

# This uses mistral (env var overrides config file)
ollama-sgpt "hello"
```

---

## Example Configurations

### Basic Configuration

```yaml
# ~/.ollama_sgpt.yaml
model: llama3
stream: true
```

### Remote Ollama Server

```yaml
model: mistral
ollama_url: http://192.168.1.100:11434/api/chat
stream: true
history_file: ~/.ollama_sgpt_history.json
```

### Code-Focused Setup

```yaml
model: codellama
stream: true
history_file: ~/projects/.sgpt_history.json
```

### Fast Responses (No Streaming)

```yaml
model: mistral
stream: false
```

### Multiple Environments

You can't have multiple config files, but you can use environment variables:

```bash
# Development
alias sgpt-dev='OLLAMA_URL=http://dev-server:11434 ollama-sgpt'

# Production
alias sgpt-prod='OLLAMA_URL=http://prod-server:11434 ollama-sgpt'

# Local with specific model
alias sgpt-code='OLLAMA_MODEL=codellama ollama-sgpt'
```

---

## Advanced Configuration

### Project-Specific Configuration

Use environment variables in project scripts:

```bash
#!/bin/bash
# project-chat.sh

export OLLAMA_MODEL=codellama
export OLLAMA_URL=http://localhost:11434

ollama-sgpt --session myproject "$@"
```

Usage:

```bash
./project-chat.sh "explain main.py"
```

### Custom History Locations

Separate history for different contexts:

```bash
# Work
alias sgpt-work='HISTORY_FILE=~/.sgpt_work.json ollama-sgpt'

# Personal
alias sgpt-personal='HISTORY_FILE=~/.sgpt_personal.json ollama-sgpt'
```

### Scripting with Configuration

```bash
#!/bin/bash
# Automated code review

export OLLAMA_MODEL=codellama

for file in src/*.py; do
  ollama-sgpt --context "$file" \
    --session code-review \
    "review this code" >> report.md
done
```

### Docker Configuration

If running Ollama in Docker:

```yaml
# ~/.ollama_sgpt.yaml
model: llama3
ollama_url: http://ollama-container:11434/api/chat
```

Or with Docker networking:

```bash
# If ollama-sgpt is also in Docker
ollama_url: http://host.docker.internal:11434/api/chat
```

---

## Session Storage

Sessions are stored separately from configuration:

**Session storage location:**

```
~/.ollama_sgpt_sessions/
```

**Session files:**

- Each session is a JSON file: `myproject.json`
- Contains conversation history
- Created automatically on first use

**Managing session storage:**

```bash
# View sessions
ls ~/.ollama_sgpt_sessions/

# Backup sessions
cp -r ~/.ollama_sgpt_sessions/ ~/backups/sessions_$(date +%Y%m%d)

# Clean old sessions
find ~/.ollama_sgpt_sessions/ -mtime +30 -delete
```

---

## Configuration Troubleshooting

### Verify Current Configuration

Create a test script to check what configuration is active:

```bash
# Check if config file exists
ls -la ~/.ollama_sgpt.yaml

# Check environment variables
env | grep OLLAMA

# Test connection to Ollama
curl http://localhost:11434/api/tags
```

### Common Issues

**1. Config file not being read**

Check file location and permissions:

```bash
ls -la ~/.ollama_sgpt.yaml
# Should show: -rw-r--r-- (readable)
```

**2. YAML syntax errors**

Validate YAML syntax:

```bash
# Install yamllint
pip install yamllint

# Check syntax
yamllint ~/.ollama_sgpt.yaml
```

**3. Model not found**

```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3
```

**4. Cannot connect to Ollama**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check firewall (Linux)
sudo ufw status

# Check if Ollama service is active
systemctl status ollama  # Linux
```

---

## Configuration Best Practices

### 1. Use Appropriate Models

- **General chat**: `llama3`, `mistral`
- **Code tasks**: `codellama`
- **Fast queries**: `mistral`
- **High quality**: `mixtral`

### 2. Enable Streaming

Keep streaming enabled for better UX:

```yaml
stream: true
```

Disable only for batch processing.

### 3. Secure Remote Connections

If using remote Ollama:

```yaml
# Use HTTPS if available
ollama_url: https://ollama.example.com/api/chat
```

### 4. Backup Configuration

```bash
# Backup config and sessions
cp ~/.ollama_sgpt.yaml ~/.ollama_sgpt.yaml.backup
tar -czf sgpt-backup.tar.gz ~/.ollama_sgpt_sessions/
```

### 5. Version Control (for teams)

```yaml
# team-config.yaml (in project repo)
model: codellama
stream: true
```

Team members copy to `~/.ollama_sgpt.yaml`

---

## Sample Configuration Templates

### Minimal Setup

```yaml
model: llama3
```

### Developer Setup

```yaml
model: codellama
stream: true
history_file: ~/dev/.sgpt_history.json
```

### Team/Remote Setup

```yaml
model: llama3
ollama_url: http://ai-server.company.com:11434/api/chat
stream: true
```

### Performance-Optimized

```yaml
model: mistral
stream: true
```

---

## Related Documentation

- [Installation Guide](installation.md) - Setup and prerequisites
- [Usage Guide](usage.md) - How to use ollama-sgpt
- [Session Guide](sessions.md) - Managing conversations
- [Troubleshooting](troubleshooting.md) - Solving common issues

---

**Need help?** Open an issue on [GitHub](https://github.com/sadorect/ollama-sgpt/issues).
