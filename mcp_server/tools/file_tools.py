from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from .sandbox import ensure_text_size_within_limit, resolve_path_in_workspace, validate_relative_path


def create_file_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    relative_path = str(arguments.get("relative_path", "")).strip()
    content = str(arguments.get("content", ""))
    overwrite = bool(arguments.get("overwrite", False))

    validate_relative_path(relative_path)
    ensure_text_size_within_limit(content)
    target = resolve_path_in_workspace(workspace_root, relative_path)

    if target.exists() and target.is_dir():
        raise ValueError("Target path is a directory")
    if target.exists() and not overwrite:
        raise ValueError("File already exists; set overwrite=true to replace")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "path": str(target),
        "relative_path": relative_path,
        "bytes_written": len(content.encode("utf-8")),
        "overwritten": overwrite and target.exists(),
    }


def read_file_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    relative_path = str(arguments.get("relative_path", "")).strip()
    max_bytes = int(arguments.get("max_bytes", 65536))

    validate_relative_path(relative_path)
    if max_bytes < 1 or max_bytes > 200000:
        raise ValueError("max_bytes must be between 1 and 200000")

    target = resolve_path_in_workspace(workspace_root, relative_path)
    if not target.exists() or not target.is_file():
        raise ValueError("Requested file does not exist")

    raw = target.read_bytes()
    chunk = raw[:max_bytes]
    return {
        "ok": True,
        "path": str(target),
        "relative_path": relative_path,
        "truncated": len(raw) > max_bytes,
        "size_bytes": len(raw),
        "content": chunk.decode("utf-8", errors="replace"),
    }


def list_directory_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    relative_path = str(arguments.get("relative_path", ".")).strip() or "."
    include_hidden = bool(arguments.get("include_hidden", False))

    validate_relative_path(relative_path)
    target = resolve_path_in_workspace(workspace_root, relative_path)
    if not target.exists() or not target.is_dir():
        raise ValueError("Requested directory does not exist")

    entries: list[dict[str, Any]] = []
    for item in sorted(target.iterdir(), key=lambda value: value.name):
        if not include_hidden and item.name.startswith("."):
            continue
        entries.append(
            {
                "name": item.name,
                "is_dir": item.is_dir(),
                "is_file": item.is_file(),
            }
        )

    return {
        "ok": True,
        "path": str(target),
        "relative_path": relative_path,
        "entries": entries,
        "count": len(entries),
    }


def append_to_file_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    relative_path = str(arguments.get("relative_path", "")).strip()
    content = str(arguments.get("content", ""))
    ensure_newline = bool(arguments.get("ensure_newline", True))

    validate_relative_path(relative_path)
    ensure_text_size_within_limit(content)
    target = resolve_path_in_workspace(workspace_root, relative_path)
    if not target.exists() or not target.is_file():
        raise ValueError("Target file does not exist")

    existing = target.read_text(encoding="utf-8", errors="replace")
    payload = content
    if ensure_newline and existing and not existing.endswith("\n"):
        payload = "\n" + payload

    target.write_text(existing + payload, encoding="utf-8")
    return {
        "ok": True,
        "path": str(target),
        "relative_path": relative_path,
        "bytes_appended": len(payload.encode("utf-8")),
    }


def insert_after_marker_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    relative_path = str(arguments.get("relative_path", "")).strip()
    marker = str(arguments.get("marker", ""))
    content = str(arguments.get("content", ""))
    occurrence = str(arguments.get("occurrence", "first")).strip().lower() or "first"

    if occurrence not in {"first", "last"}:
        raise ValueError("occurrence must be 'first' or 'last'")

    validate_relative_path(relative_path)
    ensure_text_size_within_limit(content)
    target = resolve_path_in_workspace(workspace_root, relative_path)
    if not target.exists() or not target.is_file():
        raise ValueError("Target file does not exist")

    source = target.read_text(encoding="utf-8", errors="replace")
    position = source.find(marker) if occurrence == "first" else source.rfind(marker)
    if position == -1:
        raise ValueError("marker not found in file")

    insert_at = position + len(marker)
    updated = source[:insert_at] + content + source[insert_at:]
    target.write_text(updated, encoding="utf-8")
    return {
        "ok": True,
        "path": str(target),
        "relative_path": relative_path,
        "marker": marker,
        "occurrence": occurrence,
        "bytes_inserted": len(content.encode("utf-8")),
    }


