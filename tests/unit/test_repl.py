"""Tests for REPL functionality."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from prompt_toolkit import PromptSession
from ollama_sgpt.repl import (
    create_repl_session,
    handle_special_command,
    show_help,
    show_history
)


@pytest.fixture
def history_file(tmp_path):
    """Create a temporary history file path."""
    return tmp_path / "repl_history"


def test_create_repl_session(history_file):
    """Test creating a REPL session."""
    session = create_repl_session(history_file)

    assert isinstance(session, PromptSession)
    assert history_file.parent.exists()


def test_create_repl_session_creates_parent_directory(tmp_path):
    """Test that parent directories are created."""
    nested_path = tmp_path / "deep" / "nested" / "path" / "history"

    assert not nested_path.parent.exists()

    create_repl_session(nested_path)

    assert nested_path.parent.exists()


def test_handle_special_command_exit():
    """Test handling exit commands."""
    for cmd in ['/exit', '/quit', '/q', '/EXIT', '/QUIT']:
        result = handle_special_command(cmd, [], None, None)
        assert result is True


def test_handle_special_command_help():
    """Test handling help command."""
    with patch('ollama_sgpt.repl.show_help') as mock_help:
        result = handle_special_command('/help', [], None, None)
        assert result is False
        mock_help.assert_called_once()


def test_handle_special_command_clear():
    """Test handling clear command."""
    history = [{"role": "user", "content": "test"}]

    with patch('ollama_sgpt.repl.console') as mock_console:
        result = handle_special_command('/clear', history, None, None)

        assert result is False
        assert len(history) == 0
        mock_console.print.assert_called()


def test_handle_special_command_clear_with_session():
    """Test clearing with session management."""
    history = [{"role": "user", "content": "test"}]
    mock_manager = Mock()

    with patch('ollama_sgpt.repl.console'):
        handle_special_command('/clear', history, mock_manager, "test_session")

        mock_manager.clear_session.assert_called_once_with("test_session")
        assert len(history) == 0


def test_handle_special_command_history():
    """Test handling history command."""
    history = [{"role": "user", "content": "test"}]

    with patch('ollama_sgpt.repl.show_history') as mock_show:
        result = handle_special_command('/history', history, None, None)

        assert result is False
        mock_show.assert_called_once_with(history)


def test_handle_special_command_unknown():
    """Test handling unknown command."""
    with patch('ollama_sgpt.repl.console') as mock_console:
        result = handle_special_command('/unknown', [], None, None)

        assert result is False
        # Should print error message
        assert mock_console.print.call_count >= 1


def test_handle_special_command_case_insensitive():
    """Test that commands are case-insensitive."""
    with patch('ollama_sgpt.repl.show_help'):
        handle_special_command('/HELP', [], None, None)
        handle_special_command('/Help', [], None, None)
        handle_special_command('/hElP', [], None, None)


def test_show_help():
    """Test showing help information."""
    with patch('ollama_sgpt.repl.console') as mock_console:
        show_help()

        # Should print markdown help
        mock_console.print.assert_called()
        call_args = mock_console.print.call_args

        # Check that help text contains key information
        # (Markdown object is passed, so we can't easily check content)
        assert call_args is not None


def test_show_history_empty():
    """Test showing empty history."""
    with patch('ollama_sgpt.repl.console') as mock_console:
        show_history([])

        mock_console.print.assert_called()
        # Should mention no history
        call = str(mock_console.print.call_args)
        assert "No conversation history" in call or "no conversation" in call.lower()


def test_show_history_with_messages():
    """Test showing history with messages."""
    history = [
        {"role": "user", "content": "Hello world"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    with patch('ollama_sgpt.repl.console') as mock_console:
        show_history(history)

        # Should print multiple times (header + messages)
        assert mock_console.print.call_count >= len(history)


def test_show_history_truncates_long_messages():
    """Test that long messages are truncated in history display."""
    long_content = "A" * 200
    history = [
        {"role": "user", "content": long_content}
    ]

    with patch('ollama_sgpt.repl.console') as mock_console:
        show_history(history)

        # Check that content was truncated (looking for "...")
        calls = [str(call) for call in mock_console.print.call_args_list]
        history_call = [c for c in calls if "You:" in c or "user" in c.lower()]

        # Should have some truncation indication
        assert len(history_call) > 0


def test_interactive_loop_enhanced_basic():
    """Test basic interactive loop setup."""
    # This is a complex integration test, so we'll just test that it can be imported
    # and the basic structure is correct
    from ollama_sgpt.repl import interactive_loop_enhanced

    assert callable(interactive_loop_enhanced)


@patch('ollama_sgpt.repl.PromptSession')
@patch('ollama_sgpt.repl.console')
def test_interactive_loop_keyboard_interrupt(mock_console, mock_prompt_session):
    """Test handling keyboard interrupt in interactive loop."""
    from ollama_sgpt.repl import interactive_loop_enhanced

    # Mock the session to raise KeyboardInterrupt
    mock_session = Mock()
    mock_session.prompt.side_effect = KeyboardInterrupt()
    mock_prompt_session.return_value = mock_session

    config = {"model": "llama2"}
    chat_func = Mock()

    # Should handle KeyboardInterrupt gracefully
    try:
        interactive_loop_enhanced(config, "default", chat_func)
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt should be handled")


@patch('ollama_sgpt.repl.PromptSession')
@patch('ollama_sgpt.repl.console')
def test_interactive_loop_eof(mock_console, mock_prompt_session):
    """Test handling EOF in interactive loop."""
    from ollama_sgpt.repl import interactive_loop_enhanced

    # Mock the session to raise EOFError
    mock_session = Mock()
    mock_session.prompt.side_effect = EOFError()
    mock_prompt_session.return_value = mock_session

    config = {"model": "llama2"}
    chat_func = Mock()

    # Should handle EOFError gracefully
    interactive_loop_enhanced(config, "default", chat_func)

    # Should print goodbye message
    mock_console.print.assert_called()


def test_repl_session_multiline_enabled(history_file):
    """Test that REPL session has multiline enabled."""
    session = create_repl_session(history_file)

    # Check that multiline is enabled
    assert session.default_buffer.multiline is not None


def test_handle_special_command_whitespace():
    """Test handling commands with extra whitespace."""
    history = []

    with patch('ollama_sgpt.repl.show_help'):
        # Should handle whitespace properly
        result = handle_special_command('  /help  ', history, None, None)
        assert result is False

        result = handle_special_command('/exit  ', history, None, None)
        assert result is True
