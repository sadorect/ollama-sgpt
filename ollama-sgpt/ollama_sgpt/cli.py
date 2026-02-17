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
from .executor import CodeExecutor
from . import __version__

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
        prog="ollama-sgpt",
        description="AI-powered shell assistant using Ollama",
        epilog="Examples:\n"
               "  %(prog)s 'how do I find large files?'\n"
               "  %(prog)s --shell 'compress all logs'\n"
               "  %(prog)s --code 'write a sorting function'\n"
               "  %(prog)s --session myproject 'continue discussion'\n"
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

    # Model configuration
    config_group = parser.add_argument_group("configuration",
                                             "model and output settings")
    config_group.add_argument("--model", metavar="NAME",
                              help="ollama model to use (default: from config)")
    config_group.add_argument("--no-stream", action="store_true",
                              help="disable streaming output")

    # Session management
    session_group = parser.add_argument_group("session management",
                                              "maintain conversation history")
    session_group.add_argument("--session", "-s", metavar="NAME",
                               help="use or create a named session")
    session_group.add_argument("--list-sessions", action="store_true",
                               help="list all available sessions")
    session_group.add_argument("--delete-session", metavar="NAME",
                               help="delete a specific session")

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
        console.print(f"\n[bold red]❌ Connection Error:[/bold red] {e}\n")
        console.print("[bold yellow]Troubleshooting Steps:[/bold yellow]")
        console.print("  1. [cyan]Check if Ollama is installed:[/cyan]")
        console.print("     Visit https://ollama.ai/download")
        console.print()
        console.print("  2. [cyan]Start the Ollama service:[/cyan]")
        console.print("     [dim]$[/dim] ollama serve")
        console.print()
        console.print("  3. [cyan]Verify Ollama is running:[/cyan]")
        console.print("     [dim]$[/dim] curl http://localhost:11434/api/version")
        console.print()
        console.print("  4. [cyan]List available models:[/cyan]")
        console.print("     [dim]$[/dim] ollama list")
        console.print()
        console.print("[dim]Need help?[/dim] See [link=https://github.com/sadorect/ollama-sgpt/blob/main/docs/troubleshooting.md]troubleshooting guide[/link]")
        sys.exit(1)
    except OllamaModelError as e:
        console.print(f"\n[bold red]❌ Model Error:[/bold red] {e}\n")
        console.print("[bold yellow]Fix:[/bold yellow]")
        console.print(f"  Download the model with:")
        console.print(f"  [dim]$[/dim] [cyan]ollama pull {config['model']}[/cyan]")
        console.print()
        console.print("[bold]Popular Models:[/bold]")
        console.print("  • [cyan]llama3[/cyan]      - Latest, best quality (5GB)")
        console.print("  • [cyan]mistral[/cyan]     - Fast and versatile (4GB)")
        console.print("  • [cyan]codellama[/cyan]   - Optimized for code (4GB)")
        console.print("  • [cyan]llama2[/cyan]      - Reliable and stable (4GB)")
        console.print()
        console.print("[dim]View all models:[/dim] [cyan]ollama list[/cyan]")
        sys.exit(1)

    role = "default"
    if args.shell:
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

    if not args.prompt and not stdin_input:
        # Use enhanced REPL
        def chat_func(user_input, history, cfg, r): return execute_chat(
            user_input, history, cfg, r)

        # Initialize executor if needed
        executor = None
        if args.execute or args.dry_run:
            executor = CodeExecutor(timeout=120, auto_confirm=args.yes)

        interactive_loop_enhanced(
            config,
            role,
            chat_func,
            session_manager if args.session else None,
            args.session,
            executor=executor,
            dry_run=args.dry_run
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

        # Execute command if --execute flag is set
        if args.execute or args.dry_run:
            if role == "shell":
                executor = CodeExecutor(
                    timeout=120,
                    auto_confirm=args.yes
                )

                # Extract command from response
                command = executor.extract_command_from_response(response)

                if command:
                    console.print()
                    console.print("[bold cyan]Extracted command:[/bold cyan]")
                    result = executor.execute(command, dry_run=args.dry_run)

                    # Store execution result in session if available
                    if args.session and not args.dry_run:
                        execution_summary = f"[Executed: {command}]\\nExit code: {result.returncode}"
                        try:
                            session_manager.add_message(
                                args.session,
                                "assistant",
                                execution_summary
                            )
                        except SessionError:
                            pass
                else:
                    console.print(
                        "[yellow]⚠️  Could not extract a command from the response[/yellow]")
                    console.print(
                        "[dim]The AI response doesn't contain an executable command.[/dim]")
            else:
                console.print(
                    "[yellow]⚠️  --execute flag only works with --shell mode[/yellow]")

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
