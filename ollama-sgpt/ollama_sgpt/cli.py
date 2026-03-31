import sys
import json
import argparse
import shutil
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from .config import load_config, update_config
from .history import load_history, save_history
from .ollama_client import stream_chat, chat, check_ollama_health, validate_model, list_models
from .roles import (
    get_role_prompt,
    roles_directory,
    list_custom_roles,
    save_custom_role,
    load_custom_role,
    get_display_role_prompt,
    delete_custom_role,
)
from .exceptions import OllamaConnectionError, OllamaModelError, SessionError
from .session import SessionManager
from .context import load_context_files, build_context_prompt, format_context_summary, validate_context_files
from .repl import interactive_loop_enhanced
from .executor import CodeExecutor
from .cache import (
    build_cache_key,
    get_cache_entry,
    save_cache_entry,
    list_cache_entries,
    clear_cache,
)
from .tool_runtime import execute_tool_workflow
from . import __version__

console = Console()
TEMP_SESSION_NAME = "temp"
SUPPORTED_SHELLS = {"bash", "powershell", "cmd"}
TROUBLESHOOTING_URL = (
    "https://github.com/sadorect/ollama-sgpt/blob/main/docs/troubleshooting.md"
)


def build_messages(system_prompt, history, user_input):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    return messages


def config_file_path() -> Path:
    """Return the canonical config file path."""
    return Path.home() / ".ollama_sgpt.yaml"


def app_state_root() -> Path:
    """Return the root directory used for local ollama-sgpt state."""
    return Path.home() / ".ollama-sgpt"


def runtime_directories() -> dict[str, Path]:
    """Return the local runtime directories used by the app."""
    root = app_state_root()
    return {
        "sessions": root / "sessions",
        "roles": root / "roles",
        "cache_entries": root / "cache" / "entries",
    }


def ensure_runtime_directories() -> tuple[dict[str, Path], list[Path]]:
    """Create the runtime directories if they do not exist."""
    directories = runtime_directories()
    created = []

    for path in directories.values():
        existed = path.exists()
        path.mkdir(parents=True, exist_ok=True)
        if not existed:
            created.append(path)

    return directories, created


def load_config_or_exit() -> dict:
    """Load config and convert config-file failures into a user-facing error."""
    try:
        return load_config()
    except ValueError as e:
        console.print(f"[bold red]Config error:[/bold red] {e}")
        console.print(f"[dim]Config file:[/dim] [cyan]{config_file_path()}[/cyan]")
        console.print(
            "[dim]Fix the file and retry, or move it aside and run:[/dim] "
            "[cyan]ollama-sgpt --init[/cyan]"
        )
        sys.exit(1)


def ollama_base_url(url: str) -> str:
    """Return the Ollama base URL without the chat path."""
    return url[:-9] if url.endswith("/api/chat") else url.rstrip("/")


def verify_endpoint_command(shell_type: str, url: str) -> str:
    """Return the right command to verify the Ollama API endpoint."""
    version_url = f"{ollama_base_url(url)}/api/version"
    if shell_type == "powershell":
        return f"Invoke-WebRequest {version_url}"
    return f"curl {version_url}"


def build_connection_diagnostics(config):
    """Build actionable connection troubleshooting details."""
    shell_type = config.get("shell", "bash")
    return {
        "runtime": [
            ("Endpoint", config["ollama_url"]),
            ("Shell", shell_type),
            ("Config file", str(config_file_path())),
        ],
        "steps": [
            ("Check the Ollama CLI", "ollama --version"),
            ("Start the Ollama service", "ollama serve"),
            ("Verify the API endpoint", verify_endpoint_command(shell_type, config["ollama_url"])),
            ("List installed models", "ollama list"),
        ],
    }


def build_model_diagnostics(config):
    """Build actionable model recovery details."""
    return {
        "runtime": [
            ("Requested model", config["model"]),
            ("Endpoint", config["ollama_url"]),
            ("Config file", str(config_file_path())),
        ],
        "steps": [
            ("Pull the requested model", f"ollama pull {config['model']}"),
            ("List installed models", "ollama list"),
            ("Temporarily override the model", 'ollama-sgpt --model mistral "hello"'),
        ],
    }


def render_diagnostics(title: str, diagnostics, error_message: str):
    """Render structured troubleshooting guidance."""
    console.print(f"\n[bold red]{title}[/bold red] {error_message}\n")
    console.print("[bold]Current Runtime:[/bold]")
    for label, value in diagnostics["runtime"]:
        console.print(f"  {label}: [cyan]{value}[/cyan]")
    console.print()
    console.print("[bold yellow]Troubleshooting Steps:[/bold yellow]")
    for index, (label, command) in enumerate(diagnostics["steps"], start=1):
        console.print(f"  {index}. [cyan]{label}:[/cyan]")
        console.print(f"     [dim]$[/dim] {command}")
        console.print()
    console.print(
        f"[dim]Need help?[/dim] See [link={TROUBLESHOOTING_URL}]troubleshooting guide[/link]"
    )


def make_doctor_check(name: str, status: str, details: str) -> dict:
    """Return a structured doctor check row."""
    return {"name": name, "status": status, "details": details}


