"""
Template engine.

A template is a dict[str, str | dict] — nested dicts become directories,
string leaves become files. All values are rendered with simple {var} substitution.
Keys can also contain {var} substitutions (for dynamic filenames).
"""

from __future__ import annotations
import re
import string
from pathlib import Path
from typing import Union


FileTree = dict[str, Union[str, "FileTree"]]


class TemplateError(ValueError):
    pass


class SafeTemplate(string.Template):
    """Like string.Template but leaves unknown {vars} intact instead of raising."""
    delimiter = "{"

    # Override pattern to match {VAR} style
    pattern = r"""
        \{(?:
          (?P<escaped>\{)         |  # {{ → {
          (?P<named>[_a-zA-Z][_a-zA-Z0-9]*)
          \}                      |  # {var}
          (?P<braced>)               # (unused)
          |
          (?P<invalid>)
        )
    """


def render_str(template: str, ctx: dict) -> str:
    """Replace {key} placeholders in template string."""
    def replacer(m):
        key = m.group(1)
        return str(ctx.get(key, m.group(0)))
    return re.sub(r"\{([_a-zA-Z][_a-zA-Z0-9]*)\}", replacer, template)


def render_tree(tree: FileTree, ctx: dict, root: Path, dry_run: bool = False) -> list[tuple[str, str]]:
    """
    Walk the tree dict, render each file, and write to disk.
    Returns a flat list of (relative_path, kind) for display.
    """
    entries = []
    _walk(tree, ctx, root, Path(""), entries, dry_run)
    return entries


def _walk(
    node: FileTree,
    ctx: dict,
    root: Path,
    rel: Path,
    entries: list,
    dry_run: bool,
):
    for raw_key, value in node.items():
        key = render_str(raw_key, ctx)
        child_rel = rel / key

        if isinstance(value, dict):
            entries.append((str(child_rel), "dir"))
            if not dry_run:
                (root / child_rel).mkdir(parents=True, exist_ok=True)
            _walk(value, ctx, root, child_rel, entries, dry_run)
        else:
            entries.append((str(child_rel), "file"))
            content = render_str(value, ctx)
            if not dry_run:
                target = root / child_rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
