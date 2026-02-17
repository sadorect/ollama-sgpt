import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from .config import load_config
from .history import load_history, save_history
from .ollama_client import stream_chat, check_ollama_health, validate_model
from .roles import ROLES
from .exceptions import OllamaConnectionError, OllamaModelError, SessionError
from .session import SessionManager
from .context import load_context_files, build_context_prompt, format_context_summary, validate_context_files
from .repl import interactive_loop_enhanced

console = Console()


def build_messages(system_prompt, history, user_input):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    return messages


def interactive_loop(config, role):
    history = load_history(config["history_file"])
    console.print(f"[bold green]ollama-sgpt[/] — model: {config['model']}")
    console.print("Type 'exit' to quit\n")

    while True:
        try:
            user_input = console.input("[bold cyan]you> [/]").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            messages = build_messages(ROLES[role], history, user_input)
            payload = {
                "model": config["model"],
                "messages": messages,
                "stream": config["stream"]
            }

            console.print("[bold magenta]ai> [/]", end="")
            response = stream_chat(config["ollama_url"], payload)

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


def execute_chat(user_input, history, config, role):
    """Execute a chat request and return the response."""
    messages = build_messages(ROLES[role], history, user_input)
    payload = {
        "model": config["model"],
        "messages": messages,
        "stream": config["stream"]
    }
    return stream_chat(config["ollama_url"], payload)


def main():
    parser = argparse.ArgumentParser(
        description="ShellGPT-style CLI for Ollama")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--shell", action="store_true")
    parser.add_argument("--code", action="store_true")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--no-stream", action="store_true")

    # Session management
    parser.add_argument("--session", "-s",
                        help="Session name to use or create")
    parser.add_argument("--list-sessions",
                        action="store_true", help="List all sessions")
    parser.add_argument("--delete-session", help="Delete a session")

    # Context loading
    parser.add_argument("--context", "-c", action="append",
                        help="Load context from file(s)")

    args = parser.parse_args()
    config = load_config()

    if args.model:
        config["model"] = args.model
    if args.no_stream:
        config["stream"] = False

    # Initialize session manager
    sessions_dir = Path.home() / ".ollama-sgpt" / "sessions"
    session_manager = SessionManager(sessions_dir)

    # Handle session management commands
    if args.list_sessions:
        list_sessions_command(session_manager)
        return

    if args.delete_session:
        delete_session_command(session_manager, args.delete_session)
        return

    # Validate Ollama connection and model
    try:
        check_ollama_health(config["ollama_url"])
        validate_model(config["ollama_url"], config["model"])
    except OllamaConnectionError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print("\n[yellow]Troubleshooting:[/]")
        console.print("1. Make sure Ollama is installed: https://ollama.ai")
        console.print("2. Start Ollama server: ollama serve")
        console.print(
            "3. Check server is running: curl http://localhost:11434/api/version")
        sys.exit(1)
    except OllamaModelError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print(
            f"\n[yellow]To download the model:[/] ollama pull {config['model']}")
        sys.exit(1)

    role = "default"
    if args.shell:
        role = "shell"
    elif args.code:
        role = "code"
    elif args.explain:
        role = "explain"

    stdin_input = None
    if not sys.stdin.isatty():
        stdin_input = sys.stdin.read().strip()

    if not args.prompt and not stdin_input:
        # Use enhanced REPL
        def chat_func(user_input, history, cfg, r): return execute_chat(
            user_input, history, cfg, r)
        interactive_loop_enhanced(
            config,
            role,
            chat_func,
            session_manager if args.session else None,
            args.session
        )
        return

    user_input = args.prompt or stdin_input

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

    # Load session history if using sessions
    history = []
    if args.session:
        try:
            # Create session if doesn't exist
            try:
                session_manager.get_session(args.session)
            except SessionError:
                session_manager.create_session(args.session)
                console.print(
                    f"[green]Created new session:[/green] {args.session}")

            # Load messages
            messages_data = session_manager.get_messages(args.session)
            history = [{"role": msg["role"], "content": msg["content"]}
                       for msg in messages_data]
        except SessionError as e:
            console.print(f"[bold red]Session error:[/bold red] {e}")
            sys.exit(1)

    messages = build_messages(ROLES[role], history, final_input)

    payload = {
        "model": config["model"],
        "messages": messages,
        "stream": config["stream"]
    }

    try:
        response = stream_chat(config["ollama_url"], payload)
        console.print(Markdown(response))

        # Save to session if using sessions
        if args.session:
            try:
                session_manager.add_message(args.session, "user", user_input)
                session_manager.add_message(
                    args.session, "assistant", response)
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
