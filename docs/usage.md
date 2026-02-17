# Usage Guide

Complete guide to using **ollama-sgpt** - your AI-powered shell assistant.

---

## Table of Contents

- [Basic Usage](#basic-usage)
- [Modes](#modes)
- [Role-Based Prompting](#role-based-prompting)
- [Session Management](#session-management)
- [Context Loading](#context-loading)
- [Code Execution](#code-execution)
- [Interactive Mode](#interactive-mode)
- [Advanced Usage](#advanced-usage)

---

## Basic Usage

### Simple Query

```bash
ollama-sgpt "how do I list files in Linux?"
```

### With Custom Model

```bash
ollama-sgpt "explain Docker containers" --model mistral
```

### Pipe Input

```bash
cat error.log | ollama-sgpt "explain this error"
```

### Disable Streaming

```bash
ollama-sgpt "what is Python?" --no-stream
```

---

## Modes

### Default Mode

General conversational AI:

```bash
ollama-sgpt "what is the capital of France?"
```

### Shell Mode

Get shell commands for tasks:

```bash
ollama-sgpt --shell "find all Python files"
# Output: find . -name "*.py"

ollama-sgpt --shell "compress this directory"
# Output: tar -czf directory.tar.gz directory/
```

### Code Mode

Get code examples and explanations:

```bash
ollama-sgpt --code "write a Python function to reverse a string"
```

### Explain Mode

Explain concepts clearly:

```bash
ollama-sgpt --explain "what is recursion?"
```

---

## Role-Based Prompting

Different roles provide specialized system prompts:

| Flag        | Purpose              | Example                     |
| ----------- | -------------------- | --------------------------- |
| `--shell`   | Shell commands       | "create a backup directory" |
| `--code`    | Code generation      | "write a sorting algorithm" |
| `--explain` | Clear explanations   | "explain binary search"     |
| _(none)_    | General conversation | "tell me a joke"            |

---

## Session Management

### Create/Use a Session

```bash
# Create or use existing session
ollama-sgpt --session myproject "how do I use git?"

# Continue the conversation
ollama-sgpt --session myproject "show me an example"
```

### List All Sessions

```bash
ollama-sgpt --list-sessions
```

**Output:**

```
┌─────────────┬─────────────────────┬─────────────────────┬──────────┐
│ Name        │ Created             │ Modified            │ Messages │
├─────────────┼─────────────────────┼─────────────────────┼──────────┤
│ myproject   │ 2026-02-17 10:30:00 │ 2026-02-17 11:45:00 │       12 │
│ work        │ 2026-02-16 09:15:00 │ 2026-02-17 08:20:00 │       28 │
└─────────────┴─────────────────────┴─────────────────────┴──────────┘
```

### Delete a Session

```bash
ollama-sgpt --delete-session myproject
```

**Use Cases for Sessions:**

- Per-project conversations
- Different topics/contexts
- Maintaining conversation history
- Isolating work contexts

---

## Context Loading

### Load Context from Files

```bash
# Single file
ollama-sgpt --context app.py "explain this code"

# Multiple files
ollama-sgpt --context main.py --context utils.py "review this code"

# With session
ollama-sgpt --session review --context src/*.py "find bugs"
```

**Example with Context:**

```bash
$ ollama-sgpt --context config.yaml "what is the database host?"

Loaded 1 context file(s):
  1. config.yaml (256 bytes)

AI Response: According to the configuration file, the database
host is set to "localhost" on port 5432...
```

**When to Use Context:**

- Code review
- Documentation generation
- Configuration analysis
- Multi-file queries

---

## Code Execution

### Enable Execution

```bash
# Preview and execute
ollama-sgpt --shell --execute "list all log files"

# With auto-confirm (safe commands only)
ollama-sgpt --shell --execute --yes "create backup directory"

# Dry-run (preview only)
ollama-sgpt --shell --dry-run "delete old logs"
```

### Execution Example

```bash
$ ollama-sgpt --shell --execute "show disk usage"

AI: You can use `df -h` to show disk usage in human-readable format.

┌─ Command Preview [LOW] ─────────────┐
│ df -h                                │
└──────────────────────────────────────┘

Execute this command? [Y/n]: y

Executing...
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   60G   40G  60% /
/dev/sda2       500G  120G  380G  25% /home

✓ Command completed successfully in 0.05s
```

### Safety Levels

| Risk         | Confirmation            | Examples                        |
| ------------ | ----------------------- | ------------------------------- |
| **LOW**      | Y/n (default yes)       | `ls`, `cat`, `grep`, `pwd`      |
| **MEDIUM**   | y/N (default no)        | `mv`, `cp -r`, `apt install`    |
| **HIGH**     | Type "yes"              | `rm -f`, `killall`, `chmod 777` |
| **CRITICAL** | Type "yes I understand" | `rm -rf`, `dd`, `mkfs`          |

**Important:**

- `--yes` flag only auto-confirms LOW and MEDIUM risk
- HIGH and CRITICAL always require manual confirmation
- See [Execution Safety Guide](execution.md) for details

---

## Interactive Mode

### Start Interactive Session

```bash
# Basic interactive mode
ollama-sgpt

# With session persistence
ollama-sgpt --session work

# With code execution
ollama-sgpt --shell --execute
```

### Special Commands

In interactive mode, use these commands:

| Command            | Purpose                    |
| ------------------ | -------------------------- |
| `/help`            | Show help                  |
| `/clear`           | Clear conversation history |
| `/history`         | Show all messages          |
| `/exit` or `/quit` | Exit REPL                  |

### Multi-line Input

Press **Esc+Enter** to submit multi-line input:

```
>>> def fibonacci(n):
... |    if n <= 1:
... |        return n
... |    return fibonacci(n-1) + fibonacci(n-2)
... [Press Esc+Enter]
```

### Interactive Example

```bash
$ ollama-sgpt --shell --execute --session devops

ollama-sgpt Interactive Mode
Multi-line input: Press Esc+Enter to submit
Commands: /help, /clear, /history, /exit
Command EXECUTION enabled

>>> find all Python files larger than 1MB

AI: You can use find with size parameter...

┌─ Command Preview [LOW] ─┐
│ find . -name "*.py" -size +1M │
└──────────────────────────────┘

Execute? [Y/n]: y
./large_model.py
./data_processor.py

>>> compress those files

AI: You can use tar to compress them...
[continues conversation with context]
```

---

## Advanced Usage

### Combining Features

```bash
# Session + Context + Execution
ollama-sgpt --session audit \
  --context server.log \
  --context access.log \
  --shell --execute \
  "analyze these logs and show errors"

# Multiple contexts with specific model
ollama-sgpt --context *.py \
  --model codellama \
  --code \
  "find security vulnerabilities"
```

### Environment Variables

```bash
# Set default model
export OLLAMA_MODEL=mistral

# Set Ollama URL
export OLLAMA_URL=http://remote-server:11434

ollama-sgpt "hello"
```

### Scripting

```bash
#!/bin/bash
# Automated code review script

for file in src/*.py; do
  echo "Reviewing $file..."
  ollama-sgpt --context "$file" \
    --session code-review \
    "analyze this file for issues" \
    >> review-report.md
done
```

### Output Redirection

```bash
# Save output
ollama-sgpt "explain Docker" > explanation.md

# Append to file
ollama-sgpt "what is Kubernetes" >> k8s-guide.md

# Process output
ollama-sgpt --shell "list files" | grep ".py"
```

---

## Common Workflows

### Development Workflow

```bash
# Start session for project
ollama-sgpt --session myapp

# Get command suggestions
ollama-sgpt --shell "run tests with coverage"

# Code generation
ollama-sgpt --code "write unit tests for user authentication"

# Code review
ollama-sgpt --context app.py "suggest improvements"
```

### System Administration

```bash
# Diagnose issues
cat /var/log/syslog | ollama-sgpt "find critical errors"

# Get fix commands
ollama-sgpt --shell --execute "check disk space"

# Configuration help
ollama-sgpt --context nginx.conf "explain this configuration"
```

### Data Analysis

```bash
# Analyze data
ollama-sgpt --context data.csv "what are the trends?"

# Generate scripts
ollama-sgpt --code "write Python script to clean this CSV"

# Execute analysis
ollama-sgpt --execute "analyze log patterns"
```

---

## Tips & Best Practices

### 1. Use Specific Prompts

❌ Bad: "help with files"
✅ Good: "how do I find all Python files modified in the last week?"

### 2. Leverage Sessions

Keep related conversations together:

```bash
ollama-sgpt --session project-x "initial question"
ollama-sgpt --session project-x "follow-up question"
```

### 3. Review Before Executing

Always review commands before execution:

```bash
# Use dry-run first
ollama-sgpt --shell --dry-run "delete old logs"

# Then execute if safe
ollama-sgpt --shell --execute "delete old logs"
```

### 4. Use Context for Accuracy

Provide files for better responses:

```bash
ollama-sgpt --context error.log "diagnose this error"
```

### 5. Choose the Right Model

- **llama2**: General purpose, balanced
- **mistral**: Faster, good for quick queries
- **codellama**: Best for code-related tasks

```bash
ollama-sgpt --model codellama --code "optimize this function"
```

---

## Keyboard Shortcuts

### Interactive Mode

- **Ctrl+C**: Cancel current input
- **Ctrl+D**: Exit (or type `/exit`)
- **Esc+Enter**: Submit multi-line input
- **Up/Down arrows**: Navigate command history
- **Ctrl+A**: Beginning of line
- **Ctrl+E**: End of line

---

## Getting Help

### CLI Help

```bash
ollama-sgpt --help
```

### Documentation

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Session Guide](sessions.md)
- [Execution Safety](execution.md)
- [Troubleshooting](troubleshooting.md)

### Support

- GitHub Issues: https://github.com/sadorect/ollama-sgpt/issues
- Discussions: https://github.com/sadorect/ollama-sgpt/discussions

---

**Happy prompting! 🚀**
