# ollama-sgpt

A local-first ShellGPT alternative powered by Ollama.

[![Tests](https://github.com/sadorect/ollama-sgpt/actions/workflows/test.yml/badge.svg)](https://github.com/sadorect/ollama-sgpt/actions/workflows/test.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/sadorect/ollama-sgpt/releases)

## Why ollama-sgpt?

`ollama-sgpt` is designed for people who want AI help from the terminal without depending on a hosted API. It uses Ollama as the runtime, supports shell, code, and explain modes, and includes guardrails for command execution.

## Current Status

- Current package version: `0.2.0`
- Current package status: Alpha
- Current release target: `v0.3.0`

The active `v0.3` focus is:

- cross-platform shell correctness
- Windows safety parity for `--execute`
- install and configuration accuracy
- release-quality CI and validation

Planning documents:

- [Deployment Roadmap](ollama-sgpt/docs/roadmap.md)
- [Release Tracker](ollama-sgpt/docs/release-tracker.md)

## Core Features

- Local-first chat with Ollama
- Streaming terminal output
- Specialized modes:
  - default chat
  - `--shell`
  - `--code`
  - `--explain`
- Multi-session management
- Context loading from files
- Interactive REPL with special commands
- Safe command execution with risk checks

## Supported Shells

`--shell` behavior depends on the configured `shell` value in `~/.ollama_sgpt.yaml`.

| Shell | Status | How selected | Notes |
| --- | --- | --- | --- |
| `bash` | Supported | Default on Linux/macOS or `shell: bash` | Recommended Unix-like path |
| `powershell` | Supported | Default on Windows or `shell: powershell` | Recommended Windows path |
| `cmd` | Supported | `shell: cmd` in config | Use when you want `cmd.exe` syntax |

Notes:

- There is no dedicated `--shell-type` CLI flag today.
- Shell selection is config-driven.
- `--shell` is intended to return command-only output for the configured shell family.
- Live streamed assistant replies are rendered once as they arrive and are not reprinted after the stream completes.

## Installation

### Recommended: `pipx`

```bash
pipx install ollama-sgpt
```

### Quickstart

```bash
ollama serve
ollama pull llama3
ollama-sgpt --init
ollama-sgpt --doctor
ollama-sgpt --version
ollama-sgpt "hello"
ollama-sgpt --shell "list python files recursively"
```

### Install From Source

From the repository root:

```bash
git clone https://github.com/sadorect/ollama-sgpt.git
cd ollama-sgpt/ollama-sgpt
pip install -e .
```

The package also exposes the shorter `sgpt` command as an alias.

See [Installation Guide](docs/installation.md) for platform-specific setup.

## Configuration

The current runtime reads configuration from:

- CLI flags
- `~/.ollama_sgpt.yaml`
- built-in defaults

Current default configuration:

```yaml
model: llama3
ollama_url: http://localhost:11434/api/chat
history_file: ~/.ollama_sgpt_history.json
stream: true
shell: bash                # powershell on Windows
default_session: null
request_timeout: 120
stream_idle_timeout: 60
```

Environment variable overrides are not implemented in the current runtime.

See [Configuration Guide](docs/configuration.md) for the full option list.

## Usage

### Basic Examples

```bash
ollama-sgpt "explain Docker containers"
ollama-sgpt --init
ollama-sgpt --doctor
ollama-sgpt --model mistral "summarize this error"
ollama-sgpt --role reviewer "review this patch"
ollama-sgpt --cache "summarize this error"
ollama-sgpt --tools "inspect the current git repo and summarize its status"
ollama-sgpt --code "write a Python function to reverse a string"
ollama-sgpt --explain "docker run -it ubuntu bash"
ollama-sgpt --describe-shell "Get-ChildItem -Recurse -Filter *.py"
ollama-sgpt --shell "list all Python files recursively"
ollama-sgpt --shell --stdout-only "list all Python files recursively"
```

### Sessions

```bash
ollama-sgpt --session myproject "how do I use git?"
ollama-sgpt --session myproject "show me an example"
ollama-sgpt --list-sessions
ollama-sgpt --default-session work
ollama-sgpt --show-session myproject
ollama-sgpt --export-session myproject --output transcript.md
ollama-sgpt --delete-session myproject
```

Session notes:

- named sessions are stored under `~/.ollama-sgpt/sessions/`
- `--default-session` stores a reusable session name in `~/.ollama_sgpt.yaml`
- `--show-session` prints a saved transcript without contacting Ollama
- `--export-session` writes a saved transcript to `.md`, `.txt`, or `.json`
- starting the REPL with `--session NAME` now preloads that session's prior messages
- `--session temp` starts an in-memory scratch session that is not saved to disk

### Custom Roles

```bash
ollama-sgpt --save-role reviewer --role-prompt "You are a meticulous code reviewer."
ollama-sgpt --list-roles
ollama-sgpt --show-role reviewer
ollama-sgpt --role reviewer "review this patch"
ollama-sgpt --delete-role reviewer
```

Custom role notes:

- custom roles are stored under `~/.ollama-sgpt/roles/`
- `--role NAME` is for saved custom roles only
- built-in shell/code/explain behavior still uses the dedicated mode flags
- `--delete-role NAME` removes a saved custom role

### Local Cache

```bash
ollama-sgpt --cache "summarize this error"
ollama-sgpt --show-cache
ollama-sgpt --clear-cache
```

Cache notes:

- caching is opt-in per request
- cached responses are stored locally under `~/.ollama-sgpt/cache/`
- cache management commands do not require Ollama to be running
- cached responses are generation-only and are not used with `--execute` or `--dry-run`

### Local Tools

```bash
ollama-sgpt --tools "inspect the current git repo and summarize its status"
```

Tool notes:

- local tools are disabled by default and require `tools_enabled: true` in `~/.ollama_sgpt.yaml`
- the initial tool set is read-only and currently covers file listing, file reading, git status/log, process listing, and system info
- tool usage is logged visibly during the run and in saved sessions

### Context Loading

```bash
ollama-sgpt --context app.py "explain this code"
ollama-sgpt --context main.py --context utils.py "review this code"
```

### Setup And Diagnostics

```bash
ollama-sgpt --init
ollama-sgpt --doctor
```

Setup notes:

- `--init` creates `~/.ollama_sgpt.yaml` if it does not already exist
- `--init` also prepares local state directories for sessions, roles, and cache entries
- `--doctor` inspects the current config, shell setting, Ollama CLI availability, API reachability, and configured model readiness
- `--doctor` exits nonzero when it finds blocking setup problems

### Interactive Mode

```bash
ollama-sgpt
ollama-sgpt --session work
ollama-sgpt --session temp
ollama-sgpt --shell --execute
```

Special REPL commands:

- `/help`
- `/clear`
- `/history`
- `/exit`

Multi-line input is submitted with `Esc+Enter`.

## Safe Execution

Execution is intended for shell mode:

```bash
ollama-sgpt --shell --execute "show disk usage"
ollama-sgpt --shell --dry-run "delete old log files"
ollama-sgpt --shell --execute --yes "create backup directory"
```

For shell piping or clipboard workflows:

```bash
ollama-sgpt --shell --stdout-only "list all Python files recursively"
```

Risk levels:

- LOW: default-yes confirmation
- MEDIUM: default-no confirmation
- HIGH: requires `yes`
- CRITICAL: requires `yes I understand`

`--yes` only auto-confirms LOW and MEDIUM risk commands.

See [Execution Safety Guide](docs/execution.md) for details.

## Shell Helpers

You can print opt-in shell helper snippets for supported interactive shells:

```bash
ollama-sgpt --shell-integration bash
ollama-sgpt --shell-integration zsh
ollama-sgpt --shell-integration powershell
```

The helper snippets wrap normal `ollama-sgpt` CLI calls, so they do not bypass the existing shell extraction or execution guardrails.

## Benchmarks

The `v0.3` release now includes a committed shell-quality baseline under [benchmarks/](benchmarks/README.md).

- Deterministic shell extraction fixtures: `4/4` passed
- Deterministic safety fixtures: `9/9` exact matches, `0` false positives, `0` false negatives
- Live shell-generation baseline on `2026-03-31`: `gpt-oss:20b` and `qwen3-coder:30b` both scored `6/6`

See [benchmarks/README.md](benchmarks/README.md) for the runner, suite definition, and current baseline JSON.

## Development

### Setup

```bash
git clone https://github.com/sadorect/ollama-sgpt.git
cd ollama-sgpt/ollama-sgpt
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Common Commands

```bash
pytest
ruff check ollama_sgpt
black ollama_sgpt tests
mypy ollama_sgpt
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [Usage Guide](docs/usage.md)
- [Execution Safety Guide](docs/execution.md)
- [Session Guide](docs/sessions.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Workflow examples](examples/workflows/)
- [Session examples](examples/sessions/)
- [Configuration examples](examples/configs/)

## License

MIT. See [LICENSE](LICENSE).
