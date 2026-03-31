"""Tests for session management."""
import json
import pytest
from ollama_sgpt.session import SessionManager
from ollama_sgpt.exceptions import SessionError


@pytest.fixture
def sessions_dir(tmp_path):
    """Create a temporary sessions directory."""
    return tmp_path / "sessions"


@pytest.fixture
def session_manager(sessions_dir):
    """Create a SessionManager instance."""
    return SessionManager(sessions_dir)


def test_session_manager_creates_directory(sessions_dir):
    """Test that SessionManager creates the sessions directory."""
    assert not sessions_dir.exists()
    SessionManager(sessions_dir)
    assert sessions_dir.exists()


def test_create_session(session_manager, sessions_dir):
    """Test creating a new session."""
    session_file = session_manager.create_session("test")

    assert session_file.exists()
    assert session_file.name == "test.json"

    with open(session_file, 'r') as f:
        data = json.load(f)

    assert data["name"] == "test"
    assert "created" in data
    assert "modified" in data
    assert data["messages"] == []


def test_create_session_duplicate_raises_error(session_manager):
    """Test that creating a duplicate session raises an error."""
    session_manager.create_session("test")

    with pytest.raises(SessionError, match="already exists"):
        session_manager.create_session("test")


def test_get_session(session_manager):
    """Test getting an existing session."""
    created_file = session_manager.create_session("test")
    retrieved_file = session_manager.get_session("test")

    assert created_file == retrieved_file


def test_get_session_not_found(session_manager):
    """Test getting a non-existent session raises an error."""
    with pytest.raises(SessionError, match="not found"):
        session_manager.get_session("nonexistent")


def test_list_sessions_empty(session_manager):
    """Test listing sessions when there are none."""
    sessions = session_manager.list_sessions()
    assert sessions == []


def test_list_sessions(session_manager):
    """Test listing multiple sessions."""
    session_manager.create_session("session1")
    session_manager.create_session("session2")
    session_manager.create_session("session3")

    sessions = session_manager.list_sessions()

    assert len(sessions) == 3
    names = [s["name"] for s in sessions]
    assert "session1" in names
    assert "session2" in names
    assert "session3" in names


def test_list_sessions_sorted_by_modified(session_manager):
    """Test that sessions are sorted by modification time."""
    session_manager.create_session("old")
    session_manager.create_session("new")

    # Modify the "new" session
    session_manager.add_message("new", "user", "Hello")

    sessions = session_manager.list_sessions()

    # "new" should come first (most recently modified)
    assert sessions[0]["name"] == "new"
    assert sessions[1]["name"] == "old"


def test_list_sessions_ignores_corrupted(session_manager, sessions_dir):
    """Test that corrupted sessions are ignored."""
    session_manager.create_session("good")

    # Create a corrupted session file
    corrupted_file = sessions_dir / "corrupted.json"
    with open(corrupted_file, 'w') as f:
        f.write("invalid json {")

    sessions = session_manager.list_sessions()

    assert len(sessions) == 1
    assert sessions[0]["name"] == "good"


def test_delete_session(session_manager, sessions_dir):
    """Test deleting a session."""
    session_manager.create_session("test")
    session_file = sessions_dir / "test.json"

    assert session_file.exists()

    session_manager.delete_session("test")

    assert not session_file.exists()


def test_delete_session_not_found(session_manager):
    """Test deleting a non-existent session raises an error."""
    with pytest.raises(SessionError, match="not found"):
        session_manager.delete_session("nonexistent")


def test_load_session(session_manager):
    """Test loading session data."""
    session_manager.create_session("test")
    data = session_manager.load_session("test")

    assert data["name"] == "test"
    assert "created" in data
    assert "messages" in data


def test_load_session_corrupted(session_manager, sessions_dir):
    """Test loading a corrupted session raises an error."""
    session_manager.create_session("test")
    session_file = sessions_dir / "test.json"

    # Corrupt the file
    with open(session_file, 'w') as f:
        f.write("invalid json {")

    with pytest.raises(SessionError, match="corrupted"):
        session_manager.load_session("test")


def test_save_session(session_manager):
    """Test saving session data."""
    session_manager.create_session("test")

    # Load and modify
    data = session_manager.load_session("test")
    original_modified = data["modified"]
    data["messages"].append({"role": "user", "content": "Hello"})

    # Save
    session_manager.save_session("test", data)

    # Reload and verify
    reloaded = session_manager.load_session("test")
    assert len(reloaded["messages"]) == 1
    assert reloaded["modified"] != original_modified


def test_add_message(session_manager):
    """Test adding a message to a session."""
    session_manager.create_session("test")

    session_manager.add_message("test", "user", "Hello")
    session_manager.add_message("test", "assistant", "Hi there!")

    messages = session_manager.get_messages("test")

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"
    assert "timestamp" in messages[0]
    assert "timestamp" in messages[1]


def test_get_messages_empty(session_manager):
    """Test getting messages from an empty session."""
    session_manager.create_session("test")
    messages = session_manager.get_messages("test")
    assert messages == []


def test_clear_session(session_manager):
    """Test clearing all messages from a session."""
    session_manager.create_session("test")
    session_manager.add_message("test", "user", "Hello")
    session_manager.add_message("test", "assistant", "Hi!")

    assert len(session_manager.get_messages("test")) == 2

    session_manager.clear_session("test")

    assert len(session_manager.get_messages("test")) == 0


def test_session_metadata_preserved(session_manager):
    """Test that session metadata is preserved across operations."""
    session_manager.create_session("test")
    data = session_manager.load_session("test")
    created = data["created"]

    # Add message
    session_manager.add_message("test", "user", "Hello")

    # Reload
    data = session_manager.load_session("test")

    # Created time should be the same
    assert data["created"] == created
    # Modified time should be different
    assert data["modified"] != created
