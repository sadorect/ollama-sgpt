"""Session management for ollama-sgpt."""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from .exceptions import SessionError


class SessionManager:
    """Manage multiple chat sessions."""

    def __init__(self, sessions_dir: Path):
        """Initialize session manager.

        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, name: str) -> Path:
        """Create a new session.

        Args:
            name: Name of the session

        Returns:
            Path to the session file

        Raises:
            SessionError: If session already exists
        """
        session_file = self.sessions_dir / f"{name}.json"
        if session_file.exists():
            raise SessionError(f"Session '{name}' already exists")

        session_data = {
            "name": name,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "messages": []
        }

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        return session_file

    def get_session(self, name: str) -> Path:
        """Get session file path.

        Args:
            name: Name of the session

        Returns:
            Path to the session file

        Raises:
            SessionError: If session doesn't exist
        """
        session_file = self.sessions_dir / f"{name}.json"
        if not session_file.exists():
            raise SessionError(f"Session '{name}' not found")
        return session_file

    def list_sessions(self) -> List[Dict[str, str]]:
        """List all available sessions.

        Returns:
            List of session info dictionaries
        """
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                sessions.append({
                    "name": data.get("name", session_file.stem),
                    "created": data.get("created", "unknown"),
                    "modified": data.get("modified", "unknown"),
                    "messages": len(data.get("messages", []))
                })
            except (json.JSONDecodeError, IOError):
                # Skip corrupted sessions
                continue

        return sorted(sessions, key=lambda x: x["modified"], reverse=True)

    def delete_session(self, name: str) -> None:
        """Delete a session.

        Args:
            name: Name of the session to delete

        Raises:
            SessionError: If session doesn't exist
        """
        session_file = self.get_session(name)
        session_file.unlink()

    def load_session(self, name: str) -> Dict:
        """Load session data.

        Args:
            name: Name of the session

        Returns:
            Session data dictionary

        Raises:
            SessionError: If session doesn't exist or is corrupted
        """
        session_file = self.get_session(name)
        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise SessionError(f"Session '{name}' is corrupted: {e}")

    def save_session(self, name: str, data: Dict) -> None:
        """Save session data.

        Args:
            name: Name of the session
            data: Session data to save

        Raises:
            SessionError: If session doesn't exist
        """
        session_file = self.get_session(name)
        data["modified"] = datetime.now().isoformat()

        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_message(self, name: str, role: str, content: str) -> None:
        """Add a message to a session.

        Args:
            name: Name of the session
            role: Message role (user/assistant)
            content: Message content
        """
        data = self.load_session(name)
        data["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_session(name, data)

    def get_messages(self, name: str) -> List[Dict]:
        """Get all messages from a session.

        Args:
            name: Name of the session

        Returns:
            List of message dictionaries
        """
        data = self.load_session(name)
        return data.get("messages", [])

    def clear_session(self, name: str) -> None:
        """Clear all messages from a session.

        Args:
            name: Name of the session
        """
        data = self.load_session(name)
        data["messages"] = []
        self.save_session(name, data)
