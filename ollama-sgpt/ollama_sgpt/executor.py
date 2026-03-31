"""Code execution framework with safety checks."""
import subprocess
import re
import shutil
from difflib import get_close_matches
from pathlib import Path
from typing import Tuple, List, Optional
from enum import Enum
from dataclasses import dataclass
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()


class RiskLevel(Enum):
    """Risk levels for command execution."""
    LOW = "low"           # Read-only operations
    MEDIUM = "medium"     # File creation, moves
    HIGH = "high"         # Deletions, system changes
    CRITICAL = "critical"  # Recursive deletions, disk ops


@dataclass
class ExecutionResult:
    """Result of command execution."""
    success: bool
    returncode: int
    stdout: str
    stderr: str
    command: str
    risk_level: RiskLevel
    execution_time: float = 0.0


class CodeExecutor:
    """Safe execution of shell commands with security checks."""

    SAFE_EXCEPTION_PATTERNS = [
        r'^\s*netsh\b[^|;&\n]*\bshow\b[^|;&\n]*$',
    ]

    # Dangerous patterns organized by risk level
    CRITICAL_PATTERNS = [
        # Recursive deletions
        (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force)',
         'Recursive forced file deletion'),
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r', 'Recursive forced file deletion'),

        # Disk operations
        (r'\bdd\s+.*of=/dev/', 'Writing directly to disk device'),
        (r'\bmkfs\b', 'Filesystem creation (data loss)'),
        (r'\bfdisk\b', 'Disk partitioning'),

        # System device manipulation
        (r'>\s*/dev/sd[a-z]', 'Writing to disk device'),
        (r'>\s*/dev/null', None),  # This one is safe, exclude

        # Moving critical directories
        (r'\bmv\s+.*?\s+/dev/null', None),  # Safe
        (r'\bmv\s+/\s+', 'Moving root directory'),

        # Windows recursive root deletion
        (r'\b(rd|rmdir)\b(?=[^\n]*/s\b)(?=[^\n]*/q\b)(?=[^\n]*["\']?[a-zA-Z]:\\(?:["\']|\s|$))',
         'Recursive deletion of drive root'),
        (r'\b(del|erase)\b(?=[^\n]*/[a-zA-Z]*s[a-zA-Z]*\b)(?=[^\n]*/[a-zA-Z]*q[a-zA-Z]*\b)(?=[^\n]*["\']?[a-zA-Z]:\\\*(?:["\']|\s|$))',
         'Recursive forced deletion under drive root'),
        (r'\bRemove-Item\b(?=[^\n]*-Recurse\b)(?=[^\n]*-Force\b)(?=[^\n]*["\']?[a-zA-Z]:\\\*(?:["\']|\s|$))',
         'Recursive forced deletion under drive root'),
        (r'\bRemove-Item\b(?=[^\n]*-Recurse\b)(?=[^\n]*-Force\b)(?=[^\n]*["\']?[a-zA-Z]:\\(?:["\']|\s|$))',
         'Recursive forced deletion of drive root'),

        # Windows disk operations
        (r'\bdiskpart\b', 'Disk operation (data loss risk)'),
        (r'(?<!-)\bformat\b(?!-)(?=[^\n]*\b[a-zA-Z]:)', 'Disk format operation (data loss risk)'),
    ]

    HIGH_RISK_PATTERNS = [
        # File deletion
        (r'\brm\s+(-[a-zA-Z]*f|-f\b|--force)', 'Forced file deletion'),
        (r'\brm\s+-[a-zA-Z]*r', 'Recursive deletion'),
        (r'\brmdir\b', 'Directory removal'),

        # Process killing
        (r'\bkill\s+-9', 'Force killing processes'),
        (r'\bkillall\b', 'Killing all processes by name'),
        (r'\bpkill\b', 'Pattern-based process killing'),

        # Permission changes
        (r'\bchmod\s+777', 'Setting wide-open permissions'),
        (r'\bchmod\s+-R\s+777', 'Recursive wide-open permissions'),
        (r'\bchown\s+-R\s+root', 'Changing ownership to root'),

        # Network downloads with execution
        (r'\bcurl\s+.*\|\s*(bash|sh|python)',
         'Downloading and executing remote code'),
        (r'\bwget\s+.*\|\s*(bash|sh|python)',
         'Downloading and executing remote code'),
        (r'\bInvoke-WebRequest\b[^\n]*\|\s*(iex|Invoke-Expression)\b',
         'Downloading and executing remote code'),
        (r'\biwr\b[^\n]*\|\s*(iex|Invoke-Expression)\b',
         'Downloading and executing remote code'),

        # Package management (removal)
        (r'\bapt\s+(remove|purge)', 'Removing system packages'),
        (r'\byum\s+remove', 'Removing system packages'),
        (r'\bdnf\s+remove', 'Removing system packages'),
        (r'\bpacman\s+-R', 'Removing system packages'),
        (r'\bwinget\s+uninstall\b', 'Removing system packages'),
        (r'\bchoco\s+uninstall\b', 'Removing system packages'),

        # System modifications
        (r'\b(reboot|shutdown|poweroff|init\s+0|init\s+6)\b', 'System power operations'),
        (r'\buserdel\b', 'Deleting user accounts'),
        (r'\bgroupdel\b', 'Deleting user groups'),
        (r'\b(Stop-Computer|Restart-Computer)\b', 'System power operations'),
        (r'\bRemove-Item\b(?=[^\n]*-Recurse\b)(?=[^\n]*-Force\b)',
         'Recursive forced deletion'),
        (r'\b(rd|rmdir)\b(?=[^\n]*/s\b)(?=[^\n]*/q\b)', 'Recursive forced directory deletion'),
        (r'\b(del|erase)\b(?=[^\n]*/[a-zA-Z]*s[a-zA-Z]*\b)(?=[^\n]*/[a-zA-Z]*q[a-zA-Z]*\b)',
         'Recursive forced file deletion'),
        (r'\b(powershell|powershell\.exe|pwsh|pwsh\.exe)\b[^\n]*-EncodedCommand\b',
         'Encoded PowerShell execution'),
        (r'\breg\s+delete\b[^\n]*/f\b', 'Registry deletion with force'),
        (r'\breg\s+(add|copy|import|load|restore)\b', 'Registry modification'),
        (r'\bnetsh\b', 'Network configuration changes'),
        (r'\btaskkill\b[^\n]*/f\b', 'Force killing processes'),
        (r'\bStop-Process\b(?=[^\n]*-Force\b)', 'Force killing processes'),
    ]

    MEDIUM_RISK_PATTERNS = [
        # File operations
        (r'\bmv\s+', 'Moving files'),
        (r'\bcp\s+-[a-zA-Z]*r', 'Recursive copy'),
        (r'\brm\s+(?!-)', 'File deletion'),

        # Archive operations
        (r'\btar\s+.*x', 'Extracting archive'),
        (r'\bunzip\b', 'Extracting archive'),
        (r'\bunrar\b', 'Extracting archive'),

        # Network operations
        (r'\bcurl\s+', 'Network request'),
        (r'\bwget\s+', 'Network download'),

        # Package installation
        (r'\bapt\s+install', 'Installing packages'),
        (r'\byum\s+install', 'Installing packages'),
        (r'\bpip\s+install', 'Installing Python packages'),
        (r'\bnpm\s+install', 'Installing Node packages'),
        (r'\bwinget\s+install\b', 'Installing packages'),
        (r'\bchoco\s+install\b', 'Installing packages'),

        # Process management
        (r'\bkill\s+', 'Killing processes'),
        (r'\bsudo\b', 'Running with elevated privileges'),
        (r'\btaskkill\b', 'Killing processes'),
        (r'\bStop-Process\b', 'Killing processes'),
        (r'\bStart-Process\b', 'Starting external process'),
        (r'\bInvoke-WebRequest\b', 'Network request'),
        (r'\biwr\b', 'Network request'),
    ]

    LOW_RISK_PATTERNS = [
        # Read operations
        (r'\b(ls|cat|less|more|head|tail|grep|find|locate)\b', None),
        (r'\b(pwd|whoami|date|uptime|uname)\b', None),
        (r'\b(echo|printf)\b', None),

        # Info commands
        (r'\b(df|du|free|top|htop|ps|netstat)\b', None),
        (r'\b(git\s+(status|log|diff|show))\b', None),
    ]

    def __init__(self, timeout: int = 30, auto_confirm: bool = False, shell_type: str = "bash"):
        """Initialize code executor.

        Args:
            timeout: Maximum execution time in seconds
            auto_confirm: Skip confirmation prompts (dangerous!)
            shell_type: Shell to use for execution (bash, powershell, cmd)
        """
        self.timeout = timeout
        self.auto_confirm = auto_confirm
        self.shell_type = shell_type

    def analyze_command(self, command: str) -> Tuple[RiskLevel, List[str]]:
        """Analyze command for dangerous patterns.

        Args:
            command: Shell command to analyze

        Returns:
            Tuple of (risk_level, list_of_warnings)
        """
        warnings = []
        risk_level = RiskLevel.LOW

        if self._is_safe_exception(command):
            return risk_level, warnings

        # Check critical patterns first
        for pattern, description in self.CRITICAL_PATTERNS:
            if description is None:  # Safe exception
                continue
            if re.search(pattern, command, re.IGNORECASE):
                warnings.append(f"⚠️  CRITICAL: {description}")
                risk_level = RiskLevel.CRITICAL

        # Check high risk patterns
        if risk_level != RiskLevel.CRITICAL:
            for pattern, description in self.HIGH_RISK_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    warnings.append(f"⚠️  HIGH RISK: {description}")
                    risk_level = RiskLevel.HIGH
                    break

        # Check medium risk patterns
        if risk_level == RiskLevel.LOW:
            for pattern, description in self.MEDIUM_RISK_PATTERNS:
                if description and re.search(pattern, command, re.IGNORECASE):
                    warnings.append(f"⚠️  MEDIUM RISK: {description}")
                    risk_level = RiskLevel.MEDIUM
                    break

        return risk_level, warnings

    def _is_safe_exception(self, command: str) -> bool:
        """Return True when the whole command matches a known safe exception."""
        return any(
            re.search(pattern, command, re.IGNORECASE)
            for pattern in self.SAFE_EXCEPTION_PATTERNS
        )

    def preview_command(self, command: str, risk_level: RiskLevel, warnings: List[str]):
        """Display command preview with syntax highlighting.

        Args:
            command: Command to preview
            risk_level: Risk level of command
            warnings: List of warning messages
        """
        # Color based on risk level
        risk_colors = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "bold red"
        }

        # Create syntax highlighted command
        syntax_language = "bash"
        if self.shell_type == "powershell":
            syntax_language = "powershell"
        elif self.shell_type == "cmd":
            syntax_language = "bat"

        syntax = Syntax(command, syntax_language, theme="monokai", line_numbers=False)

        # Create panel with risk indicator
        title = f"[{risk_colors[risk_level]}]Command Preview [{risk_level.value.upper()}][/]"
        panel = Panel(syntax, title=title,
                      border_style=risk_colors[risk_level])

        console.print()
        console.print(panel)

        # Show warnings
        if warnings:
            console.print()
            for warning in warnings:
                console.print(f"  {warning}")
            console.print()

    def confirm_execution(self, risk_level: RiskLevel) -> bool:
        """Ask user to confirm command execution.

        Args:
            risk_level: Risk level of command

        Returns:
            True if user confirms, False otherwise
        """
        if self.auto_confirm:
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                console.print(
                    "[yellow]⚠️  Auto-confirm is enabled, but this command is too dangerous![/]")
                console.print(
                    "[yellow]Manual confirmation required for high/critical risk commands.[/]")
            else:
                console.print(
                    "[dim]Auto-confirming (--yes flag enabled)[/dim]")
                return True

        # Prompt based on risk level
        if risk_level == RiskLevel.CRITICAL:
            console.print(
                "[bold red]⛔ CRITICAL RISK - This command could cause serious damage![/]")
            response = console.input(
                "[bold red]Type 'yes I understand' to execute: [/]")
            return response.strip().lower() == "yes i understand"

        elif risk_level == RiskLevel.HIGH:
            console.print(
                "[bold red]⚠️  HIGH RISK - This command could cause damage![/]")
            response = console.input(
                "[yellow]Type 'yes' to execute or 'no' to cancel: [/]")
            return response.strip().lower() == "yes"

        elif risk_level == RiskLevel.MEDIUM:
            response = console.input(
                "[yellow]Execute this command? [y/N]: [/]")
            return response.strip().lower() in ["y", "yes"]

        else:  # LOW risk
            response = console.input("Execute this command? [Y/n]: ")
            return response.strip().lower() in ["", "y", "yes"]

    def execute(self, command: str, dry_run: bool = False) -> ExecutionResult:
        """Execute a shell command with safety checks.

        Args:
            command: Command to execute
            dry_run: If True, only analyze but don't execute

        Returns:
            ExecutionResult with execution details
        """
        import time
        start_time = time.time()

        # Analyze command
        risk_level, warnings = self.analyze_command(command)

        # Preview command
        self.preview_command(command, risk_level, warnings)

        missing_commands = self._find_missing_commands(command)
        if missing_commands:
            message = self._build_missing_command_message(missing_commands)
            if dry_run:
                console.print(f"[yellow]{message}[/yellow]")
            else:
                console.print(f"[red]{message}[/red]")
                return ExecutionResult(
                    success=False,
                    returncode=-1,
                    stdout="",
                    stderr=message,
                    command=command,
                    risk_level=risk_level,
                    execution_time=time.time() - start_time
                )

        # Dry run mode
        if dry_run:
            console.print("[dim]Dry run mode - command not executed[/dim]")
            return ExecutionResult(
                success=True,
                returncode=0,
                stdout="",
                stderr="",
                command=command,
                risk_level=risk_level,
                execution_time=time.time() - start_time
            )

        # Confirm execution
        if not self.confirm_execution(risk_level):
            console.print("[yellow]Execution cancelled by user[/]")
            return ExecutionResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr="Cancelled by user",
                command=command,
                risk_level=risk_level,
                execution_time=time.time() - start_time
            )

        # Execute command
        try:
            console.print()
            console.print("[dim]Executing...[/dim]")

            if self.shell_type == "powershell":
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            elif self.shell_type == "cmd":
                result = subprocess.run(
                    ["cmd", "/c", command],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

            execution_time = time.time() - start_time

            # Display output
            if result.stdout:
                console.print(result.stdout)

            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")

            # Status message
            if result.returncode == 0:
                console.print(
                    f"[green]✓ Command completed successfully in {execution_time:.2f}s[/green]")
            else:
                console.print(
                    f"[red]✗ Command failed with exit code {result.returncode}[/red]")

            return ExecutionResult(
                success=result.returncode == 0,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=command,
                risk_level=risk_level,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            console.print(
                f"[red]✗ Command timed out after {self.timeout}s[/red]")
            return ExecutionResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {self.timeout}s",
                command=command,
                risk_level=risk_level,
                execution_time=self.timeout
            )

        except Exception as e:
            console.print(f"[red]✗ Execution error: {e}[/red]")
            return ExecutionResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=str(e),
                command=command,
                risk_level=risk_level,
                execution_time=time.time() - start_time
            )

    def extract_command_from_response(self, response: str) -> Optional[str]:
        """Extract shell command from AI response.

        Args:
            response: AI-generated response text

        Returns:
            Extracted command or None
        """
        # Try to find shell code blocks first
        code_blocks = re.finditer(
            r'```(?:bash|sh|shell|zsh|powershell|pwsh|ps1|cmd|bat|dosbatch)?\s*\n(.*?)\n```',
            response,
            re.DOTALL | re.IGNORECASE
        )
        for match in code_blocks:
            candidate = self._normalize_code_block(match.group(1))
            if candidate:
                return candidate

        # Try to find inline code
        inline_match = re.search(r'`([^`]+)`', response)
        if inline_match:
            candidate = self._normalize_command_line(inline_match.group(1))
            if candidate:
                return candidate

        # If response looks like a command (starts with common commands)
        common_commands = self._common_commands_for_shell()
        common_commands_lower = [cmd.lower() for cmd in common_commands]

        lines = response.strip().split('\n')
        fallback_candidate: Optional[str] = None
        for line in lines:
            candidate = self._normalize_command_line(line)
            if not candidate:
                continue

            first_word = candidate.split()[0] if candidate.split() else ''
            first_word_lower = first_word.lower()

            if first_word_lower in common_commands_lower:
                return candidate

            if self.shell_type == "powershell":
                if re.match(
                    r'^(Get|Set|New|Remove|Add|Clear|Copy|Move|Rename|Invoke|Start|Stop|Restart|Test|Select|Where|ForEach|Write)-',
                    first_word,
                    re.IGNORECASE,
                ):
                    return candidate

            if first_word.startswith('./') or first_word.startswith('.\\'):
                return candidate

            # Fallback for valid but uncommon CLI tools (e.g., nmap, ip).
            if self._looks_like_command(candidate):
                if fallback_candidate is None:
                    fallback_candidate = candidate

        return fallback_candidate

    def _normalize_code_block(self, block: str) -> str:
        """Normalize code-block content into executable shell text."""
        lines = []
        for line in block.splitlines():
            candidate = self._normalize_command_line(line)
            if candidate:
                lines.append(candidate)
        return "\n".join(lines).strip()

    def _normalize_command_line(self, line: str) -> str:
        """Normalize common line prefixes from model output."""
        candidate = line.strip()
        if not candidate or candidate.startswith('#'):
            return ""

        # Remove list and quote prefixes.
        candidate = re.sub(r'^\s*\d+[.)]\s*', '', candidate)
        candidate = re.sub(r'^\s*[-*]\s*', '', candidate)
        candidate = re.sub(r'^\s*>\s*', '', candidate)
        candidate = re.sub(r'^\s*(command|run)\s*:\s*', '', candidate, flags=re.IGNORECASE)

        # Remove common shell prompts.
        candidate = re.sub(r'^\s*PS\s+[^>]+>\s*', '', candidate, flags=re.IGNORECASE)
        candidate = re.sub(r'^\s*[A-Za-z]:\\[^>]*>\s*', '', candidate)
        # Strip Unix prompt prefix only when "$" is followed by whitespace.
        candidate = re.sub(r'^\s*\$\s+', '', candidate)

        candidate = candidate.strip().strip('`').strip()
        return candidate

    def _common_commands_for_shell(self) -> List[str]:
        """Return known common commands for the configured shell."""
        if self.shell_type == "powershell":
            return [
                'ls', 'dir', 'cd', 'pwd', 'mkdir', 'rm', 'mv', 'cp',
                'type', 'cat', 'select-string', 'findstr', 'get-childitem',
                'get-content', 'get-item', 'get-process', 'get-service',
                'get-date', 'git', 'docker', 'npm', 'python', 'pip',
                'echo', 'write-output', 'remove-item', 'invoke-webrequest',
                'iwr', 'netsh', 'reg', 'ipconfig', 'nmap', 'ping',
                'tracert', 'nslookup',
            ]
        if self.shell_type == "cmd":
            return [
                'dir', 'cd', 'mkdir', 'rmdir', 'del', 'copy', 'move',
                'type', 'findstr', 'where', 'echo', 'set', 'for', 'if',
                'git', 'docker', 'npm', 'python', 'pip', 'winget',
                'choco', 'netsh', 'reg', 'ipconfig', 'nmap', 'ping',
                'tracert', 'nslookup',
            ]
        return [
            'ls', 'cd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep',
            'find', 'chmod', 'chown', 'tar', 'git', 'docker', 'npm',
            'python', 'pip', 'apt', 'yum', 'dnf', 'sudo', 'echo',
            'sed', 'awk', 'curl', 'wget', 'ip', 'ifconfig', 'nmap',
            'ping', 'traceroute', 'nslookup',
        ]

    def _looks_like_command(self, line: str) -> bool:
        """Heuristic fallback for command-like single lines."""
        tokens = line.split()
        if len(tokens) < 2:
            return False

        first = tokens[0]
        if self.shell_type == "powershell" and first.startswith("$"):
            if not re.match(r'^\$[a-z_][a-z0-9_]*$', first, re.IGNORECASE):
                return False
        elif not re.match(r'^[a-z0-9_.-]+$', first):
            return False

        stopwords = {
            "run", "use", "execute", "first", "then", "next", "finally",
            "please", "try", "you", "your", "this", "that",
        }
        if first.lower() in stopwords:
            return False

        # Prefer lines with explicit command traits.
        if any(t.startswith("-") for t in tokens[1:]):
            return True
        if any(sym in line for sym in ["|", "&&", "||", ";", ">", "<", "$(", "`"]):
            return True
        if any(re.search(r'[/\\=*:$]', t) for t in tokens[1:]):
            return True

        return False

    def _find_missing_commands(self, command: str) -> List[str]:
        """Return missing external command names referenced in command text."""
        candidates = self._extract_command_candidates(command)
        missing: List[str] = []
        for candidate in candidates:
            if not self._is_command_available(candidate):
                missing.append(candidate)
        return missing

    def _extract_command_candidates(self, command: str) -> List[str]:
        """Extract likely executable names from command segments."""
        candidates: List[str] = []
        segments = re.split(r'\|\||&&|[|;&]', command)
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            parts = segment.split()
            if not parts:
                continue

            cmd = self._first_executable_token(parts)
            if not cmd or self._is_builtin_or_internal(cmd):
                continue

            normalized = cmd.strip().strip('"').strip("'")
            if normalized and normalized not in candidates:
                candidates.append(normalized)

        return candidates

    def _first_executable_token(self, parts: List[str]) -> str:
        """Find first token in a segment that likely represents command name."""
        idx = 0
        while idx < len(parts):
            token = parts[idx]

            if token.lower() in {"then", "do", "else", "fi", "done", "if", "for", "while", "in"}:
                idx += 1
                continue

            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', token):
                idx += 1
                continue

            # PowerShell assignment: $x = <command>
            if token.startswith("$") and idx + 2 < len(parts) and parts[idx + 1] == "=":
                idx += 2
                continue

            # Call operator in PowerShell: & "tool.exe"
            if token == "&" and idx + 1 < len(parts):
                idx += 1
                token = parts[idx]

            return token

        return ""

    def _is_builtin_or_internal(self, command_name: str) -> bool:
        """Return True when command should not be PATH-validated."""
        name = command_name.strip().strip('"').strip("'")
        lower = name.lower()
        if not lower:
            return True

        if name.startswith("./") or name.startswith(".\\"):
            return True

        if self.shell_type == "powershell":
            if lower.startswith("$"):
                return True
            # Cmdlet/function style commands are resolved by PowerShell.
            if "-" in name:
                return True
            powershell_builtins = {
                "cd", "dir", "echo", "ls", "cat", "pwd",
                "set-location", "push-location", "pop-location",
            }
            return lower in powershell_builtins

        if self.shell_type == "cmd":
            cmd_builtins = {
                "cd", "chdir", "dir", "echo", "set", "if", "for", "call",
                "rem", "cls", "copy", "move", "del", "rmdir", "md", "mkdir",
                "type", "ver",
            }
            return lower in cmd_builtins

        posix_builtins = {
            "cd", "echo", "test", "[", "alias", "export", "unset",
            "source", ".", "set", "readonly", "shift", "umask",
            "wait", "trap", "fg", "bg", "jobs",
        }
        return lower in posix_builtins

    def _is_command_available(self, command_name: str) -> bool:
        """Return True when executable exists in PATH or as a script path."""
        name = command_name.strip().strip('"').strip("'")
        if not name:
            return False

        if any(sep in name for sep in ["/", "\\"]):
            return Path(name).exists()

        return shutil.which(name) is not None

    def _build_missing_command_message(self, missing_commands: List[str]) -> str:
        """Build user-facing missing-command preflight message."""
        quoted = ", ".join(f"'{cmd}'" for cmd in missing_commands)
        suggestions = []
        hints = []
        for command_name in missing_commands:
            suggestion = self._suggest_command_name(command_name)
            if suggestion:
                suggestions.append(
                    f"Did you mean `{suggestion}` for `{command_name}`?"
                )

            hint = self._install_hint(command_name)
            if not hint and suggestion:
                hint = self._install_hint(suggestion)
            if hint:
                hints.append(hint)

        hints = [hint for hint in hints if hint]
        hints = list(dict.fromkeys(hints))
        suggestions = list(dict.fromkeys(suggestions))

        message = f"Preflight check failed: missing command(s): {quoted}."
        message += " Install the missing tool or adjust the prompt so the model uses commands available on this machine."
        if suggestions:
            message += " " + " ".join(suggestions)
        if hints:
            message += " " + " ".join(hints)
        return message

    def _suggest_command_name(self, command_name: str) -> Optional[str]:
        """Return a likely intended command name for a close typo."""
        normalized = command_name.strip().strip('"').strip("'").lower()
        if not normalized or len(normalized) < 3:
            return None

        if any(sep in normalized for sep in ["/", "\\"]):
            return None

        candidates = sorted(set(self._common_commands_for_shell()) | set(self._hintable_commands()))
        matches = get_close_matches(normalized, candidates, n=1, cutoff=0.75)
        return matches[0] if matches else None

    def _hintable_commands(self) -> List[str]:
        """Return commands that have explicit install guidance."""
        return ["ollama", "nmap", "git", "docker", "curl", "wget"]

    def _install_hint(self, command_name: str) -> str:
        """Return install hint for known external tools."""
        cmd = command_name.lower()
        if cmd == "ollama":
            return "Install Ollama from https://ollama.ai/download and start it with `ollama serve`."
        if cmd == "nmap":
            if self.shell_type in {"powershell", "cmd"}:
                return "Install nmap with: `winget install Insecure.Nmap` (or `choco install nmap`)."
            return "Install nmap with your package manager, e.g. `sudo apt install nmap`."
        if cmd == "git":
            if self.shell_type in {"powershell", "cmd"}:
                return "Install Git with: `winget install --id Git.Git -e` (or `choco install git`)."
            return "Install git with your package manager, e.g. `sudo apt install git`."
        if cmd == "docker":
            if self.shell_type in {"powershell", "cmd"}:
                return "Install Docker Desktop and make sure the `docker` CLI is on PATH."
            return "Install Docker and make sure the daemon is running."
        if cmd == "curl":
            if self.shell_type == "powershell":
                return "Use `Invoke-WebRequest` in PowerShell or install curl if you want the `curl` binary."
            return "Install curl with your package manager, e.g. `sudo apt install curl`."
        if cmd == "wget":
            if self.shell_type in {"powershell", "cmd"}:
                return "Install wget, or switch the command to `curl` / `Invoke-WebRequest`."
            return "Install wget with your package manager, e.g. `sudo apt install wget`."
        return ""
