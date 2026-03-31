# Session Guide

`ollama-sgpt` supports named sessions so you can keep separate conversation histories for different tasks or projects.

---

## What Sessions Do

Sessions let you:

- continue a conversation over multiple commands
- isolate different work contexts
- keep project-specific history separate
- store a session-specific model preference
- inspect or export saved transcripts without contacting Ollama

Session files are stored in:

```text
~/.ollama-sgpt/sessions/
```

Each session is stored as a JSON file, for example:

```text
~/.ollama-sgpt/sessions/myproject.json
```

---

## Create Or Reuse A Session

```bash
ollama-sgpt --session myproject "how do I use Docker?"
```

Short form:

```bash
ollama-sgpt -s myproject "explain containers"
```

Behavior:

- if the session does not exist, it is created
- if it already exists, its previous messages are loaded

---

## Continue A Session

```bash
ollama-sgpt --session myproject "show me an example"
```

This keeps the conversation context from earlier messages in the same session.

---

## List Sessions

```bash
ollama-sgpt --list-sessions
```

The CLI shows:

- session name
- created timestamp
- modified timestamp
- message count

---

## Show A Saved Session

```bash
ollama-sgpt --show-session myproject
```

This prints the saved transcript from disk without sending a request to Ollama.

---

## Export A Saved Session

```bash
ollama-sgpt --export-session myproject --output transcript.md
```

Export notes:

- `.md`, `.txt`, and `.json` outputs are supported
- `--output` is required with `--export-session`
- export reads the saved transcript from disk and does not require Ollama to be running

---

## Delete A Session

```bash
ollama-sgpt --delete-session myproject
```

This removes the session file from the session directory.

---

## Set A Default Session

To make a session the default for later runs:

```bash
ollama-sgpt --default-session work
```

After that:

```bash
ollama-sgpt "continue where we left off"
```

The default session name is stored in `~/.ollama_sgpt.yaml`.

---

## Temporary Scratch Session

Use the reserved `temp` session name for an in-memory scratch conversation:

```bash
ollama-sgpt --session temp
```

Scratch session notes:

- `temp` is not persisted under `~/.ollama-sgpt/sessions/`
- it is useful for short-lived experiments you do not want to keep
- `temp` cannot be saved as the default session

---

## Sessions With Context

Combine sessions with context loading:

```bash
ollama-sgpt --session review --context app.py "suggest improvements"
```

This is useful when you want ongoing discussion about the same files or project.

---

## Sessions With Shell Mode

```bash
ollama-sgpt --session ops --shell "find the largest files in this directory"
```

With execution:

```bash
ollama-sgpt --session ops --shell --execute "show disk usage"
```

---

## REPL Session Preload

When you start interactive mode with a named session:

```bash
ollama-sgpt --session work
```

the REPL loads that session's prior messages before you type the next prompt. This makes interactive session resume match one-shot `--session NAME "..."` behavior.

---

## Session-Specific Model Choice

If you run a session with `--model`, the selected model can be stored with that session and reused later.

Example:

```bash
ollama-sgpt --session code --model codellama "review this module"
```

Later:

```bash
ollama-sgpt --session code "continue the review"
```

This allows different sessions to prefer different models.

---

## Managing Session Files

### Inspect The Session Directory

```bash
ls -la ~/.ollama-sgpt/sessions/
```

```powershell
Get-ChildItem $env:USERPROFILE\.ollama-sgpt\sessions
```

### Back Up A Session

```bash
cp ~/.ollama-sgpt/sessions/myproject.json ~/myproject.json.backup
```

### Remove A Session File Manually

```bash
rm ~/.ollama-sgpt/sessions/myproject.json
```

Use the CLI delete command when possible.

---

## Troubleshooting Sessions

### Session Not Found

Run:

```bash
ollama-sgpt --list-sessions
```

Then confirm the session name matches exactly.

If you want to inspect the saved transcript before resuming, use:

```bash
ollama-sgpt --show-session myproject
```

### Corrupted Session File

If a session file becomes invalid JSON, remove or restore it from backup:

```bash
cp ~/.ollama-sgpt/sessions/myproject.json ~/myproject.json.backup
rm ~/.ollama-sgpt/sessions/myproject.json
```

Then recreate it:

```bash
ollama-sgpt --session myproject "starting fresh"
```

### Permission Problems

Check ownership and permissions for the session directory:

```bash
ls -la ~/.ollama-sgpt/sessions/
```

---

## Related Documentation

- [Usage Guide](usage.md)
- [Configuration Guide](configuration.md)
- [Troubleshooting](troubleshooting.md)
