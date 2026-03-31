"""Unit tests for CLI helpers."""

import pytest
import ollama_sgpt.cli as cli_module
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, call
from ollama_sgpt.cli import (
    build_shell_description_prompt,
    build_connection_diagnostics,
    build_model_diagnostics,
    execute_chat,
    main,
    normalize_shell_response,
)
from ollama_sgpt.exceptions import OllamaConnectionError, OllamaModelError
from ollama_sgpt.roles import SHELL_PROMPTS


def _cli_config(tmp_path, shell="powershell"):
    """Return a runtime-like CLI config for main() tests."""
    return {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "history_file": str(tmp_path / "history.json"),
        "stream": False,
        "shell": shell,
        "tools_enabled": False,
        "default_session": None,
        "request_timeout": 120,
        "stream_idle_timeout": 60,
    }


def _stdin_mock(isatty=True, data=""):
    """Return a stdin mock with configurable TTY behavior."""
    stdin = Mock()
    stdin.isatty.return_value = isatty
    stdin.read.return_value = data
    return stdin


def test_normalize_shell_response_extracts_command():
    """Shell responses should normalize to one executable command."""
    response = """Use this:

```powershell
Get-ChildItem -Recurse -Filter *.py
```"""
    command = normalize_shell_response(response, "powershell")
    assert command == "Get-ChildItem -Recurse -Filter *.py"


def test_normalize_shell_response_returns_empty_on_failure():
    """Missing commands should return an empty string."""
    response = "This describes steps but has no command."
    command = normalize_shell_response(response, "bash")
    assert command == ""


def test_normalize_shell_response_normalizes_prompt_prefixed_code_block():
    """Prompt prefixes inside code blocks should be stripped."""
    response = """```powershell
PS C:\\Users\\me> Get-ChildItem -Name
```"""
    command = normalize_shell_response(response, "powershell")
    assert command == "Get-ChildItem -Name"


def test_normalize_shell_response_strips_common_command_labels():
    """Common command labels should not block plaintext extraction."""
    response = "1. Command: dir /s *.py"
    command = normalize_shell_response(response, "cmd")
    assert command == "dir /s *.py"


def test_build_connection_diagnostics_uses_runtime_details(tmp_path):
    """Connection diagnostics should reflect the configured shell and endpoint."""
    config = {
        "ollama_url": "http://localhost:11434/api/chat",
        "shell": "powershell",
    }

    with patch("ollama_sgpt.cli.Path.home", return_value=tmp_path):
        diagnostics = build_connection_diagnostics(config)

    assert ("Endpoint", "http://localhost:11434/api/chat") in diagnostics["runtime"]
    assert ("Shell", "powershell") in diagnostics["runtime"]
    assert ("Config file", str(Path(tmp_path) / ".ollama_sgpt.yaml")) in diagnostics["runtime"]
    assert diagnostics["steps"][2][1] == "Invoke-WebRequest http://localhost:11434/api/version"


def test_build_model_diagnostics_references_requested_model(tmp_path):
    """Model diagnostics should point to the exact pull command to run."""
    config = {
        "model": "mistral",
        "ollama_url": "http://localhost:11434/api/chat",
    }

    with patch("ollama_sgpt.cli.Path.home", return_value=tmp_path):
        diagnostics = build_model_diagnostics(config)

    assert ("Requested model", "mistral") in diagnostics["runtime"]
    assert diagnostics["steps"][0][1] == "ollama pull mistral"
    assert diagnostics["steps"][1][1] == "ollama list"


def test_build_shell_description_prompt_mentions_shell_type():
    """Shell description prompts should mention the active shell family."""
    prompt = build_shell_description_prompt("Get-ChildItem -Name", "powershell")

    assert "PowerShell command" in prompt
    assert "Get-ChildItem -Name" in prompt


@patch("ollama_sgpt.cli.stream_chat")
def test_execute_chat_shell_stream_uses_no_echo(mock_stream_chat):
    """Shell mode streaming should suppress raw text and return command only."""
    mock_stream_chat.return_value = """You can run:

```bash
find . -name "*.py"
```"""
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": True,
        "shell": "bash",
    }

    with patch("ollama_sgpt.cli.console.print"):
        command = execute_chat("find python files", [], config, "shell")

    assert command == 'find . -name "*.py"'
    assert mock_stream_chat.call_args.kwargs["echo"] is False


