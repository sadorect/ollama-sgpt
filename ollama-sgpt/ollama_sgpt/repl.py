"""Advanced REPL for ollama-sgpt."""
from typing import Optional, Callable
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path

console = Console()


def create_repl_session(history_file: Path) -> PromptSession:
    """Create enhanced REPL session with prompt-toolkit.

    Args:
        history_file: Path to store command history

    Returns:
        Configured PromptSession
    """
    # Ensure history directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Custom key bindings
    bindings = KeyBindings()

    @bindings.add('escape', 'enter')
    def _(event):
        """Submit on Esc+Enter."""
        event.current_buffer.validate_and_handle()

    # Custom style
    style = Style.from_dict({
        'prompt': 'ansigreen bold',
        'continuation': 'ansigreen',
    })

    return PromptSession(
        history=FileHistory(str(history_file)),
        key_bindings=bindings,
        style=style,
        multiline=True,
        prompt_continuation='... ',
    )


def interactive_loop_enhanced(
    config: dict,
    role: str,
    chat_function: Callable,
    session_manager: Optional[object] = None,
    session_name: Optional[str] = None,
    executor: Optional[object] = None,
    dry_run: bool = False,
    initial_history: Optional[list] = None,
    transient_session: bool = False,
):
    """Enhanced interactive loop with multi-line support and special commands.

    Args:
        config: Configuration dictionary
        role: Current role (shell, code, explain, etc.)
        chat_function: Function to call for chat responses
        session_manager: Optional SessionManager instance
        session_name: Optional session name to use
        executor: Optional CodeExecutor instance for command execution
        dry_run: If True, only preview commands without executing
        initial_history: Optional existing conversation history to preload
        transient_session: If True, show that the named session is ephemeral
    """
    history_file = Path.home() / ".ollama-sgpt" / "repl_history"
    session = create_repl_session(history_file)

    # Enhanced welcome message
    console.print("\n[bold green]✨ ollama-sgpt Interactive Mode[/bold green]")
    console.print(f"[dim]Model: {config['model']}[/dim]")

    if session_name:
        console.print(f"[dim]Session: {session_name}[/dim]")
        if transient_session:
            console.print("[dim]Temporary session: this conversation is not saved to disk[/dim]")

    console.print()
    console.print("[bold cyan]Getting Started:[/bold cyan]")
    console.print("  • Type your question or request")
    console.print("  • Press [bold]Esc+Enter[/bold] for multi-line input")
    console.print("  • Type [bold]/help[/bold] to see available commands")
    console.print(
        "  • Type [bold]/exit[/bold] or press [bold]Ctrl+D[/bold] to quit")
    console.print()

    if executor:
        mode = "DRY RUN" if dry_run else "EXECUTION"
        risk_info = "[dim](HIGH/CRITICAL commands require manual confirmation)[/dim]" if not dry_run else ""
        console.print(f"[yellow]⚡ Command {mode} enabled {risk_info}[/yellow]")
        console.print()
    elif role == "shell":
        console.print(
            "[dim]💡 Tip: Add --execute flag to run generated commands[/dim]")
        console.print()

    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in (initial_history or [])
    ]
    if conversation_history:
        console.print(
            f"[dim]Loaded {len(conversation_history)} message(s) from session history[/dim]"
        )
        console.print()

    while True:
        try:
            # Get user input
            user_input = session.prompt('>>> ').strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.startswith('/'):
                if handle_special_command(
                    user_input,
                    conversation_history,
                    session_manager,
                    session_name
                ):
                    break  # Exit if /exit or /quit
                continue

            # Get response
            console.print()
            response = chat_function(
                user_input,
                conversation_history.copy(),
                config,
                role,
            )

            # Add user/assistant exchange only after the model call succeeds so
            # the next prompt sees the same history as the one-shot CLI path.
            conversation_history.append({
                "role": "user",
                "content": user_input
            })
            conversation_history.append({
                "role": "assistant",
                "content": response
            })

            # Save to session if using sessions
            if session_manager and session_name:
                session_manager.add_message(session_name, "user", user_input)
                session_manager.add_message(
                    session_name, "assistant", response)

            # Execute command if executor is available and role is shell
            if executor and role == "shell":
                command = executor.extract_command_from_response(response)
                if command:
                    console.print()
                    console.print("[bold cyan]Extracted command:[/bold cyan]")
                    result = executor.execute(command, dry_run=dry_run)

                    # Add execution result to conversation if successful
                    if not dry_run and result.success:
                        exec_msg = f"[Command executed successfully]\\n{result.stdout}"
                        conversation_history.append({
                            "role": "assistant",
                            "content": exec_msg
                        })
                        if session_manager and session_name:
                            session_manager.add_message(
                                session_name, "assistant", exec_msg)

            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            continue
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            continue


def handle_special_command(
    command: str,
    conversation_history: list,
    session_manager: Optional[object],
    session_name: Optional[str]
) -> bool:
    """Handle special REPL commands.

    Args:
        command: The command string
        conversation_history: Current conversation history
        session_manager: Optional SessionManager instance
        session_name: Optional session name

    Returns:
        True if should exit, False otherwise
    """
    cmd = command.lower().strip()

    if cmd in ['/exit', '/quit', '/q']:
        console.print("[dim]Goodbye![/dim]")
        return True

    elif cmd in ['/help', '/h']:
        show_help()

    elif cmd in ['/clear', '/c']:
        conversation_history.clear()
        if session_manager and session_name:
            session_manager.clear_session(session_name)
        console.print("[green]Conversation cleared[/green]")

    elif cmd in ['/history', '/hist']:
        show_history(conversation_history)

    elif cmd.startswith('/save'):
        # TODO: Implement save to file
        console.print("[yellow]Save command not yet implemented[/yellow]")

    else:
        console.print(f"[red]Unknown command:[/red] {command}")
        console.print("[dim]Type /help for available commands[/dim]")

    return False


def show_help():
    """Display help information."""
    help_text = """
# REPL Commands

## Input
- Press **Esc+Enter** to submit multi-line input
- Press **Ctrl+C** to cancel current input
- Press **Ctrl+D** or type **/exit** to quit

## Commands
- **/help, /h** - Show this help
- **/clear, /c** - Clear conversation history
- **/history, /hist** - Show conversation history
- **/exit, /quit, /q** - Exit REPL

## Navigation
- **Up/Down arrows** - Navigate command history
- **Ctrl+A** - Move to beginning of line
- **Ctrl+E** - Move to end of line
"""
    console.print(Markdown(help_text))


def show_history(conversation_history: list):
    """Display conversation history.

    Args:
        conversation_history: List of conversation messages
    """
    if not conversation_history:
        console.print("[dim]No conversation history[/dim]")
        return

    console.print(
        f"\n[bold]Conversation History ({len(conversation_history)} messages)[/bold]\n")

    for i, msg in enumerate(conversation_history, 1):
        role = msg['role']
        content = msg['content']

        if role == 'user':
            console.print(
                f"[bold cyan]{i}. You:[/bold cyan] {content[:100]}...")
        else:
            console.print(
                f"[bold green]{i}. Assistant:[/bold green] {content[:100]}...")

    console.print()
