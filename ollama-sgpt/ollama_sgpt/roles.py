import re
from pathlib import Path
from typing import Optional


ROLES = {
    "default": "You are a helpful assistant.",
    "shell": "You are a senior shell expert. Respond ONLY with a valid shell command.",
    "code": "You are a senior software engineer. Respond ONLY with code. No explanations.",
    "explain": "Explain the following command in clear, simple terms."
}

SHELL_PROMPTS = {
    "bash": "You are a senior Linux shell expert. Respond ONLY with a valid shell command.",
    "powershell": "You are a senior Windows PowerShell expert. Respond ONLY with a valid PowerShell command.",
    "cmd": "You are a senior Windows Command Prompt expert. Respond ONLY with a valid cmd.exe command."
}

RESERVED_ROLE_NAMES = set(ROLES)


def roles_directory(base_dir: Optional[Path] = None) -> Path:
    """Return the directory used for saved custom roles."""
    if base_dir:
        return Path(base_dir)
    return Path.home() / ".ollama-sgpt" / "roles"


def normalize_role_name(name: str) -> str:
    """Normalize a user-facing role name for storage and lookups."""
    return name.strip().lower()


def validate_custom_role_name(name: str) -> str:
    """Validate and normalize a custom role name."""
    normalized = normalize_role_name(name)
    if not normalized:
        raise ValueError("Role name cannot be empty.")
    if normalized in RESERVED_ROLE_NAMES:
        raise ValueError(
            f"Role name '{normalized}' is reserved. Use the built-in mode flags for built-in roles."
        )
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", normalized):
        raise ValueError(
            "Role name must start with a letter or number and contain only lowercase letters, numbers, hyphens, or underscores."
        )
    return normalized


def custom_role_path(name: str, base_dir: Optional[Path] = None) -> Path:
    """Return the on-disk path for a custom role."""
    normalized = validate_custom_role_name(name)
    return roles_directory(base_dir) / f"{normalized}.txt"


def list_custom_roles(base_dir: Optional[Path] = None) -> list[str]:
    """List saved custom role names."""
    directory = roles_directory(base_dir)
    if not directory.exists():
        return []
    return sorted(path.stem for path in directory.glob("*.txt"))


def save_custom_role(name: str, prompt: str, base_dir: Optional[Path] = None) -> Path:
    """Save a custom role prompt to disk."""
    normalized = validate_custom_role_name(name)
    prompt_text = prompt.strip()
    if not prompt_text:
        raise ValueError("Role prompt cannot be empty.")

    path = roles_directory(base_dir) / f"{normalized}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt_text + "\n", encoding="utf-8")
    return path


def load_custom_role(name: str, base_dir: Optional[Path] = None) -> str:
    """Load a saved custom role prompt."""
    path = custom_role_path(name, base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Custom role '{normalize_role_name(name)}' not found.")
    return path.read_text(encoding="utf-8").strip()


def delete_custom_role(name: str, base_dir: Optional[Path] = None) -> None:
    """Delete a saved custom role."""
    path = custom_role_path(name, base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Custom role '{normalize_role_name(name)}' not found.")
    path.unlink()


def get_role_prompt(role: str, shell_type: str) -> str:
    """Return the built-in prompt for a role name."""
    if role != "shell":
        return ROLES.get(role, ROLES["default"])

    prompt = SHELL_PROMPTS.get(shell_type)
    if prompt:
        return prompt
    return SHELL_PROMPTS["bash"]


def get_display_role_prompt(role_name: str, shell_type: str, base_dir: Optional[Path] = None) -> str:
    """Return the prompt text for a built-in or saved custom role."""
    normalized = normalize_role_name(role_name)
    if normalized in RESERVED_ROLE_NAMES:
        return get_role_prompt(normalized, shell_type)
    return load_custom_role(normalized, base_dir)