@patch("ollama_sgpt.cli.stream_chat")
def test_execute_chat_streaming_non_shell_does_not_reprint_response(mock_stream_chat):
    """Live streamed non-shell output should not be printed a second time."""
    mock_stream_chat.return_value = "hello world"
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": True,
        "shell": "bash",
    }

    with patch("ollama_sgpt.cli.console.print") as mock_print:
        response = execute_chat("say hi", [], config, "default")

    assert response == "hello world"
    assert mock_stream_chat.call_args.kwargs["echo"] is True
    mock_print.assert_not_called()


@patch("ollama_sgpt.cli.chat")
def test_execute_chat_shell_uses_shell_specific_prompt(mock_chat):
    """Shell mode should send the configured shell prompt in the payload."""
    mock_chat.return_value = "Use `Get-ChildItem -Name`"
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": False,
        "shell": "powershell",
    }

    with patch("ollama_sgpt.cli.console.print"):
        execute_chat("list files", [], config, "shell")

    payload = mock_chat.call_args.args[1]
    assert payload["messages"][0]["content"] == SHELL_PROMPTS["powershell"]


@patch("ollama_sgpt.cli.chat")
def test_execute_chat_shell_non_stream_returns_command(mock_chat):
    """Non-stream shell mode should still normalize to a command."""
    mock_chat.return_value = "Use `dir /s *.py`"
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": False,
        "shell": "cmd",
    }

    with patch("ollama_sgpt.cli.console.print"):
        command = execute_chat("find python files", [], config, "shell")

    assert command == "dir /s *.py"


@patch("ollama_sgpt.cli.chat")
def test_execute_chat_shell_stdout_only_writes_plain_stdout(mock_chat):
    """Stdout-only shell mode should write the normalized command directly to stdout."""
    mock_chat.return_value = 'Use `find . -name "*.py"`'
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": False,
        "shell": "bash",
    }
    stdout = StringIO()

    with patch.object(cli_module.sys, "stdout", stdout), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        command = execute_chat("find python files", [], config, "shell", stdout_only=True)

    assert command == 'find . -name "*.py"'
    assert stdout.getvalue() == 'find . -name "*.py"\n'
    mock_print.assert_not_called()


@patch("ollama_sgpt.cli.chat")
def test_execute_chat_shell_returns_empty_and_prints_error_on_extraction_failure(mock_chat):
    """Shell mode should fail clearly when no executable command can be extracted."""
    mock_chat.return_value = "Here are some general steps, but not a runnable command."
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": False,
        "shell": "powershell",
    }

    with patch("ollama_sgpt.cli.console.print") as mock_print:
        command = execute_chat("scan subnet", [], config, "shell")

    assert command == ""
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "Could not extract an executable command" in printed


@patch("ollama_sgpt.cli.chat")
def test_execute_chat_shell_stdout_only_writes_extraction_error_to_stderr(mock_chat):
    """Stdout-only shell mode should send extraction failures to stderr."""
    mock_chat.return_value = "Not a runnable command."
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "stream": False,
        "shell": "bash",
    }
    stderr = StringIO()

    with patch.object(cli_module.sys, "stderr", stderr), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        command = execute_chat("find python files", [], config, "shell", stdout_only=True)

    assert command == ""
    assert "Could not extract an executable command" in stderr.getvalue()
    mock_print.assert_not_called()


def test_main_connection_error_renders_diagnostics_and_exits(tmp_path):
    """Startup connection failures should render structured diagnostics."""
    config = _cli_config(tmp_path)

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "hello"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health", side_effect=OllamaConnectionError("boom")), \
            patch("ollama_sgpt.cli.render_diagnostics") as mock_render:
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    mock_render.assert_called_once()
    title, diagnostics, message = mock_render.call_args.args
    assert title == "Connection Error:"
    assert ("Endpoint", config["ollama_url"]) in diagnostics["runtime"]
    assert ("Shell", config["shell"]) in diagnostics["runtime"]
    assert message == "boom"


def test_main_model_error_renders_diagnostics_and_exits(tmp_path):
    """Missing model failures should render structured recovery guidance."""
    config = _cli_config(tmp_path)

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "hello"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model", side_effect=OllamaModelError("missing llama3")), \
            patch("ollama_sgpt.cli.render_diagnostics") as mock_render:
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    mock_render.assert_called_once()
    title, diagnostics, message = mock_render.call_args.args
    assert title == "Model Error:"
    assert ("Requested model", config["model"]) in diagnostics["runtime"]
    assert ("Endpoint", config["ollama_url"]) in diagnostics["runtime"]
    assert message == "missing llama3"


