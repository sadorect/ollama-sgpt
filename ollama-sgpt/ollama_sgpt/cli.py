import sys
import argparse
from rich.console import Console
from rich.markdown import Markdown
from .config import load_config
from .history import load_history, save_history
from .ollama_client import stream_chat, check_ollama_health, validate_model
from .roles import ROLES
from .exceptions import OllamaConnectionError, OllamaModelError

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
            console.print("[yellow]Make sure Ollama is running: ollama serve[/]")
        except KeyboardInterrupt:
            console.print("\nbye 👋")
            break
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error:[/] {e}")


def main():
    parser = argparse.ArgumentParser(description="ShellGPT-style CLI for Ollama")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--shell", action="store_true")
    parser.add_argument("--code", action="store_true")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--no-stream", action="store_true")

    args = parser.parse_args()
    config = load_config()

    if args.model:
        config["model"] = args.model
    if args.no_stream:
        config["stream"] = False

    # Validate Ollama connection and model
    try:
        check_ollama_health(config["ollama_url"])
        validate_model(config["ollama_url"], config["model"])
    except OllamaConnectionError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print("\n[yellow]Troubleshooting:[/]")
        console.print("1. Make sure Ollama is installed: https://ollama.ai")
        console.print("2. Start Ollama server: ollama serve")
        console.print("3. Check server is running: curl http://localhost:11434/api/version")
        sys.exit(1)
    except OllamaModelError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print(f"\n[yellow]To download the model:[/] ollama pull {config['model']}")
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
        interactive_loop(config, role)
        return

    user_input = args.prompt or stdin_input
    messages = build_messages(ROLES[role], [], user_input)

    payload = {
        "model": config["model"],
        "messages": messages,
        "stream": config["stream"]
    }

    try:
        response = stream_chat(config["ollama_url"], payload)
        console.print(Markdown(response))
    except OllamaConnectionError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