def collect_doctor_report(config: dict) -> dict:
    """Collect a diagnostic report for the current runtime environment."""
    directories = runtime_directories()
    report = {
        "runtime": [
            ("Config file", str(config_file_path())),
            ("Endpoint", config["ollama_url"]),
            ("Model", config["model"]),
            ("Shell", config.get("shell", "bash")),
            ("Tools enabled", str(bool(config.get("tools_enabled", False))).lower()),
            ("Sessions dir", str(directories["sessions"])),
            ("Roles dir", str(directories["roles"])),
            ("Cache dir", str(directories["cache_entries"])),
        ],
        "checks": [],
        "next_steps": [],
    }

    config_exists = config_file_path().exists()
    if config_exists:
        report["checks"].append(
            make_doctor_check("Config file", "PASS", "Config file exists.")
        )
    else:
        report["checks"].append(
            make_doctor_check(
                "Config file",
                "WARN",
                "Config file is missing; runtime defaults will be used.",
            )
        )
        report["next_steps"].append("Create a starter config: ollama-sgpt --init")

    shell_type = config.get("shell", "bash")
    if shell_type in SUPPORTED_SHELLS:
        report["checks"].append(
            make_doctor_check("Shell setting", "PASS", f"Using supported shell '{shell_type}'.")
        )
    else:
        report["checks"].append(
            make_doctor_check(
                "Shell setting",
                "FAIL",
                f"Unsupported shell '{shell_type}'. Supported values: bash, powershell, cmd.",
            )
        )
        report["next_steps"].append(
            f"Set shell to bash, powershell, or cmd in {config_file_path()}"
        )

    ollama_path = shutil.which("ollama")
    if ollama_path:
        report["checks"].append(
            make_doctor_check("Ollama CLI", "PASS", f"Found at {ollama_path}.")
        )
    else:
        report["checks"].append(
            make_doctor_check("Ollama CLI", "FAIL", "The 'ollama' command is not on PATH.")
        )
        report["next_steps"].append("Install Ollama: https://ollama.ai/download")

    endpoint_ok = False
    try:
        check_ollama_health(config["ollama_url"])
        endpoint_ok = True
        report["checks"].append(
            make_doctor_check("Ollama API", "PASS", f"Reachable at {config['ollama_url']}.")
        )
    except OllamaConnectionError as e:
        report["checks"].append(
            make_doctor_check("Ollama API", "FAIL", str(e))
        )
        report["next_steps"].append("Start Ollama: ollama serve")
        report["next_steps"].append(
            f"Verify the API endpoint: {verify_endpoint_command(shell_type, config['ollama_url'])}"
        )

    available_models = []
    if endpoint_ok:
        try:
            available_models = sorted(
                model["name"]
                for model in list_models(config["ollama_url"])
                if isinstance(model, dict) and model.get("name")
            )
            if available_models:
                preview = ", ".join(available_models[:5])
                if len(available_models) > 5:
                    preview += ", ..."
                report["checks"].append(
                    make_doctor_check(
                        "Installed models",
                        "PASS",
                        f"{len(available_models)} model(s) available: {preview}",
                    )
                )
            else:
                report["checks"].append(
                    make_doctor_check(
                        "Installed models",
                        "FAIL",
                        "No local Ollama models are installed yet.",
                    )
                )
                report["next_steps"].append(f"Pull a local model: ollama pull {config['model']}")
        except OllamaConnectionError as e:
            report["checks"].append(
                make_doctor_check("Installed models", "FAIL", str(e))
            )

    if endpoint_ok:
        if available_models and config["model"] in available_models:
            report["checks"].append(
                make_doctor_check(
                    "Configured model",
                    "PASS",
                    f"Configured model '{config['model']}' is installed.",
                )
            )
        elif available_models:
            report["checks"].append(
                make_doctor_check(
                    "Configured model",
                    "FAIL",
                    f"Configured model '{config['model']}' is not installed.",
                )
            )
            report["next_steps"].append(f"Pull the configured model: ollama pull {config['model']}")
        else:
            report["checks"].append(
                make_doctor_check(
                    "Configured model",
                    "FAIL",
                    f"Configured model '{config['model']}' cannot be validated until a local model is installed.",
                )
            )
    else:
        report["checks"].append(
            make_doctor_check(
                "Configured model",
                "WARN",
                "Skipped model validation because the Ollama API is unreachable.",
            )
        )

    if config.get("tools_enabled", False):
        report["checks"].append(
            make_doctor_check("Local tools", "PASS", "Constrained local tools are enabled.")
        )
    else:
        report["checks"].append(
            make_doctor_check(
                "Local tools",
                "INFO",
                "Constrained local tools are disabled by default.",
            )
        )

    if not report["next_steps"]:
        report["next_steps"].extend(
            [
                'Try a simple prompt: ollama-sgpt "hello"',
                'Try shell mode: ollama-sgpt --shell "list python files recursively"',
            ]
        )

    unique_steps = []
    seen_steps = set()
    for step in report["next_steps"]:
        if step not in seen_steps:
            unique_steps.append(step)
            seen_steps.add(step)
    report["next_steps"] = unique_steps

    return report