def test_main_shell_dry_run_executes_normalized_command(tmp_path):
    """One-shot shell dry runs should send the extracted command to the executor."""
    config = _cli_config(tmp_path)
    executor = Mock()

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--shell", "--dry-run", "scan subnet"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.execute_chat", return_value="nmap -sn 192.168.1.0/24"), \
            patch("ollama_sgpt.cli.CodeExecutor", return_value=executor) as mock_executor_cls, \
            patch("ollama_sgpt.cli.console.print"):
        main()

    mock_executor_cls.assert_called_once_with(
        timeout=120,
        auto_confirm=False,
        shell_type=config["shell"],
    )
    executor.execute.assert_called_once_with("nmap -sn 192.168.1.0/24", dry_run=True)


def test_main_interactive_shell_execute_passes_executor_to_repl(tmp_path):
    """Interactive shell execution should wire an executor into the REPL."""
    config = _cli_config(tmp_path)
    executor = Mock()

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--shell", "--execute", "--yes"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.CodeExecutor", return_value=executor) as mock_executor_cls, \
            patch("ollama_sgpt.cli.interactive_loop_enhanced") as mock_repl:
        main()

    mock_executor_cls.assert_called_once_with(
        timeout=120,
        auto_confirm=True,
        shell_type=config["shell"],
    )
    assert mock_repl.call_args.args[1] == "shell"
    assert mock_repl.call_args.kwargs["executor"] is executor
    assert mock_repl.call_args.kwargs["dry_run"] is False


def test_main_warns_when_execution_flags_are_used_without_shell(tmp_path):
    """Execution flags without shell mode should warn and skip executor wiring."""
    config = _cli_config(tmp_path, shell="bash")

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--dry-run", "hello"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.execute_chat", return_value="hello there"), \
            patch("ollama_sgpt.cli.CodeExecutor") as mock_executor_cls, \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    mock_executor_cls.assert_not_called()
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "Execution flags work best with --shell mode" in printed
    assert "--execute flag only works with --shell mode" in printed


def test_main_show_session_prints_transcript_without_ollama_checks(tmp_path):
    """Session inspection should not depend on Ollama availability."""
    config = _cli_config(tmp_path)
    session_manager = Mock()
    session_manager.load_session.return_value = {
        "name": "work",
        "created": "2026-03-31T10:00:00",
        "modified": "2026-03-31T10:05:00",
        "messages": [
            {"role": "user", "content": "hello", "timestamp": "2026-03-31T10:00:01"},
            {"role": "assistant", "content": "hi", "timestamp": "2026-03-31T10:00:02"},
        ],
        "config": {},
    }

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--show-session", "work"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager", return_value=session_manager), \
            patch("ollama_sgpt.cli.check_ollama_health") as mock_health, \
            patch("ollama_sgpt.cli.validate_model") as mock_validate, \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    mock_health.assert_not_called()
    mock_validate.assert_not_called()
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "Session: work" in printed
    assert "hello" in printed
    assert "hi" in printed


def test_main_export_session_writes_markdown_without_ollama_checks(tmp_path):
    """Session export should write the requested file without contacting Ollama."""
    config = _cli_config(tmp_path)
    output_path = tmp_path / "transcript.md"
    session_manager = Mock()
    session_manager.load_session.return_value = {
        "name": "work",
        "created": "2026-03-31T10:00:00",
        "modified": "2026-03-31T10:05:00",
        "messages": [
            {"role": "user", "content": "hello", "timestamp": "2026-03-31T10:00:01"},
        ],
        "config": {"model": "llama3"},
    }

    with patch.object(
        cli_module.sys,
        "argv",
        ["ollama-sgpt", "--export-session", "work", "--output", str(output_path)],
    ), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager", return_value=session_manager), \
            patch("ollama_sgpt.cli.check_ollama_health") as mock_health, \
            patch("ollama_sgpt.cli.validate_model") as mock_validate, \
            patch("ollama_sgpt.cli.console.print"):
        main()

    mock_health.assert_not_called()
    mock_validate.assert_not_called()
    exported = output_path.read_text(encoding="utf-8")
    assert "# Session: work" in exported
    assert "`model`: `llama3`" in exported
    assert "hello" in exported


def test_main_export_session_requires_output(tmp_path):
    """Exporting a session should require an explicit output path."""
    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--export-session", "work"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2


