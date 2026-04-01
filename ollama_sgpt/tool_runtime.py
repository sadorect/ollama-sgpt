"""Constrained local tool runtime for opt-in read-only assistance."""

import csv
import json
import os
import platform
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .ollama_client import chat


TOOL_SPECS = {
    "list_files": {
        "description": "List files and directories under a path.",
        "args": {"path": "string, optional, default '.'"},
    },
    "read_file": {
        "description": "Read a UTF-8 text file with truncation for large files.",
        "args": {"path": "string, required"},
    },
    "git_status": {
        "description": "Show git status for a repository path.",
        "args": {"path": "string, optional, default '.'"},
    },
    "git_log": {
        "description": "Show recent git commits for a repository path.",
        "args": {"path": "string, optional, default '.'", "limit": "integer, optional, default 5"},
    },
    "system_info": {
        "description": "Show basic system and runtime information.",
        "args": {},
    },
    "list_processes": {
        "description": "List running processes with a small row limit.",
        "args": {"limit": "integer, optional, default 20"},
    },
}


def build_tool_system_prompt() -> str:
    """Return the system prompt for constrained tool use."""
    lines = [
        "You are a careful local assistant with access to a small set of read-only local tools.",
        "You may either answer directly or request exactly one tool at a time.",
        "If you need a tool, respond ONLY with a JSON object of the form:",
        '{"tool":"tool_name","args":{"key":"value"}}',
        "Do not add markdown fences or explanation around tool JSON.",
        "Only use the tools listed below.",
        "",
        "Available tools:",
    ]
    for name, spec in TOOL_SPECS.items():
        lines.append(f"- {name}: {spec['description']}")
        if spec["args"]:
            for arg_name, arg_description in spec["args"].items():
                lines.append(f"  - {arg_name}: {arg_description}")
    return "\n".join(lines)


def parse_tool_request(response: str) -> Optional[Dict]:
    """Parse a tool request from model output."""
    candidates = [response.strip()]

    if "```" in response:
        parts = response.split("```")
        for part in parts:
            stripped = part.strip()
            if stripped.startswith("json"):
                candidates.append(stripped[4:].strip())
            elif stripped.startswith("{"):
                candidates.append(stripped)

    for candidate in candidates:
        if not candidate.startswith("{"):
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if not isinstance(data.get("tool"), str):
            continue
        args = data.get("args", {})
        if args is None:
            args = {}
        if not isinstance(args, dict):
            continue
        return {"tool": data["tool"], "args": args}

    return None


def _run_read_only_command(command: List[str], cwd: Optional[str] = None) -> str:
    """Run a read-only subprocess and return stdout."""
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise ValueError(message)
    return result.stdout.strip()


def _resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def list_files_tool(path: str = ".") -> str:
    """List files and directories under a path."""
    target = _resolve_path(path)
    if not target.exists():
        raise ValueError(f"Path not found: {target}")
    if target.is_file():
        return f"{target.name}"

    entries = []
    for item in sorted(target.iterdir(), key=lambda entry: entry.name.lower())[:100]:
        suffix = "/" if item.is_dir() else ""
        entries.append(f"{item.name}{suffix}")
    return "\n".join(entries) or "(empty directory)"


def read_file_tool(path: str) -> str:
    """Read and truncate a text file."""
    target = _resolve_path(path)
    if not target.exists() or not target.is_file():
        raise ValueError(f"File not found: {target}")
    content = target.read_text(encoding="utf-8", errors="replace")
    if len(content) > 4000:
        content = content[:4000] + "\n...[truncated]"
    return content


def git_status_tool(path: str = ".") -> str:
    """Show git status for a repository path."""
    target = _resolve_path(path)
    return _run_read_only_command(["git", "-C", str(target), "status", "--short", "--branch"])


def git_log_tool(path: str = ".", limit: int = 5) -> str:
    """Show recent git commits for a repository path."""
    target = _resolve_path(path)
    safe_limit = max(1, min(int(limit), 20))
    return _run_read_only_command(["git", "-C", str(target), "log", "--oneline", f"-n{safe_limit}"])


def system_info_tool() -> str:
    """Return a small system information snapshot."""
    lines = [
        f"platform: {platform.platform()}",
        f"python: {sys.version.split()[0]}",
        f"cwd: {Path.cwd()}",
        f"os_name: {os.name}",
    ]
    return "\n".join(lines)


def list_processes_tool(limit: int = 20) -> str:
    """List running processes in a cross-platform way."""
    safe_limit = max(1, min(int(limit), 50))
    if os.name == "nt":
        output = _run_read_only_command(["tasklist", "/FO", "CSV", "/NH"])
        reader = csv.reader(StringIO(output))
        rows = []
        for row in reader:
            if len(row) >= 2:
                rows.append(f"{row[0]} (PID {row[1]})")
            if len(rows) >= safe_limit:
                break
        return "\n".join(rows)

    output = _run_read_only_command(["ps", "-eo", "pid,comm"])
    lines = output.splitlines()
    return "\n".join(lines[: safe_limit + 1])


def run_tool(name: str, args: Dict) -> Dict[str, str]:
    """Run an allowlisted read-only tool."""
    normalized = name.strip()
    if normalized == "list_files":
        output = list_files_tool(path=args.get("path", "."))
    elif normalized == "read_file":
        if "path" not in args:
            raise ValueError("read_file requires a 'path' argument.")
        output = read_file_tool(path=args["path"])
    elif normalized == "git_status":
        output = git_status_tool(path=args.get("path", "."))
    elif normalized == "git_log":
        output = git_log_tool(path=args.get("path", "."), limit=args.get("limit", 5))
    elif normalized == "system_info":
        output = system_info_tool()
    elif normalized == "list_processes":
        output = list_processes_tool(limit=args.get("limit", 20))
    else:
        raise ValueError(f"Unsupported tool: {normalized}")

    return {
        "tool": normalized,
        "args": json.dumps(args, sort_keys=True),
        "output": output,
    }


def execute_tool_workflow(
    user_input: str,
    history: List[Dict[str, str]],
    config: Dict,
    max_steps: int = 4,
) -> Tuple[str, List[str]]:
    """Run a constrained multi-step tool loop and return the final answer plus trace messages."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": build_tool_system_prompt()}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    tool_traces: List[str] = []

    for _ in range(max_steps):
        response = chat(
            config["ollama_url"],
            {
                "model": config["model"],
                "messages": messages,
                "stream": False,
            },
            request_timeout=config.get("request_timeout", 120),
        )

        request = parse_tool_request(response)
        if not request:
            return response, tool_traces

        try:
            result = run_tool(request["tool"], request["args"])
            output = result["output"]
        except Exception as exc:
            result = {
                "tool": request["tool"],
                "args": json.dumps(request["args"], sort_keys=True),
                "output": f"Tool error: {exc}",
            }
            output = result["output"]

        tool_traces.append(
            f"[Tool: {result['tool']} args={result['args']}]\n{result['output']}"
        )
        messages.append({"role": "assistant", "content": response})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Tool result for {result['tool']}:\n{output}\n\n"
                    "If you need another tool, return another JSON tool request. "
                    "Otherwise answer the original user request directly."
                ),
            }
        )

    return "I reached the tool step limit before producing a final answer.", tool_traces
