"""Tests for the constrained local tool runtime."""

from pathlib import Path
from unittest.mock import patch

from ollama_sgpt.tool_runtime import (
    build_tool_system_prompt,
    execute_tool_workflow,
    parse_tool_request,
    run_tool,
)


def test_build_tool_system_prompt_lists_allowlisted_tools():
    """The tool system prompt should advertise the supported read-only tools."""
    prompt = build_tool_system_prompt()

    assert "list_files" in prompt
    assert "read_file" in prompt
    assert "git_status" in prompt


def test_parse_tool_request_accepts_plain_json():
    """Tool requests should parse from plain JSON output."""
    request = parse_tool_request('{"tool":"list_files","args":{"path":"."}}')

    assert request == {"tool": "list_files", "args": {"path": "."}}


def test_run_tool_lists_files(tmp_path):
    """The list_files tool should read the target directory contents."""
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "subdir").mkdir()

    result = run_tool("list_files", {"path": str(tmp_path)})

    assert "a.txt" in result["output"]
    assert "subdir/" in result["output"]


def test_execute_tool_workflow_runs_tool_and_returns_final_answer():
    """The tool workflow should loop through a tool call and then a final answer."""
    config = {
        "model": "llama3",
        "ollama_url": "http://localhost:11434/api/chat",
        "request_timeout": 120,
    }
    responses = [
        '{"tool":"system_info","args":{}}',
        "Final answer based on the tool output.",
    ]

    with patch("ollama_sgpt.tool_runtime.chat", side_effect=responses):
        answer, traces = execute_tool_workflow("summarize the system", [], config)

    assert answer == "Final answer based on the tool output."
    assert len(traces) == 1
    assert "[Tool: system_info" in traces[0]