def test_main_interactive_session_preloads_history_into_repl(tmp_path):
    """Interactive named sessions should preload saved history into the REPL."""
    config = _cli_config(tmp_path)
    session_manager = Mock()
    session_manager.get_config.return_value = {}
    session_manager.get_messages.return_value = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ]

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--session", "work"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager", return_value=session_manager), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.interactive_loop_enhanced") as mock_repl:
        main()

    assert mock_repl.call_args.kwargs["initial_history"] == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ]
    assert mock_repl.call_args.kwargs["transient_session"] is False


def test_main_temp_session_uses_ephemeral_repl_mode(tmp_path):
    """The reserved temp session should stay in memory and skip disk-backed session loading."""
    config = _cli_config(tmp_path)
    session_manager = Mock()

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--session", "temp"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager", return_value=session_manager), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.interactive_loop_enhanced") as mock_repl:
        main()

    session_manager.get_session.assert_not_called()
    assert mock_repl.call_args.args[3] is None
    assert mock_repl.call_args.args[4] == "temp"
    assert mock_repl.call_args.kwargs["initial_history"] == []
    assert mock_repl.call_args.kwargs["transient_session"] is True


def test_main_rejects_temp_as_default_session(tmp_path):
    """Temporary sessions should not be persisted as a default session."""
    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--default-session", "temp", "hello"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2


def test_main_persisted_session_saves_execution_summary_after_response(tmp_path):
    """Execution summaries should be appended after the model response in session storage."""
    config = _cli_config(tmp_path)
    session_manager = Mock()
    session_manager.get_config.return_value = {}
    session_manager.get_messages.return_value = []
    executor = Mock()
    executor.execute.return_value = Mock(returncode=0)

    with patch.object(
        cli_module.sys,
        "argv",
        ["ollama-sgpt", "--session", "ops", "--shell", "--execute", "--yes", "show disk usage"],
    ), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager", return_value=session_manager), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.execute_chat", return_value="Get-PSDrive"), \
            patch("ollama_sgpt.cli.CodeExecutor", return_value=executor), \
            patch("ollama_sgpt.cli.console.print"):
        main()

    assert session_manager.add_message.call_args_list == [
        call("ops", "user", "show disk usage"),
        call("ops", "assistant", "Get-PSDrive"),
        call("ops", "assistant", "[Executed: Get-PSDrive]\nExit code: 0"),
    ]


def test_main_shell_integration_prints_script_without_ollama_checks(tmp_path):
    """Shell integration snippets should be printable without contacting Ollama."""
    stdout = StringIO()

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--shell-integration", "bash"]), \
            patch.object(cli_module.sys, "stdout", stdout), \
            patch("ollama_sgpt.cli.load_config") as mock_config:
        main()

    mock_config.assert_not_called()
    assert "ollama_sgpt_command" in stdout.getvalue()
    assert "--stdout-only" in stdout.getvalue()


def test_main_init_creates_config_and_runtime_dirs_without_ollama_checks(tmp_path):
    """Init should only prepare local state and not contact Ollama."""
    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--init"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.config.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.check_ollama_health") as mock_health, \
            patch("ollama_sgpt.cli.validate_model") as mock_validate, \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    assert (tmp_path / ".ollama_sgpt.yaml").exists()
    assert (tmp_path / ".ollama-sgpt" / "sessions").is_dir()
    assert (tmp_path / ".ollama-sgpt" / "roles").is_dir()
    assert (tmp_path / ".ollama-sgpt" / "cache" / "entries").is_dir()
    config_text = (tmp_path / ".ollama_sgpt.yaml").read_text(encoding="utf-8")
    assert "model: llama3" in config_text
    assert "tools_enabled: false" in config_text
    mock_health.assert_not_called()
    mock_validate.assert_not_called()
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "Initialized ollama-sgpt" in printed
    assert "--doctor" in printed


def test_main_doctor_reports_successful_runtime(tmp_path):
    """Doctor should report a healthy runtime and exit cleanly."""
    config_file = tmp_path / ".ollama_sgpt.yaml"
    config_file.write_text(
        "model: llama3\nshell: powershell\ntools_enabled: true\n",
        encoding="utf-8",
    )

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--doctor"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.config.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.shutil.which", return_value="C:\\Ollama\\ollama.exe"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch(
                "ollama_sgpt.cli.list_models",
                return_value=[{"name": "llama3"}, {"name": "mistral"}],
            ), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "Doctor Runtime" in printed
    assert "Doctor found no blocking issues." in printed


