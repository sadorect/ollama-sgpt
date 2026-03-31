"""Tests for custom role storage and display helpers."""

import pytest

from ollama_sgpt.roles import (
    delete_custom_role,
    get_display_role_prompt,
    list_custom_roles,
    load_custom_role,
    save_custom_role,
    validate_custom_role_name,
)


def test_save_and_load_custom_role(tmp_path):
    """Saved custom roles should round-trip from disk."""
    save_custom_role("reviewer", "You are a meticulous reviewer.", tmp_path)

    assert load_custom_role("reviewer", tmp_path) == "You are a meticulous reviewer."


def test_list_custom_roles_returns_sorted_names(tmp_path):
    """Custom roles should list in sorted order."""
    save_custom_role("beta", "Prompt B", tmp_path)
    save_custom_role("alpha", "Prompt A", tmp_path)

    assert list_custom_roles(tmp_path) == ["alpha", "beta"]


def test_delete_custom_role_removes_saved_prompt(tmp_path):
    """Deleting a custom role should remove it from storage."""
    save_custom_role("reviewer", "You are a reviewer.", tmp_path)

    delete_custom_role("reviewer", tmp_path)

    with pytest.raises(FileNotFoundError):
        load_custom_role("reviewer", tmp_path)


def test_validate_custom_role_name_rejects_built_in_names():
    """Reserved built-in names should not be reusable as custom roles."""
    with pytest.raises(ValueError):
        validate_custom_role_name("shell")


def test_get_display_role_prompt_supports_builtin_and_custom_roles(tmp_path):
    """Displaying a role should work for built-ins and saved custom roles."""
    save_custom_role("reviewer", "You are a meticulous reviewer.", tmp_path)

    assert "Respond ONLY with a valid PowerShell command" in get_display_role_prompt(
        "shell",
        "powershell",
        tmp_path,
    )
    assert get_display_role_prompt("reviewer", "bash", tmp_path) == "You are a meticulous reviewer."
