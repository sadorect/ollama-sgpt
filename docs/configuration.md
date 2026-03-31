# Configuration Guide

Complete guide to configuring **ollama-sgpt**.

---

## What The App Reads Today

The current release reads configuration from:

- command-line flags
- the config file at `~/.ollama_sgpt.yaml`
- built-in defaults

Environment variable overrides are **not** implemented in the current runtime. If you want to change behavior, use CLI flags or the config file.

Other local runtime state is stored under:

- `~/.ollama-sgpt/sessions/`
- `~/.ollama-sgpt/roles/`
- `~/.ollama-sgpt/cache/`

---

## Config File Location

**Linux/macOS**

```text
~/.ollama_sgpt.yaml
```

**Windows**

```text
C:\Users\<username>\.ollama_sgpt.yaml
```

Create the file if it does not exist:

```bash
# Linux/macOS
touch ~/.ollama_sgpt.yaml
```

```powershell
# Windows PowerShell
New-Item -Path $env:USERPROFILE\.ollama_sgpt.yaml -ItemType File -Force
```

Or let the CLI create the starter file and local state directories for you:

```bash
ollama-sgpt --init
```

---

## Current Default Configuration

These are the defaults used by the current codebase when no config file is present:

```yaml
model: llama3
ollama_url: http://localhost:11434/api/chat
history_file: ~/.ollama_sgpt_history.json
stream: true
shell: bash                # powershell on Windows
tools_enabled: false
default_session: null
request_timeout: 120
stream_idle_timeout: 60
```

Notes:

- On Windows, the default `shell` is `powershell`.
- On Linux and macOS, the default `shell` is `bash`.
- `cmd` is supported, but you must set `shell: cmd` in the config file.

---

## Configuration Options

| Option | Type | Default | What it does |
| --- | --- | --- | --- |
| `model` | string | `llama3` | Default Ollama model |
| `ollama_url` | string | `http://localhost:11434/api/chat` | Ollama chat endpoint |
| `history_file` | string | `~/.ollama_sgpt_history.json` | One-shot and non-session history file |
| `stream` | boolean | `true` | Enables streaming output |
| `shell` | string | `bash` or `powershell` by OS | Shell family used for `--shell` behavior |
| `tools_enabled` | boolean | `false` | Enables opt-in constrained local tools for `--tools` |
| `default_session` | string or `null` | `null` | Session name reused when `--session` is omitted |
| `request_timeout` | integer | `120` | HTTP timeout for standard chat requests |
| `stream_idle_timeout` | integer | `60` | Maximum idle time during streaming before error |

---

## Recommended Config Templates

### Minimal Setup

```yaml
model: llama3
```

### Linux/macOS Shell Setup

```yaml
model: llama3
shell: bash
stream: true
```

### Windows PowerShell Setup

```yaml
model: llama3
shell: powershell
stream: true
```

### Windows Command Prompt Setup

```yaml
model: llama3
shell: cmd
stream: true
```

### Code-Focused Setup

```yaml
model: codellama
shell: bash
stream: true
history_file: ~/.ollama_sgpt_history.json
```

### Remote Ollama Server

```yaml
model: mistral
ollama_url: http://192.168.1.100:11434/api/chat
shell: bash
stream: true
```

---

## How Settings Are Chosen

Settings are resolved in this order:

1. CLI flags
2. Session-specific model override, if a session stores one
3. Config file values
4. Built-in defaults

Examples:

- `--model` overrides the configured model
- `--no-stream` overrides `stream: true`
- a saved session model can override the config-file model for that session

---

## Shell Selection

`ollama-sgpt` does not currently expose a `--shell-type` CLI flag.

To choose the shell family used by `--shell`, set it in the config file:

```yaml
shell: powershell
```

Supported values:

- `bash`
- `powershell`
- `cmd`

Use the shell that matches the commands you want generated and executed.

---

## Session Storage

Session data is stored separately from the config file.

**Session directory**

```text
~/.ollama-sgpt/sessions/
```

Each session is stored as a JSON file inside that directory.

Examples:

- `~/.ollama-sgpt/sessions/work.json`
- `~/.ollama-sgpt/sessions/review.json`

---

## Practical Examples

### Use a Default Session

```yaml
model: llama3
default_session: work
```

Then:

```bash
ollama-sgpt "continue where we left off"
```

### Prefer Non-Streaming Output

```yaml
model: mistral
stream: false
```

### Increase Timeouts for Slower Models

```yaml
model: llama3
request_timeout: 180
stream_idle_timeout: 90
```

---

## Troubleshooting Configuration

If you want a quick health check of the current configuration plus local Ollama readiness, run:

```bash
ollama-sgpt --doctor
```

### Confirm The Config File Path

```bash
ls -la ~/.ollama_sgpt.yaml
```

```powershell
Get-Item $env:USERPROFILE\.ollama_sgpt.yaml
```

### Verify Your Installed Models

```bash
ollama list
```

### Verify The Ollama Endpoint

```bash
curl http://localhost:11434/api/version
```

```powershell
Invoke-WebRequest http://localhost:11434/api/version
```

### If You Need Different Shell Output

Edit the config file and change:

```yaml
shell: bash
```

to either:

```yaml
shell: powershell
```

or:

```yaml
shell: cmd
```

---

## Known Limitations

- Environment variable overrides are documented in some older references but are not active in the current runtime.
- Shell selection is config-driven today, not flag-driven.
- Session-specific configuration currently only affects selected fields such as model choice.

---

## Related Documentation

- [Installation Guide](installation.md)
- [Usage Guide](usage.md)
- [Execution Safety Guide](execution.md)
- [Troubleshooting](troubleshooting.md)
