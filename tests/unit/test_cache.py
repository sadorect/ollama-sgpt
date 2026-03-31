"""Tests for the local cache helpers."""

from ollama_sgpt.cache import (
    build_cache_key,
    clear_cache,
    get_cache_entry,
    list_cache_entries,
    save_cache_entry,
)


def test_build_cache_key_changes_with_context_and_role_prompt():
    """Cache keys should change when prompt-affecting inputs change."""
    base = dict(
        model="llama3",
        role="default",
        prompt="hello",
        context="",
        shell_type="bash",
        role_prompt="",
        history=[],
        stream=False,
    )

    key_a = build_cache_key(**base)
    key_b = build_cache_key(**{**base, "context": "extra"})
    key_c = build_cache_key(**{**base, "role_prompt": "You are a reviewer."})

    assert key_a != key_b
    assert key_a != key_c


def test_save_and_get_cache_entry_updates_hits(tmp_path):
    """Reading a cached response should increment its hit counter."""
    save_cache_entry(
        "abc123",
        "hello",
        {"model": "llama3", "role_name": "default", "prompt_preview": "hello"},
        tmp_path,
    )

    entry = get_cache_entry("abc123", tmp_path)

    assert entry["response"] == "hello"
    assert entry["hits"] == 1
    assert entry["last_hit_at"]


def test_list_and_clear_cache_entries(tmp_path):
    """Cache entries should be listable and removable."""
    save_cache_entry(
        "first",
        "one",
        {"model": "llama3", "role_name": "default", "prompt_preview": "one"},
        tmp_path,
    )
    save_cache_entry(
        "second",
        "two",
        {"model": "llama3", "role_name": "default", "prompt_preview": "two"},
        tmp_path,
    )

    entries = list_cache_entries(tmp_path)
    removed = clear_cache(tmp_path)

    assert len(entries) == 2
    assert removed == 2
    assert list_cache_entries(tmp_path) == []