def render_doctor_report(report: dict) -> int:
    """Render a doctor report and return the suggested exit code."""
    console.print("[bold]Doctor Runtime[/bold]")
    for label, value in report["runtime"]:
        console.print(f"  {label}: [cyan]{value}[/cyan]")
    console.print()

    table = Table(title="Doctor Checks", show_header=True)
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Details", style="white")

    style_map = {
        "PASS": "green",
        "WARN": "yellow",
        "FAIL": "red",
        "INFO": "cyan",
    }

    failures = 0
    warnings = 0
    for check in report["checks"]:
        status = check["status"]
        if status == "FAIL":
            failures += 1
        elif status == "WARN":
            warnings += 1

        table.add_row(
            check["name"],
            f"[{style_map.get(status, 'white')}]{status}[/{style_map.get(status, 'white')}]",
            check["details"],
        )

    console.print(table)
    console.print()

    console.print("[bold yellow]Recommended Next Steps:[/bold yellow]")
    for index, step in enumerate(report["next_steps"], start=1):
        console.print(f"  {index}. {step}")

    if failures:
        console.print(f"\n[bold red]Doctor found {failures} failing check(s).[/bold red]")
        return 1

    if warnings:
        console.print(f"\n[bold yellow]Doctor found {warnings} warning(s).[/bold yellow]")
        return 0

    console.print("\n[bold green]Doctor found no blocking issues.[/bold green]")
    return 0


def doctor_command(config: dict) -> int:
    """Run the diagnostic flow and return a process exit code."""
    return render_doctor_report(collect_doctor_report(config))


def validate_runtime(config):
    """Validate the Ollama endpoint and selected model."""
    try:
        check_ollama_health(config["ollama_url"])
        validate_model(config["ollama_url"], config["model"])
    except OllamaConnectionError as e:
        render_diagnostics(
            "Connection Error:",
            build_connection_diagnostics(config),
            str(e),
        )
        sys.exit(1)
    except OllamaModelError as e:
        render_diagnostics(
            "Model Error:",
            build_model_diagnostics(config),
            str(e),
        )
        sys.exit(1)


def interactive_loop(config, role):
    history = load_history(config["history_file"])
    console.print(f"[bold green]ollama-sgpt[/] — model: {config['model']}")
    console.print("Type 'exit' to quit\n")

    while True:
        try:
            user_input = console.input("[bold cyan]you> [/]").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            system_prompt = get_role_prompt(role, config.get("shell"))
            messages = build_messages(system_prompt, history, user_input)
            payload = {
                "model": config["model"],
                "messages": messages,
                "stream": config["stream"]
            }

            console.print("[bold magenta]ai> [/]", end="")
            response = stream_chat(
                config["ollama_url"],
                payload,
                request_timeout=config.get("request_timeout", 120),
                idle_timeout=config.get("stream_idle_timeout", 60)
            )

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            save_history(config["history_file"], history)

        except OllamaConnectionError as e:
            console.print(f"\n[bold red]Error:[/] {e}")
            console.print(
                "[yellow]Make sure Ollama is running: ollama serve[/]")
        except KeyboardInterrupt:
            console.print("\nbye 👋")
            break
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error:[/] {e}")


def list_sessions_command(session_manager):
    """Display all available sessions."""
    sessions = session_manager.list_sessions()

    if not sessions:
        console.print("[dim]No sessions found[/dim]")
        return

    table = Table(title="Available Sessions", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Created", style="green")
    table.add_column("Modified", style="yellow")
    table.add_column("Messages", justify="right", style="magenta")

    for session in sessions:
        table.add_row(
            session["name"],
            session["created"][:19] if len(
                session["created"]) > 19 else session["created"],
            session["modified"][:19] if len(
                session["modified"]) > 19 else session["modified"],
            str(session["messages"])
        )

    console.print(table)


def delete_session_command(session_manager, session_name):
    """Delete a session."""
    try:
        session_manager.delete_session(session_name)
        console.print(f"[green]Deleted session:[/green] {session_name}")
    except SessionError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def is_temp_session(session_name):
    """Return True when a session name should be treated as ephemeral."""
    return bool(session_name) and session_name.strip().lower() == TEMP_SESSION_NAME


def build_history_from_messages(messages_data):
    """Convert stored session messages into chat history payloads."""
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages_data
    ]


def load_session_history(session_manager, session_name):
    """Load chat history for a persisted session."""
    if not session_name or is_temp_session(session_name):
        return []
    return build_history_from_messages(session_manager.get_messages(session_name))


def build_session_text(session_data):
    """Return a plain-text transcript for terminal display or export."""
    messages = session_data.get("messages", [])
    config = session_data.get("config", {}) or {}
    lines = [
        f"Session: {session_data.get('name', 'unknown')}",
        f"Created: {session_data.get('created', 'unknown')}",
        f"Modified: {session_data.get('modified', 'unknown')}",
        f"Messages: {len(messages)}",
    ]

    if config:
        lines.append("")
        lines.append("Config:")
        for key, value in sorted(config.items()):
            lines.append(f"  {key}: {value}")

    if not messages:
        lines.append("")
        lines.append("No messages saved.")
        return "\n".join(lines)

    for index, message in enumerate(messages, start=1):
        role = str(message.get("role", "unknown")).title()
        timestamp = message.get("timestamp", "unknown")
        lines.append("")
        lines.append(f"{index}. {role} [{timestamp}]")
        lines.append(str(message.get("content", "")))

    return "\n".join(lines)


