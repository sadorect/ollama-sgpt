# Session Management Guide

Complete guide to managing conversations with **ollama-sgpt** sessions.

---

## Table of Contents

- [What are Sessions?](#what-are-sessions)
- [Basic Session Operations](#basic-session-operations)
- [Session Use Cases](#session-use-cases)
- [Advanced Session Management](#advanced-session-management)
- [Best Practices](#best-practices)

---

## What are Sessions?

Sessions allow you to maintain **separate, persistent conversations** with the AI. Each session:

- **Maintains conversation history** - The AI remembers previous messages
- **Stored independently** - Different sessions don't interfere with each other
- **Persistent across invocations** - Resume conversations anytime
- **Named and organized** - Use descriptive names for different topics

### Why Use Sessions?

**Without sessions** (default):

```bash
ollama-sgpt "what is Python?"
ollama-sgpt "tell me more"
# AI doesn't remember the first question ❌
```

**With sessions:**

```bash
ollama-sgpt --session python-learning "what is Python?"
ollama-sgpt --session python-learning "tell me more"
# AI remembers context and continues conversation ✅
```

---

## Basic Session Operations

### Create/Use a Session

```bash
# Create or continue a session
ollama-sgpt --session myproject "how do I use Docker?"

# Short flag
ollama-sgpt -s myproject "explain containers"
```

**On first use:**

- Session is created automatically
- File stored in `~/.ollama_sgpt_sessions/myproject.json`

**On subsequent use:**

- Previous conversation is loaded
- AI has full context

### List All Sessions

```bash
ollama-sgpt --list-sessions
```

**Example output:**

```
┌──────────────┬─────────────────────┬─────────────────────┬──────────┐
│ Name         │ Created             │ Modified            │ Messages │
├──────────────┼─────────────────────┼─────────────────────┼──────────┤
│ python-help  │ 2026-02-15 09:30:00 │ 2026-02-17 14:22:00 │       24 │
│ devops       │ 2026-02-16 11:15:00 │ 2026-02-17 10:45:00 │       18 │
│ code-review  │ 2026-02-17 08:00:00 │ 2026-02-17 16:30:00 │       42 │
└──────────────┴─────────────────────┴─────────────────────┴──────────┘
```

### Delete a Session

```bash
ollama-sgpt --delete-session myproject
```

**Confirmation prompt:**

```
Delete session 'myproject'? [y/N]: y
Session 'myproject' deleted.
```

### Clear Session History

To restart a conversation while keeping the session name:

```bash
# Delete and recreate
ollama-sgpt --delete-session myproject
ollama-sgpt --session myproject "starting fresh"
```

---

## Session Use Cases

### 1. Project-Specific Assistance

Maintain context for different projects:

```bash
# Frontend project
ollama-sgpt -s webapp-frontend "how do I center a div?"
ollama-sgpt -s webapp-frontend "now make it responsive"

# Backend project
ollama-sgpt -s webapp-backend "explain REST API design"
ollama-sgpt -s webapp-backend "show me an example endpoint"
```

**Benefits:**

- AI understands project context
- No context mixing between projects
- Easy to resume project work

### 2. Learning Topics

Track learning progress:

```bash
# Python learning
ollama-sgpt -s learn-python "what are decorators?"
ollama-sgpt -s learn-python "show me an example"
ollama-sgpt -s learn-python "what about generators?"

# Docker learning
ollama-sgpt -s learn-docker "explain Dockerfile"
ollama-sgpt -s learn-docker "what's the difference from docker-compose?"
```

### 3. Code Review Sessions

Review code with persistent context:

```bash
ollama-sgpt -s review-auth-module \
  --context auth.py \
  "review this authentication code"

ollama-sgpt -s review-auth-module \
  --context tests/test_auth.py \
  "now review the tests"

ollama-sgpt -s review-auth-module \
  "summarize all issues found"
```

### 4. Troubleshooting

Debug issues incrementally:

```bash
ollama-sgpt -s bug-fix-123 \
  --context error.log \
  "analyze this error"

ollama-sgpt -s bug-fix-123 \
  "what could cause this?"

ollama-sgpt -s bug-fix-123 \
  "suggest a fix"

ollama-sgpt -s bug-fix-123 \
  --shell --execute "implement the fix"
```

### 5. Documentation Writing

Build documentation progressively:

```bash
ollama-sgpt -s docs-api "explain database schema"
ollama-sgpt -s docs-api "write API endpoint documentation"
ollama-sgpt -s docs-api "add authentication examples"
```

### 6. DevOps Tasks

Maintain infrastructure context:

```bash
ollama-sgpt -s prod-deployment "what's our deployment process?"
ollama-sgpt -s prod-deployment --shell "show server status"
ollama-sgpt -s prod-deployment "explain the monitoring setup"
```

---

## Advanced Session Management

### Session with Interactive Mode

Combine session persistence with REPL:

```bash
ollama-sgpt --session myproject

>>> what is Redis?
AI: Redis is an in-memory data structure store...

>>> show me an example
AI: Here's how to use Redis with Python...

>>> thank you
AI: You're welcome! Anything else?

>>> /exit
```

All conversation stored in `myproject` session.

### Multiple Sessions Workflow

Switch between sessions for different contexts:

```bash
# Morning: frontend work
ollama-sgpt -s frontend "implement dark mode"

# Afternoon: backend work
ollama-sgpt -s backend "optimize database queries"

# Evening: devops
ollama-sgpt -s deployment "update deployment scripts"

# Review all progress
ollama-sgpt --list-sessions
```

### Session with Code Execution

Combine all features:

```bash
ollama-sgpt --session automation \
  --shell \
  --execute \
  "create backup script for /var/log"

# Later, in the same session
ollama-sgpt --session automation \
  --execute \
  "now test the backup script"
```

### Team Collaboration

Share sessions with team members:

```bash
# Developer 1
ollama-sgpt -s team-code-review "review auth module"

# Export session
cp ~/.ollama_sgpt_sessions/team-code-review.json ~/shared/

# Developer 2
cp ~/shared/team-code-review.json ~/.ollama_sgpt_sessions/
ollama-sgpt -s team-code-review "I have additional concerns..."
```

---

## Session Storage

### Storage Location

```
~/.ollama_sgpt_sessions/
```

### File Format

Each session is a JSON file:

```
~/.ollama_sgpt_sessions/myproject.json
```

**Example structure:**

```json
{
  "name": "myproject",
  "created": "2026-02-17T10:30:00",
  "modified": "2026-02-17T14:45:00",
  "messages": [
    {
      "role": "user",
      "content": "what is Docker?"
    },
    {
      "role": "assistant",
      "content": "Docker is a platform..."
    }
  ]
}
```

### Managing Session Files

**Backup sessions:**

```bash
tar -czf sessions-backup-$(date +%Y%m%d).tar.gz \
  ~/.ollama_sgpt_sessions/
```

**Restore sessions:**

```bash
tar -xzf sessions-backup-20260217.tar.gz -C ~/
```

**Clean old sessions:**

```bash
# Delete sessions older than 30 days
find ~/.ollama_sgpt_sessions/ -name "*.json" -mtime +30 -delete
```

**View session content:**

```bash
cat ~/.ollama_sgpt_sessions/myproject.json | jq
```

---

## Best Practices

### 1. Use Descriptive Names

❌ Bad:

```bash
ollama-sgpt -s s1 "..."
ollama-sgpt -s temp "..."
ollama-sgpt -s asdf "..."
```

✅ Good:

```bash
ollama-sgpt -s webapp-frontend "..."
ollama-sgpt -s bug-fix-authentication "..."
ollama-sgpt -s learn-kubernetes "..."
```

### 2. One Session Per Context

Keep topics separate:

```bash
# ❌ Bad: mixing topics
ollama-sgpt -s general "how do I use Docker?"
ollama-sgpt -s general "explain Python decorators"
ollama-sgpt -s general "what's the weather?"

# ✅ Good: separate sessions
ollama-sgpt -s learn-docker "how do I use Docker?"
ollama-sgpt -s learn-python "explain Python decorators"
ollama-sgpt -s daily-tasks "what's the weather?"
```

### 3. Clean Up Regularly

Delete completed sessions:

```bash
# List all sessions
ollama-sgpt --list-sessions

# Delete completed ones
ollama-sgpt --delete-session bug-fix-123
ollama-sgpt --delete-session feature-complete
```

### 4. Use Sessions for Long Conversations

**One-off questions** - No session needed:

```bash
ollama-sgpt "what is the capital of France?"
```

**Multi-turn conversations** - Use sessions:

```bash
ollama-sgpt -s travel-planning "best time to visit Paris?"
ollama-sgpt -s travel-planning "what about accommodations?"
ollama-sgpt -s travel-planning "recommend restaurants"
```

### 5. Combine with Context

Use sessions with file context for comprehensive analysis:

```bash
ollama-sgpt -s code-review \
  --context src/main.py \
  "review this code"

ollama-sgpt -s code-review \
  --context src/utils.py \
  "now review utilities"

ollama-sgpt -s code-review \
  "summarize all findings"
```

### 6. Leverage Session History

Use `/history` in interactive mode:

```bash
ollama-sgpt -s myproject

>>> /history
1. User: what is Docker?
2. Assistant: Docker is a platform...
3. User: show me an example
4. Assistant: Here's a Dockerfile...
```

---

## Session Naming Conventions

### Recommended Patterns

**By project:**

- `project-feature-auth`
- `webapp-frontend-redesign`
- `api-v2-development`

**By task type:**

- `bug-fix-issue-123`
- `feature-user-dashboard`
- `refactor-database-layer`

**By topic:**

- `learn-kubernetes`
- `study-algorithms`
- `training-git-advanced`

**By date (for temporary):**

- `work-2026-02-17`
- `daily-2026-02-17`
- `temp-20260217`

### Avoid These Patterns

❌ Too generic:

- `test`
- `temp`
- `aaa`
- `session1`

❌ Too long:

- `webapp-frontend-redesign-user-dashboard-authentication-module`

✅ Sweet spot:

- `webapp-frontend`
- `redesign-auth`
- `user-dashboard`

---

## Session Troubleshooting

### Session Not Found

```bash
$ ollama-sgpt -s myproject "hello"
Error: Session 'myproject' not found
```

**Solution:** Session was likely deleted or not created yet. Just proceed - it will be created automatically.

### Can't Delete Session

```bash
$ ollama-sgpt --delete-session myproject
Error: Permission denied
```

**Solution:** Check file permissions:

```bash
ls -la ~/.ollama_sgpt_sessions/
chmod 644 ~/.ollama_sgpt_sessions/myproject.json
```

### Corrupted Session

```bash
Error: Failed to load session 'myproject'
```

**Solution:** Delete and recreate:

```bash
rm ~/.ollama_sgpt_sessions/myproject.json
ollama-sgpt -s myproject "starting fresh"
```

### Too Many Sessions

Performance impact with 100+ sessions.

**Solution:** Regular cleanup:

```bash
# List all
ollama-sgpt --list-sessions

# Delete old ones
find ~/.ollama_sgpt_sessions/ -name "*.json" -mtime +30 -delete
```

---

## Example Workflows

### Daily Development Workflow

```bash
# Morning standup prep
ollama-sgpt -s standup "summarize yesterday's work on auth module"

# Feature development
ollama-sgpt -s feature-payments "design payment flow"
ollama-sgpt -s feature-payments --code "implement payment handler"
ollama-sgpt -s feature-payments "what tests do we need?"

# Code review
ollama-sgpt -s review --context pr-changes.diff "review this PR"

# EOD cleanup
ollama-sgpt --list-sessions
ollama-sgpt --delete-session standup
```

### Learning Sprint

```bash
# Start learning topic
ollama-sgpt -s learn-k8s "what is Kubernetes?"
ollama-sgpt -s learn-k8s "explain pods"
ollama-sgpt -s learn-k8s "show deployment example"
ollama-sgpt -s learn-k8s --shell "install kubectl"

# Review progress later
ollama-sgpt -s learn-k8s "summarize what we've covered"
```

### Bug Investigation

```bash
# Initial investigation
ollama-sgpt -s bug-500-error \
  --context error.log \
  "analyze this 500 error"

# Deep dive
ollama-sgpt -s bug-500-error \
  --context api/handlers.py \
  "which code could cause this?"

# Fix implementation
ollama-sgpt -s bug-500-error \
  --shell --execute \
  "run unit tests"

# Verify
ollama-sgpt -s bug-500-error \
  "has this been fully fixed?"
```

---

## Related Documentation

- [Usage Guide](usage.md) - General usage instructions
- [Configuration Guide](configuration.md) - Configuration options
- [Execution Guide](execution.md) - Code execution safety
- [Troubleshooting](troubleshooting.md) - Solving common issues

---

**Organize your conversations effectively with sessions! 🎯**
