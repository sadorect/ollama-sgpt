# Code Execution Safety Guide

Complete guide to safely executing AI-generated commands with **ollama-sgpt**.

---

## Table of Contents

- [Overview](#overview)
- [Risk Levels](#risk-levels)
- [Execution Modes](#execution-modes)
- [Risk Analysis](#risk-analysis)
- [Safety Features](#safety-features)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

**ollama-sgpt** can execute AI-generated shell commands with built-in **safety checks** to prevent dangerous operations.

### Supported Shell Families

Execution behavior follows the configured `shell` value in `~/.ollama_sgpt.yaml`.

| Shell | Status | Typical use |
| --- | --- | --- |
| `bash` | Supported | Default on Linux/macOS |
| `powershell` | Supported | Default on Windows |
| `cmd` | Supported | Use when you want `cmd.exe` command syntax |

Notes:

- `bash` is the default on Linux and macOS.
- `powershell` is the default on Windows.
- `cmd` must be selected explicitly in the config file:

```yaml
shell: cmd
```

- `--shell --execute` is only as safe and correct as the configured shell family, so keep docs, config, and expectations aligned.

### Key Features

✅ **4-tier risk assessment** (LOW, MEDIUM, HIGH, CRITICAL)
✅ **30+ dangerous pattern detection**
✅ **Syntax-highlighted command preview**
✅ **Risk-appropriate confirmation prompts**
✅ **Execution timeout protection**
✅ **Dry-run mode for testing**

### Warning

⚠️ **Never use `--yes` flag blindly!**
⚠️ **Always review commands before execution**
⚠️ **Understand what commands do before confirming**

---

## Risk Levels

### LOW - Read Operations

**Characteristics:**

- Read-only operations
- No system modifications
- Safe for auto-confirmation

**Examples:**

```bash
ls -la
cat file.txt
grep "error" log.txt
pwd
df -h
ps aux
git status
```

**Confirmation:**

```
Execute this command? [Y/n]:
```

Default: **Yes** (just press Enter)

---

### MEDIUM - File Operations

**Characteristics:**

- File creation/modification
- Package installation
- Network requests
- Requires explicit confirmation

**Examples:**

```bash
cp file.txt backup.txt
mv oldname.txt newname.txt
curl https://api.example.com
pip install requests
apt install vim
sudo systemctl restart nginx
```

**Confirmation:**

```
Execute this command? [y/N]:
```

Default: **No** (must type 'y')

---

### HIGH - Destructive Operations

**Characteristics:**

- File deletion
- Process killing
- Permission changes
- Requires typing "yes"

**Examples:**

```bash
rm -f important.txt
rm -r directory/
killall -9 process
chmod 777 file.sh
chown -R root:root /path
curl http://site.com | bash
apt remove package
```

**Confirmation:**

```
⚠️  HIGH RISK: Forced file deletion
Type 'yes' to confirm:
```

Must type: **"yes"** (exact match)

---

### CRITICAL - Catastrophic Operations

**Characteristics:**

- Recursive forced deletion
- Disk operations
- System-wide changes
- Requires full acknowledgment

**Examples:**

```bash
rm -rf /
rm -rf *
dd if=/dev/zero of=/dev/sda
mkfs.ext4 /dev/sda1
fdisk /dev/sda
```

**Confirmation:**

```
🚨 CRITICAL: Recursive forced file deletion
Type 'yes I understand' to confirm:
```

Must type: **"yes I understand"** (exact match)

---

## Execution Modes

### Standard Preview Mode

Review before execution:

```bash
ollama-sgpt --shell --execute "list log files"
```

**Flow:**

1. AI generates command
2. Command is analyzed for risk
3. Preview shown with syntax highlighting
4. User confirms or rejects
5. Command executed if confirmed

---

### Auto-Confirm Mode

Skip confirmation for LOW and MEDIUM risk:

```bash
ollama-sgpt --shell --execute --yes "show disk space"
```

**Behavior:**

- ✅ **LOW** risk: Auto-executes
- ✅ **MEDIUM** risk: Auto-executes
- ❌ **HIGH** risk: Still requires "yes"
- ❌ **CRITICAL** risk: Still requires "yes I understand"

⚠️ **Use with caution!**

---

### Dry-Run Mode

Preview commands without executing:

```bash
ollama-sgpt --shell --dry-run "delete old logs"
```

**Flow:**

1. AI generates command
2. Command is analyzed
3. Preview shown
4. **No execution** - exits immediately

**Use cases:**

- Testing AI responses
- Learning shell commands
- Auditing before running
- Script generation

---

## Risk Analysis

### Dangerous Pattern Detection

**ollama-sgpt** detects 30+ dangerous patterns:

#### CRITICAL Patterns

| Pattern           | Description                           |
| ----------------- | ------------------------------------- |
| `rm -rf`          | Recursive forced deletion             |
| `rm -fr`          | Recursive forced deletion (alternate) |
| `dd ... of=/dev/` | Writing to disk device                |
| `mkfs`            | Filesystem creation (data loss)       |
| `fdisk`           | Disk partitioning                     |
| `> /dev/sda`      | Direct disk writing                   |
| `rd` / `rmdir` with `/s /q` on `C:\` | Recursive drive-root deletion (cmd) |
| `del` / `erase` with `/s /q` on `C:\*` | Recursive forced root deletion (cmd) |
| `Remove-Item ... -Recurse -Force` on `C:\` or `C:\*` | Recursive root deletion (PowerShell) |
| `format` / `diskpart` | Disk operations (data loss) |

#### HIGH Patterns

| Pattern               | Description             |
| --------------------- | ----------------------- |
| `rm -f`               | Forced file deletion    |
| `rm -r`               | Recursive deletion      |
| `kill -9`             | Force killing processes |
| `killall`             | Kill all by name        |
| `chmod 777`           | Wide-open permissions   |
| `curl ... \| bash`    | Remote code execution   |
| `apt remove`          | Package removal         |
| `reboot` / `shutdown` | System power operations |
| `userdel`             | User account deletion   |
| `rd /s /q`            | Recursive deletion (cmd) |
| `del /s /q`           | Forced recursive deletion (cmd) |
| `powershell` / `pwsh` with `-EncodedCommand` | Encoded script execution |
| `Invoke-WebRequest ... \| iex` | Remote code execution (PowerShell) |
| `reg delete ... /f`   | Forced registry deletion |
| `reg add` / `reg import` | Registry modification |
| `netsh ...`           | Network configuration changes |
| `Stop-Computer` / `Restart-Computer` | System power operations |
| `taskkill /f` / `Stop-Process -Force` | Force killing processes |

#### MEDIUM Patterns

| Pattern           | Description                 |
| ----------------- | --------------------------- |
| `mv`              | Moving files                |
| `cp -r`           | Recursive copy              |
| `rm` (non-forced) | File deletion               |
| `curl` / `wget`   | Network operations          |
| `apt install`     | Package installation        |
| `pip install`     | Python package installation |
| `sudo`            | Elevated privileges         |
| `winget install`  | Windows package installation |
| `choco install`   | Chocolatey package installation |
| `Invoke-WebRequest` / `iwr` | Network operations |
| `taskkill` / `Stop-Process` | Process control |

#### LOW Patterns (Safe)

| Pattern                 | Operation             |
| ----------------------- | --------------------- |
| `ls`, `cat`, `grep`     | Read operations       |
| `pwd`, `whoami`, `date` | System info           |
| `df`, `du`, `ps`        | Status commands       |
| `git status`, `git log` | Version control reads |
| `netsh ... show ...`   | Read-only network queries |

---

## Safety Features

### 1. Command Preview

Before execution, see exactly what will run:

```
┌─ Command Preview [MEDIUM] ────────────────┐
│ sudo apt install vim                       │
└────────────────────────────────────────────┘

⚠️  MEDIUM RISK: Installing packages
Execute this command? [y/N]:
```

**Features:**

- Syntax highlighting
- Risk level indicator
- Color-coded border (green/yellow/red)
- Warning messages

### 2. Risk-Appropriate Confirmation

Confirmation difficulty scales with risk:

| Risk     | Confirmation            | Auto-confirm with `--yes`? |
| -------- | ----------------------- | -------------------------- |
| LOW      | Y/n                     | ✅ Yes                     |
| MEDIUM   | y/N                     | ✅ Yes                     |
| HIGH     | Type "yes"              | ❌ No                      |
| CRITICAL | Type "yes I understand" | ❌ No                      |

### 3. Execution Timeout

Commands timeout after 30 seconds (configurable):

```python
# In Python API
executor = CodeExecutor(timeout=60)
```

Prevents hanging processes.

### 4. Command Extraction

AI responses are parsed to extract commands from:

- Markdown code blocks: ` ```bash ... ``` `
- Inline code: `` `command` ``
- Plain text suggestions

### 5. Detailed Warnings

Specific warnings for detected patterns:

```
┌─ Command Preview [HIGH] ──────────────────┐
│ rm -f important.txt                        │
└────────────────────────────────────────────┘

⚠️  HIGH RISK: Forced file deletion

Type 'yes' to confirm:
```

---

## Best Practices

### 1. Always Review Commands

**Never blindly confirm!**

```bash
# ❌ Dangerous
ollama-sgpt --shell --execute --yes "clean up system"

# ✅ Safe
ollama-sgpt --shell --execute "clean up system"
# Review the command, then confirm
```

### 2. Use Dry-Run First

Test before executing:

```bash
# Step 1: Dry-run
ollama-sgpt --shell --dry-run "compress all logs"

# Step 2: Review output
# If command looks good...

# Step 3: Execute
ollama-sgpt --shell --execute "compress all logs"
```

### 3. Combine with Sessions

Track what was executed:

```bash
ollama-sgpt --session cleanup \
  --shell --execute \
  "remove old temp files"

# Later, review what was done
ollama-sgpt --session cleanup \
  "what commands did we run?"
```

### 4. Limit Scope

Be specific in prompts:

```bash
# ❌ Too broad
ollama-sgpt --shell --execute "delete old files"

# ✅ Specific
ollama-sgpt --shell --execute "delete .log files older than 30 days in /tmp"
```

### 5. Understand Before Executing

If you don't understand a command, **don't run it!**

```bash
# If unsure, ask first
ollama-sgpt "explain what 'dd if=/dev/zero of=...' does"

# Then decide if you should run it
```

### 6. Use Appropriate Flags

| Scenario            | Flags                     | Reason                      |
| ------------------- | ------------------------- | --------------------------- |
| Learning            | `--shell --dry-run`       | See commands without risk   |
| Interactive work    | `--shell --execute`       | Review each command         |
| Trusted automation  | `--shell --execute --yes` | Skip LOW/MEDIUM confirms    |
| Critical operations | `--shell --execute`       | Always review HIGH/CRITICAL |

---

## Examples

### Example 1: Safe Read Operation (LOW)

```bash
$ ollama-sgpt --shell --execute --yes "show disk usage"

AI: You can use `df -h` to display disk usage in human-readable format.

┌─ Command Preview [LOW] ───────────────────┐
│ df -h                                      │
└────────────────────────────────────────────┘

Auto-executing (LOW risk)...

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   60G   40G  60% /
/dev/sda2       500G  120G  380G  25% /home

✓ Command completed successfully in 0.05s
```

### Example 2: File Operation (MEDIUM)

```bash
$ ollama-sgpt --shell --execute "create a backup of config.yaml"

AI: You can copy the file to create a backup:

┌─ Command Preview [MEDIUM] ────────────────┐
│ cp config.yaml config.yaml.backup          │
└────────────────────────────────────────────┘

⚠️  MEDIUM RISK: File operations

Execute this command? [y/N]: y

Executing...
✓ Command completed successfully in 0.02s
```

### Example 3: Destructive Operation (HIGH)

```bash
$ ollama-sgpt --shell --execute "delete all .tmp files"

AI: To delete all .tmp files:

┌─ Command Preview [HIGH] ──────────────────┐
│ find . -name "*.tmp" -type f -delete       │
└────────────────────────────────────────────┘

⚠️  HIGH RISK: File deletion

Type 'yes' to confirm: yes

Executing...
✓ Command completed successfully in 0.15s
Deleted 23 files
```

### Example 4: Rejected Dangerous Command (CRITICAL)

```bash
$ ollama-sgpt --shell --execute "remove everything in this directory"

AI: To remove all files and directories:

┌─ Command Preview [CRITICAL] ──────────────┐
│ rm -rf *                                   │
└────────────────────────────────────────────┘

🚨 CRITICAL: Recursive forced file deletion

Type 'yes I understand' to confirm: no

✗ Execution cancelled by user
```

### Example 5: Dry-Run Mode

```bash
$ ollama-sgpt --shell --dry-run "compress logs"

AI: You can use tar to compress log files:

┌─ Command Preview [MEDIUM] ────────────────┐
│ tar -czf logs.tar.gz *.log                 │
└────────────────────────────────────────────┘

⚠️  MEDIUM RISK: Archive operations

[DRY RUN] Command would execute with confirmation
```

### Example 6: Interactive Session with Execution

```bash
$ ollama-sgpt --shell --execute --session cleanup

>>> find old log files

AI: Find logs older than 30 days:

┌─ Command Preview [LOW] ───────────────────┐
│ find /var/log -name "*.log" -mtime +30    │
└────────────────────────────────────────────┘

Execute? [Y/n]: y

/var/log/old-app.log
/var/log/error-2026-01.log

>>> now compress them

AI: Compress with tar:

┌─ Command Preview [MEDIUM] ────────────────┐
│ tar -czf old-logs.tar.gz /var/log/*.log   │
└────────────────────────────────────────────┘

Execute? [y/N]: y
✓ Compressed successfully
```

---

## Command Execution Results

After execution, you'll see:

```
✓ Command completed successfully in 0.12s
```

Or if failed:

```
✗ Command failed (exit code 1)
Error: permission denied
```

**Result includes:**

- Success/failure status
- Exit code
- Execution time
- stdout/stderr output
- Error messages (if any)

---

## Troubleshooting

### "Command not found"

```bash
✗ Command failed (exit code 127)
Error: bash: mycmd: command not found
```

**Solution:** Install missing command or check PATH.

### "Permission denied"

```bash
✗ Command failed (exit code 1)
Error: permission denied
```

**Solution:**

- Check file permissions
- Use `sudo` if appropriate
- Verify you have necessary access

### Timeout

```bash
✗ Command timed out after 30s
```

**Solution:** Increase timeout (requires API usage) or optimize command.

### False Positives

Sometimes safe commands are flagged:

```bash
# Safe but flagged as MEDIUM
sudo systemctl status nginx
```

**Solution:** Review and confirm if you know it's safe.

---

## Security Considerations

### What Execution DOES Protect Against

✅ Accidental `rm -rf /`
✅ Unintended disk formatting
✅ Recursive forced deletions
✅ Blind execution of dangerous commands

### What Execution DOES NOT Protect Against

❌ Malicious AI responses (trust your model)
❌ Complex command chains hiding danger
❌ Social engineering attacks
❌ Execution after insufficient review

### Recommendations

1. **Use trusted models** - Only use Ollama models you trust
2. **Understand commands** - Don't execute what you don't understand
3. **Test in safe environments** - Use VMs or containers for testing
4. **Review session history** - Check what was executed
5. **Backup important data** - Before running HIGH/CRITICAL operations

---

## Related Documentation

- [Usage Guide](usage.md) - General usage instructions
- [Configuration Guide](configuration.md) - Configuration options
- [Session Guide](sessions.md) - Managing conversations
- [Troubleshooting](troubleshooting.md) - Solving common issues

---

**Execute safely! 🛡️**