def build_session_markdown(session_data):
    """Return a Markdown transcript export for a saved session."""
    messages = session_data.get("messages", [])
    config = session_data.get("config", {}) or {}
    lines = [
        f"# Session: {session_data.get('name', 'unknown')}",
        "",
        f"- Created: `{session_data.get('created', 'unknown')}`",
        f"- Modified: `{session_data.get('modified', 'unknown')}`",
        f"- Messages: `{len(messages)}`",
    ]

    if config:
        lines.extend(["", "## Config", ""])
        for key, value in sorted(config.items()):
            lines.append(f"- `{key}`: `{value}`")

    if not messages:
        lines.extend(["", "_No messages saved._"])
        return "\n".join(lines) + "\n"

    for index, message in enumerate(messages, start=1):
        role = str(message.get("role", "unknown")).title()
        timestamp = message.get("timestamp", "unknown")
        lines.extend(
            [
                "",
                f"## {index}. {role}",
                "",
                f"- Timestamp: `{timestamp}`",
                "",
                str(message.get("content", "")),
            ]
        )

    return "\n".join(lines) + "\n"


def build_session_export(session_data, output_path: Path):
    """Return export content for a session based on the output extension."""
    suffix = output_path.suffix.lower()
    if suffix == ".json":
        return json.dumps(session_data, indent=2) + "\n"
    if suffix in {".md", ".markdown"}:
        return build_session_markdown(session_data)
    return build_session_text(session_data) + "\n"


