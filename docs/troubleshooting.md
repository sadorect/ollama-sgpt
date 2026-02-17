# Troubleshooting Guide

Solutions to common issues with **ollama-sgpt**.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Issues](#connection-issues)
- [Model Issues](#model-issues)
- [Execution Issues](#execution-issues)
- [Session Issues](#session-issues)
- [Performance Issues](#performance-issues)
- [General Issues](#general-issues)

---

## Installation Issues

### "command not found: ollama-sgpt"

**Problem:** Command not in PATH after installation.

**Solutions:**

```bash
# 1. Verify installation
pip show ollama-sgpt

# 2. Check if installed in user directory
ls ~/.local/bin/ollama-sgpt

# 3. Add to PATH (Linux/macOS)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Reinstall with --force
pip install --force-reinstall --user ollama-sgpt

# 5. Use python -m method
python -m ollama_sgpt "test query"
```

### "No module named 'ollama_sgpt'"

**Problem:** Package not installed properly.

**Solutions:**

```bash
# 1. Check Python version
python --version  # Should be 3.9+

# 2. Reinstall
pip uninstall ollama-sgpt
pip install ollama-sgpt

# 3. Try with python3
pip3 install ollama-sgpt

# 4. Install in virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install ollama-sgpt
```

### "error: externally-managed-environment"

**Problem:** System-protected Python (Debian/Ubuntu 23+).

**Solutions:**

```bash
# Option 1: Use pipx (recommended)
sudo apt install pipx
pipx install ollama-sgpt

# Option 2: Use virtual environment
python -m venv ~/venvs/ollama-sgpt
source ~/venvs/ollama-sgpt/bin/activate
pip install ollama-sgpt

# Option 3: User installation
pip install --user ollama-sgpt

# Option 4: Override (not recommended)
pip install --break-system-packages ollama-sgpt
```

### "Permission denied" during installation

**Problem:** Trying to install system-wide without privileges.

**Solutions:**

```bash
# 1. Install for user only
pip install --user ollama-sgpt

# 2. Use sudo (not recommended)
sudo pip install ollama-sgpt

# 3. Use virtual environment (best practice)
python -m venv venv && source venv/bin/activate
pip install ollama-sgpt
```

---

## Connection Issues

### "Connection refused" to Ollama

**Problem:** Cannot connect to Ollama API.

**Diagnostic:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check process
ps aux | grep ollama

# Check port
ss -tlnp | grep 11434  # Linux
lsof -i :11434         # macOS
```

**Solutions:**

```bash
# 1. Start Ollama
ollama serve  # Linux/macOS

# 2. Check service status (Linux)
systemctl status ollama
systemctl start ollama

# 3. Verify firewall
sudo ufw status  # Linux
sudo ufw allow 11434

# 4. Check Ollama URL in config
cat ~/.ollama_sgpt.yaml
# Should show: ollama_url: http://localhost:11434/api/chat
```

### "Connection timeout"

**Problem:** Slow or unresponsive Ollama instance.

**Solutions:**

```bash
# 1. Check network connectivity
ping localhost
ping your-server-ip

# 2. Verify Ollama is responsive
time curl http://localhost:11434/api/tags

# 3. Restart Ollama
killall ollama
ollama serve

# 4. Check system resources
htop  # Check CPU/RAM usage
df -h  # Check disk space
```

### Remote Ollama connection fails

**Problem:** Cannot connect to remote Ollama server.

**Solutions:**

```bash
# 1. Verify server is accessible
ping remote-server

# 2. Test Ollama endpoint
curl http://remote-server:11434/api/tags

# 3. Check firewall on server
# On server:
sudo ufw allow 11434
sudo firewall-cmd --add-port=11434/tcp --permanent

# 4. Update configuration
echo "ollama_url: http://remote-server:11434/api/chat" > ~/.ollama_sgpt.yaml

# 5. Use environment variable
export OLLAMA_URL=http://remote-server:11434
```

---

## Model Issues

### "Model not found"

**Problem:** Requested model not installed in Ollama.

**Solutions:**

```bash
# 1. List available models
ollama list

# 2. Pull missing model
ollama pull llama3
ollama pull mistral
ollama pull codellama

# 3. Use different model
ollama-sgpt --model mistral "test query"

# 4. Update default model
echo "model: mistral" > ~/.ollama_sgpt.yaml
```

### Model downloads too slow

**Problem:** Slow download of large models.

**Solutions:**

```bash
# 1. Check internet speed
speedtest-cli

# 2. Use smaller model
ollama pull llama2:7b  # Instead of llama2:70b

# 3. Download during off-peak hours

# 4. Use mirror (if available)
# Check Ollama documentation for mirrors
```

### "Out of memory" errors

**Problem:** Model too large for available RAM.

**Solutions:**

```bash
# 1. Check available memory
free -h  # Linux
vm_stat  # macOS

# 2. Use smaller model
ollama pull llama2:7b   # ~4GB RAM
ollama pull mistral:7b  # ~4GB RAM

# 3. Close other applications

# 4. Set up swap (Linux)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 5. Upgrade RAM (if possible)
```

### Model responses are poor quality

**Problem:** Inaccurate or low-quality responses.

**Solutions:**

```bash
# 1. Try a better model
ollama pull llama3  # Latest model
ollama-sgpt --model llama3 "your query"

# 2. Use specialized model
ollama-sgpt --model codellama --code "code task"

# 3. Provide more context
ollama-sgpt --context file.py "specific question"

# 4. Use appropriate role
ollama-sgpt --shell "shell command task"
ollama-sgpt --explain "explanation request"

# 5. Be more specific in prompts
# ❌ "help with files"
# ✅ "how do I find Python files modified in the last week?"
```

---

## Execution Issues

### "Command not executed"

**Problem:** `--execute` flag not working.

**Solutions:**

```bash
# 1. Verify flags are correct
ollama-sgpt --shell --execute "your query"

# 2. Check if command was extracted
ollama-sgpt --shell --dry-run "your query"

# 3. Ensure shell mode is active
ollama-sgpt --shell "list files"  # Then add --execute

# 4. Review confirmation prompt
# Make sure you're typing correct confirmation:
# LOW/MEDIUM: y/n
# HIGH: "yes"
# CRITICAL: "yes I understand"
```

### False positive risk detection

**Problem:** Safe commands flagged as dangerous.

**Solutions:**

```bash
# Safe command flagged as MEDIUM/HIGH
ollama-sgpt --shell --execute "sudo systemctl status nginx"
# Just review and confirm if you know it's safe

# Override with --yes for LOW/MEDIUM
ollama-sgpt --shell --execute --yes "safe command"

# HIGH/CRITICAL always require manual review (by design)
```

### Execution timeout

**Problem:** Commands timing out after 30 seconds.

**Current:** Timeout not configurable via CLI (30s default).

**Workarounds:**

```bash
# 1. Optimize command to run faster
# ❌ find / -name "*.log"
# ✅ find /var/log -name "*.log"

# 2. Run without execution flag
ollama-sgpt --shell "long running task"
# Then copy command and run manually

# 3. Break into smaller steps
ollama-sgpt --shell --execute "step 1"
ollama-sgpt --shell --execute "step 2"
```

---

## Session Issues

### "Session not found"

**Problem:** Session appears to be missing.

**Solutions:**

```bash
# 1. List all sessions
ollama-sgpt --list-sessions

# 2. Check session directory
ls -la ~/.ollama_sgpt_sessions/

# 3. Verify session name (case-sensitive)
# ❌ ollama-sgpt -s MyProject
# ✅ ollama-sgpt -s myproject

# 4. Create session if it doesn't exist
ollama-sgpt -s newsession "first message"
```

### Cannot delete session

**Problem:** Permission error when deleting.

**Solutions:**

```bash
# 1. Check permissions
ls -la ~/.ollama_sgpt_sessions/

# 2. Fix permissions
chmod 644 ~/.ollama_sgpt_sessions/*.json
chmod 755 ~/.ollama_sgpt_sessions/

# 3. Delete manually
rm ~/.ollama_sgpt_sessions/sessionname.json

# 4. Check ownership
# If owned by root:
sudo chown $USER:$USER ~/.ollama_sgpt_sessions/*.json
```

### Corrupted session file

**Problem:** Session fails to load.

**Symptoms:**

```
Error: Failed to load session 'myproject'
```

**Solutions:**

```bash
# 1. Check JSON validity
cat ~/.ollama_sgpt_sessions/myproject.json | jq

# 2. Backup and remove
cp ~/.ollama_sgpt_sessions/myproject.json ~/myproject.json.backup
rm ~/.ollama_sgpt_sessions/myproject.json

# 3. Recreate session
ollama-sgpt -s myproject "starting fresh"

# 4. Restore from backup (if partially valid)
# Manually edit backup to fix JSON
cp ~/myproject.json.backup ~/.ollama_sgpt_sessions/myproject.json
```

### Too many sessions slow performance

**Problem:** 100+ sessions causing slowdown.

**Solutions:**

```bash
# 1. List all sessions
ollama-sgpt --list-sessions

# 2. Delete old sessions
find ~/.ollama_sgpt_sessions/ -name "*.json" -mtime +30 -delete

# 3. Archive important sessions
mkdir ~/session-archives
mv ~/.ollama_sgpt_sessions/important-*.json ~/session-archives/

# 4. Delete by pattern
rm ~/.ollama_sgpt_sessions/temp-*.json
rm ~/.ollama_sgpt_sessions/test-*.json
```

---

## Performance Issues

### Slow response times

**Problem:** Responses take too long.

**Solutions:**

```bash
# 1. Use faster model
ollama-sgpt --model mistral "query"  # Faster than llama3

# 2. Disable streaming (if network is slow)
echo "stream: false" >> ~/.ollama_sgpt.yaml

# 3. Check Ollama performance
# Monitor CPU/GPU usage while querying
htop

# 4. Reduce conversation history
ollama-sgpt -s newsession "query"  # Fresh session

# 5. Use remote GPU server
echo "ollama_url: http://gpu-server:11434/api/chat" > ~/.ollama_sgpt.yaml
```

### High memory usage

**Problem:** ollama-sgpt or Ollama using too much RAM.

**Solutions:**

```bash
# 1. Check memory usage
ps aux | grep -E '(ollama|python)'

# 2. Use smaller model
ollama pull llama2:7b

# 3. Restart Ollama
killall ollama
ollama serve

# 4. Clear session history
find ~/.ollama_sgpt_sessions/ -delete
ollama-sgpt --list-sessions

# 5. Limit context in prompts
# Avoid loading large files with --context
```

### Streaming stops mid-response

**Problem:** Response cuts off during streaming.

**Solutions:**

```bash
# 1. Check network stability
ping localhost

# 2. Disable streaming
ollama-sgpt --no-stream "query"

# 3. Restart Ollama
killall ollama && ollama serve

# 4. Check logs
journalctl -u ollama -f  # Linux
tail -f ~/.ollama/logs/server.log  # If available
```

---

## General Issues

### Configuration file not loaded

**Problem:** Settings in `~/.ollama_sgpt.yaml` not applied.

**Solutions:**

```bash
# 1. Verify file location
ls -la ~/.ollama_sgpt.yaml

# 2. Check YAML syntax
python -c "import yaml; yaml.safe_load(open('$HOME/.ollama_sgpt.yaml'))"

# Or use yamllint:
yamllint ~/.ollama_sgpt.yaml

# 3. Check permissions
chmod 644 ~/.ollama_sgpt.yaml

# 4. Verify content
cat ~/.ollama_sgpt.yaml
# Should show valid YAML:
# model: llama3
# stream: true
```

### Environment variables not working

**Problem:** `OLLAMA_MODEL` or `OLLAMA_URL` ignored.

**Solutions:**

```bash
# 1. Verify variables are set
echo $OLLAMA_MODEL
echo $OLLAMA_URL
env | grep OLLAMA

# 2. Export variables properly
export OLLAMA_MODEL=mistral
export OLLAMA_URL=http://localhost:11434

# 3. Make permanent (Linux/macOS)
echo 'export OLLAMA_MODEL=mistral' >> ~/.bashrc
source ~/.bashrc

# 4. Check shell type
echo $SHELL
# If zsh, update ~/.zshrc instead of ~/.bashrc

# 5. Command-line flags override everything
ollama-sgpt --model llama3 "query"  # This wins
```

### Unicode/emoji rendering issues

**Problem:** Emojis or Unicode characters display incorrectly.

**Solutions:**

```bash
# 1. Check terminal supports UTF-8
locale | grep UTF-8

# 2. Set locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 3. Use modern terminal
# Linux: GNOME Terminal, Konsole, Alacritty
# macOS: iTerm2, Alacritty
# Windows: Windows Terminal, WSL with modern terminal

# 4. Update fonts
# Install fonts with emoji support:
# - Noto Color Emoji (Linux)
# - Apple Color Emoji (macOS)
# - Segoe UI Emoji (Windows)
```

### Colors not displaying

**Problem:** No colors or highlighting in output.

**Solutions:**

```bash
# 1. Check if terminal supports colors
echo $TERM  # Should be xterm-256color or similar

# 2. Force color support
export TERM=xterm-256color

# 3. Check if NO_COLOR is set
unset NO_COLOR

# 4. Verify Rich library
python -c "from rich.console import Console; Console().print('[red]Test[/red]')"

# 5. Use modern terminal
# Avoid basic terminals like Linux console
```

### Command history not saving

**Problem:** Previous commands not accessible with arrow keys.

**In interactive mode:**

```bash
# 1. Check history file
ls -la ~/.ollama_sgpt_history.json

# 2. Check permissions
chmod 644 ~/.ollama_sgpt_history.json

# 3. Verify prompt_toolkit
pip install --upgrade prompt-toolkit

# 4. Start fresh
ollama-sgpt
# Press Up arrow - should show previous commands
```

### "Import error" for dependencies

**Problem:** Missing or outdated dependencies.

**Solutions:**

```bash
# 1. Reinstall with dependencies
pip install --force-reinstall ollama-sgpt

# 2. Install specific missing package
pip install rich pyyaml requests prompt-toolkit

# 3. Check versions
pip show rich pyyaml requests prompt-toolkit

# 4. Upgrade all
pip install --upgrade ollama-sgpt rich pyyaml requests prompt-toolkit
```

---

## Getting More Help

### Enable Debug Mode

```bash
# Run with Python verbose mode
python -v -m ollama_sgpt "query"

# Check Python errors
python -c "import ollama_sgpt; print(ollama_sgpt.__version__)"
```

### Check Logs

```bash
# Ollama logs (if systemd)
journalctl -u ollama -f

# Python errors
python -m ollama_sgpt "test" 2>&1 | tee error.log
```

### Report Issues

If problem persists:

1. **Gather information:**

   ```bash
   python --version
   pip show ollama-sgpt
   ollama --version
   uname -a  # System info
   ```

2. **Create minimal reproduction:**

   ```bash
   ollama-sgpt "simple test query"
   ```

3. **Report on GitHub:**
   - https://github.com/sadorect/ollama-sgpt/issues
   - Include: OS, Python version, ollama-sgpt version, error message, steps to reproduce

4. **Community help:**
   - GitHub Discussions: https://github.com/sadorect/ollama-sgpt/discussions

---

## Quick Diagnostic Checklist

Run this to check everything:

```bash
#!/bin/bash
echo "=== System Check ==="
python --version
pip show ollama-sgpt | grep Version
ollama --version

echo -e "\n=== Configuration ==="
ls -la ~/.ollama_sgpt.yaml
cat ~/.ollama_sgpt.yaml

echo -e "\n=== Ollama Connection ==="
curl -s http://localhost:11434/api/tags | head -n 5

echo -e "\n=== Models ==="
ollama list

echo -e "\n=== Sessions ==="
ollama-sgpt --list-sessions

echo -e "\n=== Test Query ==="
ollama-sgpt "hello"
```

Save as `check.sh`, run with `bash check.sh`.

---

## Related Documentation

- [Installation Guide](installation.md) - Setup instructions
- [Usage Guide](usage.md) - How to use features
- [Configuration Guide](configuration.md) - Configuration options
- [Session Guide](sessions.md) - Managing conversations
- [Execution Guide](execution.md) - Execution safety

---

**Still having issues?** [Open an issue](https://github.com/sadorect/ollama-sgpt/issues/new) with details! 🔧
