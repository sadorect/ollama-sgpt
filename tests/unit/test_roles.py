"""Unit tests for roles module."""

from ollama_sgpt.roles import ROLES


def test_roles_exist():
    """Test that all expected roles exist."""
    assert "default" in ROLES
    assert "shell" in ROLES
    assert "code" in ROLES
    assert "explain" in ROLES


def test_role_content():
    """Test role content is appropriate."""
    assert "helpful assistant" in ROLES["default"].lower()
    assert "shell" in ROLES["shell"].lower()
    assert "code" in ROLES["code"].lower()
    assert "explain" in ROLES["explain"].lower()


def test_shell_role_specificity():
    """Test shell role is specific about output format."""
    assert "command" in ROLES["shell"].lower()


def test_code_role_specificity():
    """Test code role is specific about output format."""
    assert "code" in ROLES["code"].lower()