def show_session_command(session_manager, session_name):
    """Display a saved session transcript."""
    if is_temp_session(session_name):
        console.print("[bold red]Error:[/bold red] Temporary sessions are in-memory only and cannot be shown after exit.")
        sys.exit(1)

    try:
        session_data = session_manager.load_session(session_name)
        console.print(build_session_text(session_data))
    except SessionError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def export_session_command(session_manager, session_name, output_path: Path):
    """Export a saved session transcript to disk."""
    if is_temp_session(session_name):
        console.print("[bold red]Error:[/bold red] Temporary sessions are in-memory only and cannot be exported.")
        sys.exit(1)

    try:
        session_data = session_manager.load_session(session_name)
        export_content = build_session_export(session_data, output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(export_content, encoding="utf-8")
        console.print(f"[green]Exported session:[/green] {session_name} -> {output_path}")
    except SessionError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def list_roles_command(shell_type: str):
    """Display built-in and custom roles."""
    table = Table(title="Available Roles", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")

    for name in ["default", "shell", "code", "explain"]:
        table.add_row(name, "builtin")

    for name in list_custom_roles(roles_directory()):
        table.add_row(name, "custom")

    console.print(table)


def show_role_command(role_name: str, shell_type: str):
    """Display the prompt text for a built-in or custom role."""
    try:
        console.print(get_display_role_prompt(role_name, shell_type, roles_directory()))
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def save_role_command(role_name: str, prompt_text: str):
    """Save a custom role prompt."""
    try:
        path = save_custom_role(role_name, prompt_text, roles_directory())
        console.print(f"[green]Saved role:[/green] {path.stem}")
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def delete_role_command(role_name: str):
    """Delete a custom role prompt."""
    try:
        delete_custom_role(role_name, roles_directory())
        console.print(f"[green]Deleted role:[/green] {role_name.strip().lower()}")
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def show_cache_command():
    """Display cache entry summaries."""
    entries = list_cache_entries()
    if not entries:
        console.print("[dim]No cached responses found[/dim]")
        return

    table = Table(title="Cached Responses", show_header=True)
    table.add_column("Updated", style="yellow")
    table.add_column("Model", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Hits", justify="right", style="magenta")
    table.add_column("Prompt", style="white")

    for entry in entries:
        table.add_row(
            str(entry.get("updated_at", ""))[:19],
            str(entry.get("model", "")),
            str(entry.get("role_name", "")),
            str(entry.get("hits", 0)),
            str(entry.get("prompt_preview", "")),
        )

    console.print(table)


def clear_cache_command():
    """Delete all cached responses."""
    removed = clear_cache()
    console.print(f"[green]Cleared cache entries:[/green] {removed}")


def init_command():
    """Prepare local config and runtime directories for first use."""
    config_path = config_file_path()
    config_created = not config_path.exists()
    directories, created_dirs = ensure_runtime_directories()

    if config_created:
        update_config({})

    config = load_config_or_exit()

    console.print("[bold green]Initialized ollama-sgpt[/bold green]")
    if config_created:
        console.print(f"  Config file created: [cyan]{config_path}[/cyan]")
    else:
        console.print(f"  Config file already exists: [cyan]{config_path}[/cyan]")

    if created_dirs:
        console.print("\n[bold]Created local state directories:[/bold]")
        for path in created_dirs:
            console.print(f"  - [cyan]{path}[/cyan]")
    else:
        console.print("\n[bold]Local state directories:[/bold]")
        for path in directories.values():
            console.print(f"  - [cyan]{path}[/cyan]")

    console.print("\n[bold]Current defaults:[/bold]")
    console.print(f"  Model: [cyan]{config['model']}[/cyan]")
    console.print(f"  Shell: [cyan]{config.get('shell', 'bash')}[/cyan]")
    console.print(f"  Endpoint: [cyan]{config['ollama_url']}[/cyan]")
    console.print(f"  Tools enabled: [cyan]{str(bool(config.get('tools_enabled', False))).lower()}[/cyan]")

    console.print("\n[bold yellow]Suggested next steps:[/bold yellow]")
    console.print("  1. Install Ollama if needed: https://ollama.ai/download")
    console.print("  2. Start Ollama: ollama serve")
    console.print(f"  3. Pull your model: ollama pull {config['model']}")
    console.print("  4. Run a full diagnostic: ollama-sgpt --doctor")
    console.print('  5. Try a prompt: ollama-sgpt "hello"')


def build_shell_description_prompt(command: str, shell_type: str) -> str:
    """Build a focused prompt for explaining a shell command."""
    shell_label = {
        "powershell": "PowerShell",
        "cmd": "cmd.exe",
    }.get(shell_type or "bash", "shell")
    return (
        f"Explain this {shell_label} command in clear, concise terms. "
        "Describe what it does, what the important flags mean, and any risky side effects.\n\n"
        f"{command}"
    )


def print_stdout_only(text: str):
    """Write plain text to stdout without Rich formatting."""
    output = text if text.endswith("\n") else f"{text}\n"
    sys.stdout.write(output)


def print_stderr_line(text: str):
    """Write a single plain-text line to stderr."""
    sys.stderr.write(f"{text}\n")


def build_shell_integration_script(shell_name: str) -> str:
    """Return an opt-in shell helper snippet for the requested shell."""
    if shell_name == "powershell":
        return """function Invoke-OllamaSgptCommand {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Prompt)
    ollama-sgpt --shell --stdout-only ($Prompt -join ' ')
}

function Invoke-OllamaSgptDescribe {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CommandText)
    ollama-sgpt --describe-shell ($CommandText -join ' ')
}

Set-Alias sgpt-command Invoke-OllamaSgptCommand
Set-Alias sgpt-describe Invoke-OllamaSgptDescribe
"""

    return """ollama_sgpt_command() {
  ollama-sgpt --shell --stdout-only "$*"
}

ollama_sgpt_describe() {
  ollama-sgpt --describe-shell "$*"
}
"""


def normalize_shell_response(response: str, shell_type: str) -> str:
    """Normalize shell-mode output to a single executable command."""
    extractor = CodeExecutor(shell_type=shell_type or "bash")
    command = extractor.extract_command_from_response(response)
    return command or ""


def render_response_output(response, role, config, stdout_only=False, already_streamed=False):
    """Render a response the same way for live and cached paths."""
    if role == "shell":
        if response:
            if stdout_only:
                print_stdout_only(response)
            else:
                console.print(response)
            return response
        if stdout_only:
            print_stderr_line("ERROR: Could not extract an executable command from the model output.")
        else:
            console.print(
                "[yellow]ERROR: Could not extract an executable command from the model output.[/yellow]"
            )
        return ""

    if config["stream"]:
        if already_streamed:
            return response
        console.print(response)
    else:
        console.print(Markdown(response))

    return response


def execute_chat(user_input, history, config, role, stdout_only=False, role_prompt=None):
    """Execute a chat request and return the response."""
    system_prompt = role_prompt or get_role_prompt(role, config.get("shell"))
    messages = build_messages(system_prompt, history, user_input)
    payload = {
        "model": config["model"],
        "messages": messages,
        "stream": config["stream"]
    }
    if config["stream"]:
        response = stream_chat(
            config["ollama_url"],
            payload,
            request_timeout=config.get("request_timeout", 120),
            idle_timeout=config.get("stream_idle_timeout", 60),
            echo=role != "shell",
        )
    else:
        response = chat(
            config["ollama_url"],
            payload,
            request_timeout=config.get("request_timeout", 120),
        )

    if role == "shell":
        response = normalize_shell_response(response, config.get("shell"))

    return render_response_output(
        response,
        role,
        config,
        stdout_only=stdout_only,
        already_streamed=config["stream"] and role != "shell",
    )


def main():
    parser = argparse.ArgumentParser(
        prog="ollama-sgpt",
        description="AI-powered shell assistant using Ollama",
        epilog="Examples:\n"
               "  %(prog)s 'how do I find large files?'\n"
               "  %(prog)s --shell 'compress all logs'\n"
               "  %(prog)s --code 'write a sorting function'\n"
               "  %(prog)s --session myproject 'continue discussion'\n"
               "  %(prog)s --session temp\n"
               "  %(prog)s --show-session myproject\n"
               "  %(prog)s --export-session myproject --output transcript.md\n"
               "  %(prog)s --context file.py 'review this code'\n"
               "  %(prog)s --shell --execute 'show disk usage'\n\n"
               "Documentation: https://github.com/sadorect/ollama-sgpt",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--version", "-v", action="version",
                        version=f"%(prog)s {__version__}")

    parser.add_argument("prompt", nargs="?",
                        help="your question or request (omit for interactive mode)")

    # Role/Mode selection
    mode_group = parser.add_argument_group("modes",
                                           "specialized prompting modes")
    mode_group.add_argument("--shell", action="store_true",
                            help="shell command mode - get executable commands")
    mode_group.add_argument("--code", action="store_true",
                            help="code generation mode - for programming tasks")
    mode_group.add_argument("--explain", action="store_true",
                            help="explanation mode - detailed explanations")
    mode_group.add_argument("--describe-shell", metavar="COMMAND",
                            help="explain a shell command in plain language")
    mode_group.add_argument("--role", metavar="NAME",
                            help="use a saved custom prompt role")
    mode_group.add_argument("--tools", action="store_true",
                            help="enable constrained local read-only tools (requires tools_enabled: true in config)")

    # Model configuration
    config_group = parser.add_argument_group("configuration",
                                             "model and output settings")
    config_group.add_argument("--model", metavar="NAME",
                              help="ollama model to use (default: from config)")
    config_group.add_argument("--no-stream", action="store_true",
                              help="disable streaming output")
    config_group.add_argument("--stdout-only", action="store_true",
                              help="print shell output to stdout without Rich formatting")
    config_group.add_argument("--shell-integration", choices=["bash", "zsh", "powershell"],
                              help="print an opt-in shell helper snippet and exit")
    config_group.add_argument("--init", action="store_true",
                              help="create local config/state directories and print quick-start guidance")
    config_group.add_argument("--doctor", action="store_true",
                              help="inspect local config, Ollama reachability, and model readiness")

    # Session management
    session_group = parser.add_argument_group("session management",
                                              "maintain conversation history")
    session_group.add_argument("--session", "-s", metavar="NAME",
                               help="use or create a named session")
    session_group.add_argument("--default-session", metavar="NAME",
                               help="set and use a default session for future runs")
    session_group.add_argument("--list-sessions", action="store_true",
                               help="list all available sessions")
    session_group.add_argument("--delete-session", metavar="NAME",
                               help="delete a specific session")
    session_group.add_argument("--show-session", metavar="NAME",
                               help="show a saved session transcript")
    session_group.add_argument("--export-session", metavar="NAME",
                               help="export a saved session transcript to --output")
    session_group.add_argument("--output", metavar="FILE",
                               help="output file for --export-session")

    role_group = parser.add_argument_group("prompt roles",
                                           "manage saved custom prompt roles")
    role_group.add_argument("--list-roles", action="store_true",
                            help="list built-in and saved custom roles")
    role_group.add_argument("--show-role", metavar="NAME",
                            help="show the prompt for a built-in or custom role")
    role_group.add_argument("--save-role", metavar="NAME",
                            help="save a custom role using --role-prompt")
    role_group.add_argument("--role-prompt", metavar="TEXT",
                            help="prompt text used with --save-role")
    role_group.add_argument("--delete-role", metavar="NAME",
                            help="delete a saved custom role")

    # Context loading
    context_group = parser.add_argument_group("context",
                                              "include file contents in prompts")
    context_group.add_argument("--context", "-c", action="append",
                               metavar="FILE",
                               help="load context from file(s) - can be used multiple times")

    # Code execution
    exec_group = parser.add_argument_group("code execution",
                                           "safely execute AI-generated commands")
    exec_group.add_argument("--execute", "-e", action="store_true",
                            help="enable command execution (requires --shell)")
    exec_group.add_argument("--yes", "-y", action="store_true",
                            help="auto-confirm LOW/MEDIUM risk commands (use carefully!)")
    exec_group.add_argument("--dry-run", action="store_true",
                            help="preview commands without executing")

    cache_group = parser.add_argument_group("cache",
                                            "opt-in local response caching")
    cache_group.add_argument("--cache", action="store_true",
                             help="cache one-shot responses locally for faster repeats")
    cache_group.add_argument("--show-cache", action="store_true",
                             help="show cached response entries")
    cache_group.add_argument("--clear-cache", action="store_true",
                             help="delete all cached response entries")

    args = parser.parse_args()
    session_actions = sum(
        bool(value)
        for value in [
            args.list_sessions,
            args.delete_session,
            args.show_session,
            args.export_session,
        ]
    )
    if session_actions > 1:
        parser.error("choose only one session management command at a time")
    if args.export_session and not args.output:
        parser.error("--export-session requires --output FILE")
    if args.output and not args.export_session:
        parser.error("--output requires --export-session")
    if args.default_session and is_temp_session(args.default_session):
        parser.error("temporary session 'temp' cannot be saved as the default session")
    if args.describe_shell and args.prompt:
        parser.error("--describe-shell cannot be combined with the positional prompt")
    if args.role and any([args.shell, args.code, args.explain, args.describe_shell, args.tools]):
        parser.error("--role cannot be combined with built-in mode flags")
    if args.tools and any([args.shell, args.code, args.explain, args.describe_shell]):
        parser.error("--tools cannot be combined with other mode flags")
    if args.stdout_only and not args.shell:
        parser.error("--stdout-only requires --shell")
    if args.stdout_only and (args.execute or args.dry_run):
        parser.error("--stdout-only cannot be combined with --execute or --dry-run")
    if args.describe_shell and any([args.shell, args.code, args.explain]):
        parser.error("--describe-shell cannot be combined with other mode flags")
    if args.describe_shell and any([args.execute, args.dry_run, args.yes]):
        parser.error("--describe-shell cannot be combined with execution flags")
    if args.cache and (args.execute or args.dry_run):
        parser.error("--cache cannot be combined with --execute or --dry-run")
    if args.tools and any([args.execute, args.dry_run, args.yes, args.stdout_only, args.cache]):
        parser.error("--tools cannot be combined with execution or cache flags")

    role_actions = sum(
        bool(value)
        for value in [
            args.list_roles,
            args.show_role,
            args.save_role,
            args.delete_role,
        ]
    )
    if role_actions > 1:
        parser.error("choose only one role management command at a time")
    if args.save_role and not args.role_prompt:
        parser.error("--save-role requires --role-prompt TEXT")
    if args.role_prompt and not args.save_role:
        parser.error("--role-prompt requires --save-role")

    cache_actions = sum(bool(value) for value in [args.show_cache, args.clear_cache])
    if cache_actions > 1:
        parser.error("choose only one cache management command at a time")

    setup_actions = sum(bool(value) for value in [args.init, args.doctor, args.shell_integration])
    if setup_actions > 1:
        parser.error("choose only one setup or diagnostic command at a time")

    standalone_command_flags = any(
        [
            args.prompt,
            args.shell,
            args.code,
            args.explain,
            args.describe_shell,
            args.role,
            args.tools,
            args.model,
            args.no_stream,
            args.stdout_only,
            args.session,
            args.default_session,
            args.list_sessions,
            args.delete_session,
            args.show_session,
            args.export_session,
            args.output,
            args.list_roles,
            args.show_role,
            args.save_role,
            args.role_prompt,
            args.delete_role,
            args.context,
            args.execute,
            args.yes,
            args.dry_run,
            args.cache,
            args.show_cache,
            args.clear_cache,
        ]
    )
    if args.init and standalone_command_flags:
        parser.error("--init cannot be combined with prompt, mode, session, role, cache, or execution flags")
    if args.doctor and standalone_command_flags:
        parser.error("--doctor cannot be combined with prompt, mode, session, role, cache, or execution flags")

    if args.init:
        init_command()
        return

    if args.doctor:
        config = load_config_or_exit()
        exit_code = doctor_command(config)
        if exit_code:
            sys.exit(exit_code)
        return

    if args.shell_integration:
        print_stdout_only(build_shell_integration_script(args.shell_integration))
        return

    config = load_config_or_exit()

    if args.model:
        config["model"] = args.model
    if args.no_stream:
        config["stream"] = False

    if args.list_roles:
        list_roles_command(config.get("shell", "bash"))
        return

    if args.show_role:
        show_role_command(args.show_role, config.get("shell", "bash"))
        return

    if args.save_role:
        save_role_command(args.save_role, args.role_prompt)
        return

    if args.delete_role:
        delete_role_command(args.delete_role)
        return

    if args.show_cache:
        show_cache_command()
        return

    if args.clear_cache:
        clear_cache_command()
        return

    # Initialize session manager
    sessions_dir = runtime_directories()["sessions"]
    session_manager = SessionManager(sessions_dir)

    # Handle session management commands
    if args.list_sessions:
        list_sessions_command(session_manager)
        return

    if args.delete_session:
        delete_session_command(session_manager, args.delete_session)
        return

    if args.show_session:
        show_session_command(session_manager, args.show_session)
        return

    if args.export_session:
        export_session_command(session_manager, args.export_session, Path(args.output))
        return

    session_name = args.session or config.get("default_session")
    if args.default_session:
        session_name = args.default_session
        config = update_config({"default_session": session_name})

    persist_session = bool(session_name) and not is_temp_session(session_name)
    active_session_manager = session_manager if persist_session else None

    if persist_session:
        try:
            try:
                session_manager.get_session(session_name)
            except SessionError:
                session_manager.create_session(session_name)
                console.print(
                    f"[green]Created new session:[/green] {session_name}")

            session_config = session_manager.get_config(session_name)
            if args.model:
                session_manager.update_config(
                    session_name, {"model": config["model"]})
            elif "model" in session_config:
                config["model"] = session_config["model"]
        except SessionError as e:
            console.print(f"[bold red]Session error:[/bold red] {e}")
            sys.exit(1)

    role = "default"
    role_prompt_override = None
    if args.describe_shell:
        role = "explain"
    elif args.tools:
        if not config.get("tools_enabled", False):
            console.print(
                "[bold red]Error:[/bold red] Local tools are disabled. Set `tools_enabled: true` in `~/.ollama_sgpt.yaml` to opt in."
            )
            sys.exit(1)
    elif args.role:
        try:
            role_prompt_override = load_custom_role(
                args.role,
                roles_directory(),
            )
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
    elif args.shell:
        role = "shell"
    elif args.code:
        role = "code"
    elif args.explain:
        role = "explain"

    # Validate flag combinations
    if (args.execute or args.yes or args.dry_run) and not args.shell:
        console.print("\n[bold yellow]⚠️  Warning:[/bold yellow] Execution flags work best with --shell mode\n")
        console.print("[dim]Did you mean:[/dim]")
        console.print("  [cyan]ollama-sgpt --shell --execute 'your command'[/cyan]")
        console.print()
        if not args.prompt and not sys.stdin.isatty():
            console.print("[yellow]Continuing without execution mode...[/yellow]\n")

    if args.yes and not args.execute:
        console.print("\n[bold yellow]💡 Tip:[/bold yellow] --yes flag requires --execute\n")
        console.print("[dim]Use:[/dim] [cyan]--execute --yes[/cyan] to auto-confirm safe commands\n")

    stdin_input = None
    if not sys.stdin.isatty():
        stdin_input = sys.stdin.read().strip()

    if args.cache and not args.prompt and not args.describe_shell and not stdin_input:
        parser.error("--cache currently supports one-shot requests only")
    if args.tools and not args.prompt and not stdin_input:
        parser.error("--tools currently supports one-shot requests only")

    if not args.prompt and not args.describe_shell and not stdin_input:
        validate_runtime(config)
        # Use enhanced REPL
        def chat_func(user_input, history, cfg, r): return execute_chat(
            user_input, history, cfg, r, role_prompt=role_prompt_override)

        # Initialize executor if needed
        executor = None
        if args.execute or args.dry_run:
            executor = CodeExecutor(
                timeout=120,
                auto_confirm=args.yes,
                shell_type=config.get("shell")
            )

        initial_history = []
        if persist_session:
            try:
                initial_history = load_session_history(session_manager, session_name)
            except SessionError as e:
                console.print(f"[bold red]Session error:[/bold red] {e}")
                sys.exit(1)

        interactive_loop_enhanced(
            config,
            role,
            chat_func,
            active_session_manager,
            session_name,
            executor=executor,
            dry_run=args.dry_run,
            initial_history=initial_history,
            transient_session=is_temp_session(session_name),
        )
        return

    user_input = args.describe_shell or args.prompt or stdin_input

    # Load context if provided
    context = None
    if args.context:
        try:
            valid_files, invalid_files = validate_context_files(args.context)
            if invalid_files:
                console.print(
                    f"[yellow]Warning: Cannot read {len(invalid_files)} file(s):[/yellow]")
                for f in invalid_files:
                    console.print(f"  - {f}")
            if valid_files:
                context = load_context_files(valid_files)
                console.print(
                    f"[dim]{format_context_summary(valid_files)}[/dim]\n")
            else:
                console.print(
                    "[bold red]Error:[/bold red] No valid context files found")
                sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]Error loading context:[/bold red] {e}")
            sys.exit(1)

    # Build prompt with context
    final_input = build_context_prompt(user_input, context)
    if args.describe_shell:
        final_input = build_shell_description_prompt(user_input, config.get("shell"))

    # Load session history if using sessions
    history = []
    if persist_session:
        try:
            history = load_session_history(session_manager, session_name)
        except SessionError as e:
            console.print(f"[bold red]Session error:[/bold red] {e}")
            sys.exit(1)

    try:
        response = None
        tool_trace_messages = []
        cache_key = None
        if args.tools:
            validate_runtime(config)
            response, tool_trace_messages = execute_tool_workflow(
                final_input,
                history,
                config,
            )
            for trace_message in tool_trace_messages:
                console.print(f"[dim]{trace_message}[/dim]")
                console.print()
            if config["stream"]:
                console.print(response)
            else:
                console.print(Markdown(response))
        elif args.cache:
            cache_key = build_cache_key(
                model=config["model"],
                role=role,
                prompt=user_input,
                context=context or "",
                shell_type=config.get("shell", ""),
                role_prompt=role_prompt_override or "",
                history=history,
                stream=config["stream"],
            )
            cached_entry = get_cache_entry(cache_key)
            if cached_entry:
                response = render_response_output(
                    cached_entry["response"],
                    role,
                    config,
                    stdout_only=args.stdout_only,
                )

        if response is None:
            validate_runtime(config)
            response = execute_chat(
                final_input,
                history,
                config,
                role,
                stdout_only=args.stdout_only,
                role_prompt=role_prompt_override,
            )
            if args.cache and response:
                save_cache_entry(
                    cache_key,
                    response,
                    {
                        "model": config["model"],
                        "role_name": args.role or role,
                        "shell_type": config.get("shell", ""),
                        "prompt_preview": user_input[:80],
                    },
                )
        execution_summary = None

        # Execute command if --execute flag is set
        if args.execute or args.dry_run:
            if role == "shell":
                executor = CodeExecutor(
                    timeout=120,
                    auto_confirm=args.yes,
                    shell_type=config.get("shell")
                )

                # execute_chat() already normalizes shell response to a command.
                command = response.strip()

                if command:
                    console.print()
                    console.print("[bold cyan]Extracted command:[/bold cyan]")
                    result = executor.execute(command, dry_run=args.dry_run)

                    # Store execution result in session if available
                    if persist_session and not args.dry_run:
                        execution_summary = f"[Executed: {command}]\nExit code: {result.returncode}"
                elif response.strip():
                    console.print(
                        "[yellow]⚠️  Could not extract a command from the response[/yellow]")
                    console.print(
                        "[dim]The AI response doesn't contain an executable command.[/dim]")
            else:
                console.print(
                    "[yellow]⚠️  --execute flag only works with --shell mode[/yellow]")

        # Save to session if using sessions
        if persist_session:
            try:
                active_session_manager.add_message(session_name, "user", user_input)
                for trace_message in tool_trace_messages:
                    active_session_manager.add_message(
                        session_name,
                        "assistant",
                        trace_message,
                    )
                active_session_manager.add_message(
                    session_name, "assistant", response)
                if execution_summary:
                    active_session_manager.add_message(
                        session_name, "assistant", execution_summary
                    )
            except SessionError as e:
                console.print(
                    f"[yellow]Warning: Could not save to session: {e}[/yellow]")

    except OllamaConnectionError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
