# Troubleshooting Guide

This guide covers the most common runtime problems in the current `ollama-sgpt` codebase.

---

## Quick Checks

Before deep debugging, verify:

```bash
ollama --version
ollama-sgpt --version
ollama list
curl http://localhost:11434/api/version
```

On Windows PowerShell:

```powershell
ollama --version
ollama-sgpt --version
ollama list
Invoke-WebRequest http://localhost:11434/api/version
```

Also check your config file:

```bash
cat ~/.ollama_sgpt.yaml
```

For a consolidated runtime check, run:

```bash
ollama-sgpt --doctor
```

---

## Installation Problems

### `ollama-sgpt: command not found`

If you installed with `pipx`:

```bash
python -m pipx ensurepath
```

If you installed with `pip`, make sure your Python scripts directory is on `PATH`.

### `No module named 'ollama_sgpt'`

Reinstall the package:

```bash
pip uninstall ollama-sgpt
pip install ollama-sgpt
```

Or use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install ollama-sgpt
```

### Externally managed Python environment

Use `pipx` or a virtual environment instead of forcing a system-wide install.

---

## Connection Problems

### Cannot connect to Ollama

Start the server:

```bash
ollama serve
```

Then verify the endpoint:

```bash
curl http://localhost:11434/api/version
```

Current default endpoint:

```text
http://localhost:11434/api/chat
```

Current default config file:

```text
~/.ollama_sgpt.yaml
```

If you use a remote Ollama server, set it in the config file:

```yaml
ollama_url: http://remote-server:11434/api/chat
```

### Slow or hanging responses

Try:

- a smaller model such as `mistral`
- `--no-stream`
- increasing `request_timeout` and `stream_idle_timeout` in the config file

Example:

```yaml
request_timeout: 180
stream_idle_timeout: 90
```

---

## Model Problems

### Model not found

List installed models:

```bash
ollama list
```

Pull the model you want:

```bash
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

If `ollama-sgpt` says the requested model is not installed locally, either:

- pull that exact model with `ollama pull <model-name>`
- rerun with `--model <installed-model>`
- update `model:` in `~/.ollama_sgpt.yaml`

### No models are installed yet

Pull one local model before first use:

```bash
ollama pull llama3
```

Then verify:

```bash
ollama list
ollama-sgpt "hello"
```

You can override the model per command:

```bash
ollama-sgpt --model mistral "hello"
```

### Model quality is poor

Try:

- `llama3` for general use
- `mistral` for faster responses
- `codellama` for code-heavy tasks
- better prompts
- `--context` for relevant files

---

## Shell And Execution Problems

### `--execute` does nothing useful

Make sure you are using shell mode:

```bash
ollama-sgpt --shell --execute "show disk usage"
```

If you want to inspect first:

```bash
ollama-sgpt --shell --dry-run "show disk usage"
```

### Wrong shell syntax is returned

Shell behavior depends on the configured `shell` value in `~/.ollama_sgpt.yaml`.

Examples:

```yaml
shell: bash
```

```yaml
shell: powershell
```

```yaml
shell: cmd
```

Notes:

- `bash` is the default on Linux/macOS
- `powershell` is the default on Windows
- `cmd` must be selected explicitly

### A safe command is flagged as risky

Use:

```bash
ollama-sgpt --shell --dry-run "your command request"
```

Then review the generated command manually. HIGH and CRITICAL confirmations are intentionally strict.

### Command not found during execution

The runtime can fail preflight when an external tool is missing. Install the missing tool first, then retry.

Example:

```text
Preflight check failed: missing command(s): 'nmap'.
```

Common example:

- install `nmap` before running prompts that generate `nmap` commands
- install `git` before prompts that generate Git commands
- install Docker Desktop before prompts that generate `docker` commands on Windows

If the missing command is `ollama`, install Ollama from `https://ollama.ai/download`, then start it with:

```bash
ollama serve
```

If you want the CLI to summarize setup issues in one place, run:

```bash
ollama-sgpt --doctor
```

---

## Session Problems

Sessions are stored in:

```text
~/.ollama-sgpt/sessions/
```

### Session not found

List sessions:

```bash
ollama-sgpt --list-sessions
```

### Session file is corrupted

Back it up and remove it:

```bash
cp ~/.ollama-sgpt/sessions/myproject.json ~/myproject.json.backup
rm ~/.ollama-sgpt/sessions/myproject.json
```

Then recreate it:

```bash
ollama-sgpt --session myproject "starting fresh"
```

### Permission problems with sessions

Check directory ownership and permissions:

```bash
ls -la ~/.ollama-sgpt/sessions/
```

---

## Configuration Problems

### Config file not loaded

Verify the file exists:

```bash
ls -la ~/.ollama_sgpt.yaml
```

Validate the YAML:

```bash
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path.home().joinpath('.ollama_sgpt.yaml').read_text())"
```

### Environment variable overrides do not work

That is expected in the current runtime.

Use:

- CLI flags such as `--model` and `--no-stream`
- the config file at `~/.ollama_sgpt.yaml`

Example:

```yaml
model: mistral
stream: false
shell: powershell
```

---

## Display Problems

### Unicode or emoji looks wrong

Use a terminal with UTF-8 support. On Windows, prefer Windows Terminal or a modern PowerShell host.

### Colors do not appear

Try a terminal that supports ANSI color output.

---

## When You Need More Detail

### Inspect Python-side errors

```bash
python -v -m ollama_sgpt "test"
```

### Check the installed package version

```bash
python -c "import ollama_sgpt; print(ollama_sgpt.__version__)"
```

### Save stderr output

```bash
python -m ollama_sgpt "test" 2>&1 | tee error.log
```

---

## Related Documentation

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Usage Guide](usage.md)
- [Session Guide](sessions.md)
- [Execution Safety Guide](execution.md)