def test_main_doctor_reports_actionable_failures_and_exits_nonzero(tmp_path):
    """Doctor should exit nonzero when required runtime checks fail."""
    config = _cli_config(tmp_path)

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--doctor"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.shutil.which", return_value=None), \
            patch(
                "ollama_sgpt.cli.check_ollama_health",
                side_effect=OllamaConnectionError("cannot reach test endpoint"),
            ), \
            patch("ollama_sgpt.cli.list_models") as mock_models, \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    mock_models.assert_not_called()
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "Doctor found" in printed
    assert "ollama serve" in printed


def test_main_describe_shell_uses_explain_role(tmp_path):
    """The describe-shell flow should call the model in explain mode."""
    config = _cli_config(tmp_path, shell="powershell")

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--describe-shell", "Get-ChildItem -Name"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.execute_chat", return_value="Lists items") as mock_execute:
        main()

    assert mock_execute.call_args.args[2] == config
    assert mock_execute.call_args.args[3] == "explain"
    assert "Explain this PowerShell command" in mock_execute.call_args.args[0]


def test_main_stdout_only_requires_shell_flag():
    """Stdout-only output should be limited to shell mode."""
    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--stdout-only", "hello"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2


def test_main_stdout_only_rejects_execute_flags():
    """Stdout-only mode should not be combined with execution flows."""
    with patch.object(
        cli_module.sys,
        "argv",
        ["ollama-sgpt", "--shell", "--stdout-only", "--dry-run", "hello"],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2


def test_main_list_roles_prints_builtin_and_custom_roles(tmp_path):
    """Listing roles should show built-ins plus saved custom roles."""
    config = _cli_config(tmp_path)
    roles_home = tmp_path
    roles_dir = roles_home / ".ollama-sgpt" / "roles"
    roles_dir.mkdir(parents=True)
    (roles_dir / "reviewer.txt").write_text("You are a reviewer.\n", encoding="utf-8")

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--list-roles"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.roles.Path.home", return_value=roles_home), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    table = mock_print.call_args.args[0]
    assert table.title == "Available Roles"
    assert "reviewer" in table.columns[0]._cells
    assert "shell" in table.columns[0]._cells


def test_main_save_role_writes_custom_prompt(tmp_path):
    """Saving a custom role should write it to the local roles directory."""
    config = _cli_config(tmp_path)

    with patch.object(
        cli_module.sys,
        "argv",
        ["ollama-sgpt", "--save-role", "reviewer", "--role-prompt", "You are a reviewer."],
    ), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.roles.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.console.print"):
        main()

    saved = (tmp_path / ".ollama-sgpt" / "roles" / "reviewer.txt").read_text(encoding="utf-8")
    assert saved == "You are a reviewer.\n"


def test_main_show_role_prints_saved_prompt(tmp_path):
    """Showing a custom role should print its prompt without contacting Ollama."""
    config = _cli_config(tmp_path)
    roles_dir = tmp_path / ".ollama-sgpt" / "roles"
    roles_dir.mkdir(parents=True)
    (roles_dir / "reviewer.txt").write_text("You are a reviewer.\n", encoding="utf-8")

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--show-role", "reviewer"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.roles.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "You are a reviewer." in printed


def test_main_custom_role_passes_saved_prompt_to_execute_chat(tmp_path):
    """Using --role should resolve the saved custom prompt and pass it to execute_chat."""
    config = _cli_config(tmp_path)
    roles_dir = tmp_path / ".ollama-sgpt" / "roles"
    roles_dir.mkdir(parents=True)
    (roles_dir / "reviewer.txt").write_text("You are a reviewer.\n", encoding="utf-8")

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--role", "reviewer", "review this patch"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.roles.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.execute_chat", return_value="Looks good") as mock_execute:
        main()

    assert mock_execute.call_args.kwargs["role_prompt"] == "You are a reviewer."


def test_main_role_rejects_built_in_names(tmp_path):
    """Built-in mode names should not be reusable through --role."""
    config = _cli_config(tmp_path)

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--role", "shell", "hello"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.roles.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "reserved" in printed.lower()


