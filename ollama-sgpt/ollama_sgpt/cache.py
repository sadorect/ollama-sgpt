"""Local on-disk response cache for opt-in prompt reuse."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def cache_directory(base_dir: Optional[Path] = None) -> Path:
    """Return the directory used for cached responses."""
    if base_dir:
        return Path(base_dir)
    return Path.home() / ".ollama-sgpt" / "cache"


def cache_entries_directory(base_dir: Optional[Path] = None) -> Path:
    """Return the directory where cache entry files are stored."""
    return cache_directory(base_dir) / "entries"


def _hash_text(value: str) -> str:
    """Return a stable SHA-256 hash for a text value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _history_hash(history: List[Dict[str, str]]) -> str:
    """Return a stable hash for message history."""
    payload = json.dumps(history, sort_keys=True, ensure_ascii=True)
    return _hash_text(payload)


def build_cache_key(
    *,
    model: str,
    role: str,
    prompt: str,
    context: str,
    shell_type: str,
    role_prompt: str,
    history: List[Dict[str, str]],
    stream: bool,
) -> str:
    """Build a stable cache key for a request."""
    payload = {
        "model": model,
        "role": role,
        "prompt": prompt,
        "context_hash": _hash_text(context or ""),
        "shell_type": shell_type or "",
        "role_prompt_hash": _hash_text(role_prompt or ""),
        "history_hash": _history_hash(history),
        "stream": stream,
    }
    return _hash_text(json.dumps(payload, sort_keys=True, ensure_ascii=True))


def cache_entry_path(cache_key: str, base_dir: Optional[Path] = None) -> Path:
    """Return the on-disk path for a cache entry."""
    return cache_entries_directory(base_dir) / f"{cache_key}.json"


def load_cache_entry(cache_key: str, base_dir: Optional[Path] = None) -> Optional[Dict]:
    """Load a cache entry without mutating hit counters."""
    path = cache_entry_path(cache_key, base_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_cache_entry(cache_key: str, base_dir: Optional[Path] = None) -> Optional[Dict]:
    """Load a cache entry and update its hit counters."""
    entry = load_cache_entry(cache_key, base_dir)
    if not entry:
        return None

    entry["hits"] = int(entry.get("hits", 0)) + 1
    entry["last_hit_at"] = datetime.now(timezone.utc).isoformat()
    cache_entry_path(cache_key, base_dir).write_text(
        json.dumps(entry, indent=2) + "\n",
        encoding="utf-8",
    )
    return entry


def save_cache_entry(
    cache_key: str,
    response: str,
    metadata: Dict[str, str],
    base_dir: Optional[Path] = None,
) -> Path:
    """Persist a cache entry to disk."""
    path = cache_entry_path(cache_key, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_cache_entry(cache_key, base_dir) or {}
    created_at = existing.get("created_at") or datetime.now(timezone.utc).isoformat()
    entry = {
        "key": cache_key,
        "created_at": created_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_hit_at": existing.get("last_hit_at"),
        "hits": int(existing.get("hits", 0)),
        "response": response,
    }
    entry.update(metadata)

    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    return path


def list_cache_entries(base_dir: Optional[Path] = None) -> List[Dict]:
    """List cached responses newest-first."""
    directory = cache_entries_directory(base_dir)
    if not directory.exists():
        return []

    entries = []
    for path in directory.glob("*.json"):
        try:
            entries.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue

    return sorted(entries, key=lambda entry: entry.get("updated_at", ""), reverse=True)


def clear_cache(base_dir: Optional[Path] = None) -> int:
    """Delete all cached response entries and return the count removed."""
    directory = cache_entries_directory(base_dir)
    if not directory.exists():
        return 0

    removed = 0
    for path in directory.glob("*.json"):
        path.unlink()
        removed += 1
    return removed
