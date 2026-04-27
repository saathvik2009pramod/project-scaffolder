"""
Command implementations for forge's subcommands.

Each cmd_* function receives parsed argparse args.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from forge import config, output, templates
from forge.engine import render_tree


# ── helpers ──────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    """Turn 'my-cool project' → 'my_cool_project'."""
    s = name.lower().strip()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    if s and s[0].isdigit():
        s = "p_" + s
    return s or "project"


def _python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def _git_init(path: Path):
    try:
        subprocess.run(
            ["git", "init", str(path)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(path), "add", "-A"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(path), "commit", "-m", "initial commit (via forge)"],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        output.warn("git not found — skipped")
    except subprocess.CalledProcessError as e:
        output.warn(f"git init failed: {e}")


def _create_venv(path: Path):
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(path / ".venv")],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        output.warn(f"venv creation failed: {e}")


# ── forge new ────────────────────────────────────────────────────────────────

def cmd_new(args):
    name = args.name
    slug = _slugify(name)

    tpl = templates.get(args.template)
    if tpl is None:
        output.error(f"unknown template: {args.template!r}")
        output.info(f"run {output.bold('forge list')} to see available templates")
        sys.exit(1)

    author = config.resolve_author(getattr(args, "author", None))
    email  = config.resolve_email(getattr(args, "email",  None))

    # interactive fill-in for anything still missing
    if not args.dry_run:
        if not author:
            author = output.prompt("author name", default=slug)
        if not email:
            email = output.prompt("author email", default="")

    ctx = {
        "name":    name,
        "slug":    slug,
        "author":  author,
        "email":   email,
        "year":    str(date.today().year),
        "python":  _python_version(),
        "license": config.get("license", "MIT"),
        "description_placeholder": f"short description of {name}",
    }

    dest = Path.cwd() / name
    dry_run = getattr(args, "dry_run", False)

    if dest.exists() and not dry_run:
        output.error(f"directory already exists: {dest}")
        sys.exit(1)

    output.blank()
    output.step(f"scaffolding {output.bold(name)} using {output.cyan(args.template)}")
    output.blank()

    entries = render_tree(tpl["tree"], ctx, dest, dry_run=dry_run)
    output.print_tree(entries)

    if dry_run:
        output.blank()
        output.warn("dry run — nothing written")
        return

    output.blank()

    no_git  = getattr(args, "no_git",  False)
    no_venv = getattr(args, "no_venv", False)

    if not no_git:
        with output.Spinner("git init + initial commit"):
            _git_init(dest)

    if not no_venv:
        with output.Spinner("creating .venv"):
            _create_venv(dest)

    output.blank()
    output.success(f"created {output.bold(str(dest))}")
    output.blank()

    # next-steps guidance
    activate = ".venv\\Scripts\\activate" if sys.platform == "win32" else "source .venv/bin/activate"
    print(output.dim("  ─────────────────────────────────────"))
    print(f"  {output.bold('next steps')}")
    print(output.dim("  ─────────────────────────────────────"))
    output.info(f"cd {name}")
    output.info(activate)
    if tpl.get("requires"):
        pkgs = " ".join(tpl["requires"])
        output.info(f"pip install -e \".[dev]\"  # installs {pkgs} + dev tools")
    else:
        output.info('pip install -e ".[dev]"')
    output.info("make test")
    output.blank()

    if args.template == "fastapi":
        output.info(f"then: uvicorn {slug}.main:app --reload")
        output.info("docs: http://localhost:8000/docs")
        output.blank()

    if tpl.get("requires"):
        output.info(f"{output.dim('key deps:')} {', '.join(tpl['requires'])}")
        output.blank()


# ── forge list ───────────────────────────────────────────────────────────────

def cmd_list(args):
    output.blank()
    print(f"  {output.bold('available templates')}")
    output.blank()
    for name, tpl in templates.ALL.items():
        badge = output.cyan(f"{name:<12}")
        print(f"  {badge}  {tpl['description']}")
    output.blank()
    print(output.dim(f"  usage: forge new <project> --template <name>"))
    output.blank()


# ── forge info ───────────────────────────────────────────────────────────────

def cmd_info(args):
    tpl = templates.get(args.template)
    if tpl is None:
        output.error(f"no template named {args.template!r}")
        sys.exit(1)

    output.blank()
    print(f"  {output.bold(tpl['name'])}  —  {tpl['description']}")
    output.blank()

    if tpl.get("requires"):
        print(f"  {output.dim('dependencies')}  {', '.join(tpl['requires'])}")
        output.blank()

    print(f"  {output.dim('file tree')}")
    ctx = {
        "name": "myproject", "slug": "myproject",
        "author": "you", "email": "you@example.com",
        "year": str(date.today().year), "python": _python_version(),
        "license": "MIT", "description_placeholder": "...",
    }
    from forge.engine import render_tree
    entries = render_tree(tpl["tree"], ctx, Path("/tmp/__forge_preview"), dry_run=True)
    output.print_tree(entries)
    output.blank()


# ── forge config ─────────────────────────────────────────────────────────────

def cmd_config(args):
    key   = getattr(args, "key",   None)
    value = getattr(args, "value", None)

    if key and value:
        config.set_value(key, value)
        output.success(f"set {output.bold(key)} = {value}")
        return

    if key:
        val = config.get(key)
        if val:
            print(f"  {key} = {val}")
        else:
            output.warn(f"no value set for {key!r}")
        return

    # show all
    output.blank()
    print(f"  {output.bold('forge config')}  ({config.CONFIG_FILE})")
    output.blank()
    for k, v in config.all_values().items():
        val_str = output.dim("(unset)") if not v else v
        print(f"  {output.cyan(k):<20}  {val_str}")
    output.blank()
    print(output.dim("  set a value: forge config author \"Jane Smith\""))
    output.blank()