def replace_range_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    relative_path = str(arguments.get("relative_path") or arguments.get("file_path") or "").strip()
    start_line = int(arguments.get("start_line", 0))
    end_line = int(arguments.get("end_line", 0))
    has_content_key = "content" in arguments
    has_replacement_key = "replacement_text" in arguments
    content = str(arguments.get("content") if has_content_key else arguments.get("replacement_text", ""))
    allow_empty = bool(arguments.get("allow_empty", False))

    if not (has_content_key or has_replacement_key):
        raise ValueError("replace_range requires 'content' or 'replacement_text'")
    if not content and not allow_empty:
        raise ValueError("replace_range replacement text is empty; set allow_empty=true to explicitly delete range")

    validate_relative_path(relative_path)
    ensure_text_size_within_limit(content)
    if start_line < 1 or end_line < start_line:
        raise ValueError("start_line/end_line are invalid")

    target = resolve_path_in_workspace(workspace_root, relative_path)
    if target.exists() and target.is_dir():
        raise ValueError("Target path is a directory")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")

    source = target.read_text(encoding="utf-8", errors="replace")
    lines = source.splitlines(keepends=True)

    start_idx = min(max(start_line - 1, 0), len(lines))
    end_idx = min(max(end_line, start_idx), len(lines))

    replacement = content
    if replacement and not replacement.endswith("\n") and any(line.endswith("\n") for line in lines):
        replacement = replacement + "\n"

    updated_lines = lines[:start_idx] + [replacement] + lines[end_idx:]
    updated = "".join(updated_lines)
    target.write_text(updated, encoding="utf-8")
    return {
        "ok": True,
        "path": str(target),
        "relative_path": relative_path,
        "start_line": start_line,
        "end_line": end_line,
        "effective_start_line": start_idx + 1,
        "effective_end_line": end_idx,
        "bytes_written": len(replacement.encode("utf-8")),
    }


def search_files_tool(arguments: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    pattern = str(arguments.get("pattern", "**/*")).strip()
    content_query = str(arguments.get("content_query", "")).strip()
    max_results = min(int(arguments.get("max_results", 50)), 200)

    # Reject absolute paths or traversal attempts
    if pattern.startswith("/") or ".." in pattern:
        raise ValueError("Pattern must be relative (no leading '/' or '..')")

    # Collect all files under workspace, then match against pattern
    all_files: list[Path] = []
    try:
        all_files = [p for p in workspace_root.rglob("*") if p.is_file()]
    except Exception as exc:
        raise ValueError(f"Could not list workspace: {exc}") from exc

    # fnmatch against the relative path string so ** acts like a path wildcard
    matched: list[Path] = []
    for f in all_files:
        rel = str(f.relative_to(workspace_root))
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f.name, pattern):
            matched.append(f)

    results: list[dict[str, Any]] = []
    for f in matched:
        if len(results) >= max_results:
            break
        rel = str(f.relative_to(workspace_root))
        entry: dict[str, Any] = {"path": rel, "size_bytes": f.stat().st_size}

        if content_query:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            lower_text = text.lower()
            lower_query = content_query.lower()
            if lower_query not in lower_text:
                continue  # skip files that don't contain the query
            hits = [
                {"line": i + 1, "content": line.rstrip()}
                for i, line in enumerate(text.splitlines())
                if lower_query in line.lower()
            ]
            entry["matches"] = hits[:10]

        results.append(entry)

    return {
        "ok": True,
        "pattern": pattern,
        "content_query": content_query if content_query else None,
        "count": len(results),
        "files": results,
    }
