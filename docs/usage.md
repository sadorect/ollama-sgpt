# Usage Guide

This guide describes the current CLI behavior of **ollama-sgpt**.

---

## Basic Commands

### One-Shot Query

```bash
ollama-sgpt "explain Docker containers"
```

### Interactive Chat

```bash
ollama-sgpt
```

### Use A Specific Model

```bash
ollama-sgpt --model mistral "summarize this error"
```

### Disable Streaming

```bash
ollama-sgpt --no-stream "what is Python?"
```

### First-Time Setup

```bash
ollama-sgpt --init
ollama-sgpt --doctor
```

---

## Modes

### Default Mode

General assistant behavior:

```bash
ollama-sgpt "what is the capital of France?"
```

### Shell Mode

Generate a command for the configured shell family:

```bash
ollama-sgpt --shell "list all Python files recursively"
```

For plain stdout suitable for piping:

```bash
ollama-sgpt --shell --stdout-only "list all Python files recursively"
```

### Describe A Shell Command

Explain a shell command in plain language:

```bash
ollama-sgpt --describe-shell "Get-ChildItem -Recurse -Filter *.py"
```

### Code Mode

Generate code only:

```bash
ollama-sgpt --code "write a Python function to reverse a string"
```

### Explain Mode

Explain a command or concept:

```bash
ollama-sgpt --explain "docker run -it ubuntu bash"
```

---

## Supported Shells

`--shell` behavior depends on the configured `shell` value in `~/.ollama_sgpt.yaml`.

| Shell | Status | How it is selected | Notes |
| --- | --- | --- | --- |
| `bash` | Supported | Default on Linux/macOS or `shell: bash` | Best-tested path for Unix-like systems |
| `powershell` | Supported | Default on Windows or `shell: powershell` | Recommended Windows shell family |
| `cmd` | Supported | `shell: cmd` in config | Supported for command generation and extraction; use when you want `cmd.exe` syntax |

Important notes:

- There is no dedicated `--shell-type` flag today.
- Shell selection is config-driven.
- `--shell` is intended to return command-only output for the configured shell.
- `--stdout-only` is intended for pipe-friendly shell output without Rich formatting.
- Live streamed assistant replies are rendered once as they arrive and are not reprinted after the stream completes.

Example config:

```yaml
model: llama3
shell: powershell
```

---

## Role Behavior

| Mode | Purpose | Typical output |
| --- | --- | --- |
| default | General assistant | conversational response |
| `--shell` | Command generation | one executable command |
| `--code` | Code generation | code-only response |
| `--explain` | Explanations | prose explanation |

---

## Setup And Diagnostics

Prepare local config and state directories:

```bash
ollama-sgpt --init
```

Run a local readiness check:

```bash
ollama-sgpt --doctor
```

Important notes:

- `--init` creates `~/.ollama_sgpt.yaml` if it does not already exist
- `--init` also ensures the local sessions, roles, and cache directories exist
- `--doctor` reports the current config path, shell, endpoint, model, and local state directories
- `--doctor` checks whether the `ollama` CLI is on `PATH`, whether the API endpoint is reachable, and whether the configured model is installed
- `--doctor` exits with a nonzero status when blocking setup issues are found

---

## Custom Prompt Roles

Save a reusable local role:

```bash
ollama-sgpt --save-role reviewer --role-prompt "You are a meticulous code reviewer."
```

List available roles:

```bash
ollama-sgpt --list-roles
```

Show a built-in or saved role:

```bash
ollama-sgpt --show-role reviewer
ollama-sgpt --show-role shell
```

Use a saved custom role:

```bash
ollama-sgpt --role reviewer "review this patch"
```

Delete a saved custom role:

```bash
ollama-sgpt --delete-role reviewer
```

Important notes:

- saved custom roles are stored under `~/.ollama-sgpt/roles/`
- `--role NAME` is for saved custom roles only
- built-in shell/code/explain behavior still uses the dedicated mode flags
- custom roles can be combined with sessions and context loading
- `--delete-role NAME` only removes saved custom roles; built-in roles cannot be deleted

---

## Local Response Cache

Cache a one-shot response locally:

```bash
ollama-sgpt --cache "summarize this error"
```

Inspect or clear the cache:

```bash
ollama-sgpt --show-cache
ollama-sgpt --clear-cache
```

Important notes:

- caching is opt-in and local-only
- cached entries are stored under `~/.ollama-sgpt/cache/`
- cache hits can be served without contacting Ollama
- `--cache` currently supports one-shot requests only
- cached responses are not used with `--execute` or `--dry-run`

---

## Constrained Local Tools

Enable tools in config:

```yaml
tools_enabled: true
```

Then run a tool-assisted prompt:

```bash
ollama-sgpt --tools "inspect the current git repo and summarize its status"
```

Current tool set:

