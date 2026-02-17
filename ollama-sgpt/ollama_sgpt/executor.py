"""Code execution framework with safety checks."""
import subprocess
import re
import shlex
from typing import Tuple, List, Optional, Dict
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

        # Package management (removal)
        (r'\bapt\s+(remove|purge)', 'Removing system packages'),
        (r'\byum\s+remove', 'Removing system packages'),
        (r'\bdnf\s+remove', 'Removing system packages'),
        (r'\bpacman\s+-R', 'Removing system packages'),

        # System modifications
        (r'\b(reboot|shutdown|poweroff|init\s+0|init\s+6)\b', 'System power operations'),
        (r'\buserdel\b', 'Deleting user accounts'),
        (r'\bgroupdel\b', 'Deleting user groups'),
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

        # Process management
        (r'\bkill\s+', 'Killing processes'),
        (r'\bsudo\b', 'Running with elevated privileges'),
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

    def __init__(self, timeout: int = 30, auto_confirm: bool = False):
        """Initialize code executor.

        Args:
            timeout: Maximum execution time in seconds
            auto_confirm: Skip confirmation prompts (dangerous!)
        """
        self.timeout = timeout
        self.auto_confirm = auto_confirm

    def analyze_command(self, command: str) -> Tuple[RiskLevel, List[str]]:
        """Analyze command for dangerous patterns.

        Args:
            command: Shell command to analyze

        Returns:
            Tuple of (risk_level, list_of_warnings)
        """
        warnings = []
        risk_level = RiskLevel.LOW

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
        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)

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
        # Try to find code blocks first
        code_block_match = re.search(
            r'```(?:bash|sh|shell)?\n(.*?)\n```', response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Try to find inline code
        inline_match = re.search(r'`([^`]+)`', response)
        if inline_match:
            return inline_match.group(1).strip()

        # If response looks like a command (starts with common commands)
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Check if it looks like a command
                common_commands = ['ls', 'cd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep',
                                   'find', 'chmod', 'chown', 'tar', 'git', 'docker', 'npm',
                                   'python', 'pip', 'apt', 'yum', 'dnf', 'sudo', 'echo']
                first_word = line.split()[0] if line.split() else ''
                if first_word in common_commands or first_word.startswith('./'):
                    return line

        return None