def test_main_show_cache_prints_entries_without_ollama_checks(tmp_path):
    """Showing cache entries should not require Ollama connectivity."""
    config = _cli_config(tmp_path)
    cache_dir = tmp_path / ".ollama-sgpt" / "cache" / "entries"
    cache_dir.mkdir(parents=True)
    (cache_dir / "entry.json").write_text(
        '{\n'
        '  "updated_at": "2026-03-31T10:00:00+00:00",\n'
        '  "model": "llama3",\n'
        '  "role_name": "default",\n'
        '  "hits": 2,\n'
        '  "prompt_preview": "hello"\n'
        '}\n',
        encoding="utf-8",
    )

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--show-cache"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cache.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    table = mock_print.call_args.args[0]
    assert table.title == "Cached Responses"
    assert "hello" in table.columns[4]._cells


def test_main_clear_cache_removes_entries(tmp_path):
    """Clearing the cache should remove saved entries from disk."""
    config = _cli_config(tmp_path)
    cache_dir = tmp_path / ".ollama-sgpt" / "cache" / "entries"
    cache_dir.mkdir(parents=True)
    (cache_dir / "entry.json").write_text("{}", encoding="utf-8")

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--clear-cache"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cache.Path.home", return_value=tmp_path), \
            patch("ollama_sgpt.cli.console.print"):
        main()

    assert list(cache_dir.glob("*.json")) == []


def test_main_cache_hit_skips_live_call_and_ollama_validation(tmp_path):
    """Cached one-shot responses should render without a live Ollama call."""
    config = _cli_config(tmp_path)
    cache_home = tmp_path
    cache_dir = cache_home / ".ollama-sgpt" / "cache" / "entries"
    cache_dir.mkdir(parents=True)

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--cache", "hello"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cache.Path.home", return_value=cache_home), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health"), \
            patch("ollama_sgpt.cli.validate_model"), \
            patch("ollama_sgpt.cli.execute_chat", return_value="cached hello"), \
            patch("ollama_sgpt.cli.console.print"):
        main()

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--cache", "hello"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cache.Path.home", return_value=cache_home), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.check_ollama_health") as mock_health, \
            patch("ollama_sgpt.cli.validate_model") as mock_validate, \
            patch("ollama_sgpt.cli.execute_chat") as mock_execute, \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        main()

    mock_health.assert_not_called()
    mock_validate.assert_not_called()
    mock_execute.assert_not_called()
    rendered = mock_print.call_args.args[0]
    assert getattr(rendered, "markup", "") == "cached hello"


def test_main_cache_rejects_execution_flags():
    """Caching should not be available for execute or dry-run flows."""
    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--cache", "--shell", "--dry-run", "hello"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2


def test_main_tools_requires_opt_in_config(tmp_path):
    """Tool mode should require tools_enabled in config."""
    config = _cli_config(tmp_path)
    config["tools_enabled"] = False

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--tools", "inspect the repo"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager"), \
            patch("ollama_sgpt.cli.console.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    printed = "".join(str(call) for call in mock_print.call_args_list)
    assert "tools are disabled" in printed.lower()


def test_main_tools_runs_workflow_and_logs_trace_to_session(tmp_path):
    """Tool mode should run the constrained workflow and persist tool traces."""
    config = _cli_config(tmp_path)
    config["tools_enabled"] = True
    session_manager = Mock()
    session_manager.get_config.return_value = {}
    session_manager.get_messages.return_value = []

    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--tools", "--session", "ops", "inspect the repo"]), \
            patch.object(cli_module.sys, "stdin", _stdin_mock(isatty=True)), \
            patch("ollama_sgpt.cli.load_config", return_value=config), \
            patch("ollama_sgpt.cli.SessionManager", return_value=session_manager), \
            patch("ollama_sgpt.cli.validate_runtime"), \
            patch(
                "ollama_sgpt.cli.execute_tool_workflow",
                return_value=("Here is the summary.", ['[Tool: git_status args={"path": "."}]\nclean']),
            ) as mock_tools, \
            patch("ollama_sgpt.cli.console.print"):
        main()

    mock_tools.assert_called_once()
    assert session_manager.add_message.call_args_list == [
        call("ops", "user", "inspect the repo"),
        call("ops", "assistant", '[Tool: git_status args={"path": "."}]\nclean'),
        call("ops", "assistant", "Here is the summary."),
    ]


def test_main_tools_rejects_shell_mode():
    """Tool mode should not combine with built-in shell mode."""
    with patch.object(cli_module.sys, "argv", ["ollama-sgpt", "--tools", "--shell", "hello"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2