- `list_files`
- `read_file`
- `git_status`
- `git_log`
- `system_info`
- `list_processes`

Important notes:

- tool mode is opt-in and currently supports one-shot requests only
- the current tool set is read-only
- tool usage is printed during the run and recorded in saved sessions
- `--tools` does not bypass the existing shell execution safeguards because it does not expose direct execution tools

---

## Session Management

### Create Or Reuse A Session

```bash
ollama-sgpt --session myproject "how do I use git?"
```

### Continue A Session

```bash
ollama-sgpt --session myproject "show me an example"
```

### List Sessions

```bash
ollama-sgpt --list-sessions
```

### Show A Saved Session

```bash
ollama-sgpt --show-session myproject
```

### Export A Saved Session

```bash
ollama-sgpt --export-session myproject --output transcript.md
```

### Delete A Session

```bash
ollama-sgpt --delete-session myproject
```

### Set A Default Session

```bash
ollama-sgpt --default-session work
```

After that:

```bash
ollama-sgpt "continue where we left off"
```

Sessions are stored in:

```text
~/.ollama-sgpt/sessions/
```

Additional session notes:

- starting the REPL with `--session NAME` now preloads that session's prior messages
- `--show-session` prints a saved transcript without contacting Ollama
- `--export-session` writes a saved transcript to `.md`, `.txt`, or `.json`
- `--session temp` creates an in-memory scratch session that is not persisted

---

## Context Loading

Load file contents into the prompt:

```bash
ollama-sgpt --context app.py "explain this code"
```

Multiple files:

```bash
ollama-sgpt --context main.py --context utils.py "review this code"
```

With a session:

```bash
ollama-sgpt --session review --context src/handler.js "suggest improvements"
```

Use context for:

- code review
- configuration analysis
- bug triage
- documentation help

---

## Command Execution

Execution only makes sense with `--shell`.

### Preview And Execute

```bash
ollama-sgpt --shell --execute "show disk usage"
```

### Dry Run

```bash
ollama-sgpt --shell --dry-run "delete old log files"
```

### Auto-Confirm Safe Commands

```bash
ollama-sgpt --shell --execute --yes "create backup directory"
```

Execution notes:

- `--yes` only auto-confirms LOW and MEDIUM risk commands
- HIGH and CRITICAL commands still require manual confirmation
- the generated command is analyzed before execution
- `--stdout-only` is generation-only and cannot be combined with execution flags

See [Execution Safety Guide](execution.md) for full details.

---

## Shell Integration Helpers

Print an opt-in helper snippet for your shell:

```bash
ollama-sgpt --shell-integration bash
ollama-sgpt --shell-integration zsh
ollama-sgpt --shell-integration powershell
```

Notes:

- the snippets call back into `ollama-sgpt`; they do not bypass the execution guardrails
- `bash`, `zsh`, and PowerShell helper output is supported
- `cmd` remains supported for shell generation, but no dedicated shell helper snippet is provided

---

## Interactive Mode

Start an interactive session:

```bash
ollama-sgpt
```

With a session:

```bash
ollama-sgpt --session work
```

With an in-memory scratch session:

```bash
ollama-sgpt --session temp
```

With command execution:

```bash
ollama-sgpt --shell --execute
```

Special commands:

| Command | Meaning |
| --- | --- |
| `/help` | show REPL help |
| `/clear` | clear current history |
| `/history` | show conversation history |
| `/exit` or `/quit` | leave the REPL |

Multi-line input is submitted with `Esc+Enter`.

---

## Practical Workflows

### Development

```bash
ollama-sgpt --session myapp "how should I structure this package?"
ollama-sgpt --code "write tests for a login validator"
ollama-sgpt --context app.py "suggest improvements"
```

### Systems Work

```bash
ollama-sgpt --shell "find the largest files in this directory"
ollama-sgpt --shell --dry-run "delete .log files older than 30 days"
```

### Code Review

```bash
ollama-sgpt --session review --context src/main.py "find likely bugs"
```

---

## Current Configuration Surface

The runtime currently supports configuration through:

- CLI flags
- `~/.ollama_sgpt.yaml`

Environment variable overrides are not part of the current implementation.

Useful config fields:

```yaml
model: llama3
stream: true
shell: bash
default_session: null
request_timeout: 120
stream_idle_timeout: 60
```

See [Configuration Guide](configuration.md) for the full option list.

---

## Tips

### Be Specific

Better prompt:

```text
find all Python files modified in the last week
```

Worse prompt:

```text
help with files
```

### Use Dry-Run First

```bash
ollama-sgpt --shell --dry-run "delete old logs"
```

### Pick A Suitable Model

- `llama3` for general use
- `mistral` for faster responses
- `codellama` for code-heavy work

---

## Related Documentation

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Execution Safety Guide](execution.md)
- [Troubleshooting](troubleshooting.md)
