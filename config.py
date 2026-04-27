"""Persist user config to ~/.forge/config.toml (stdlib tomllib / tomli fallback)."""

import os
import sys
from pathlib import Path

CONFIG_DIR  = Path.home() / ".forge"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "author": "",
    "email":  "",
    "github": "",
    "license": "MIT",
}


def _load_raw() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    text = CONFIG_FILE.read_text()
    # stdlib tomllib (3.11+) or manual parse
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(text)
    return _parse_toml(text)


def _parse_toml(text: str) -> dict:
    """Minimal TOML parser — only handles flat key = "value" lines."""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            result[k] = v
    return result


def _write_raw(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# forge config\n"]
    for k, v in data.items():
        lines.append(f'{k} = "{v}"\n')
    CONFIG_FILE.write_text("".join(lines))


def get(key: str, fallback: str = "") -> str:
    raw = _load_raw()
    return raw.get(key, DEFAULTS.get(key, fallback))


def set_value(key: str, value: str):
    raw = _load_raw()
    raw[key] = value
    _write_raw(raw)


def all_values() -> dict:
    raw = _load_raw()
    merged = dict(DEFAULTS)
    merged.update(raw)
    return merged


def resolve_author(args_author=None) -> str:
    if args_author:
        return args_author
    cfg = get("author")
    if cfg:
        return cfg
    # try git config as last resort
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "config", "user.name"], stderr=subprocess.DEVNULL, text=True
        )
        return out.strip()
    except Exception:
        return ""


def resolve_email(args_email=None) -> str:
    if args_email:
        return args_email
    cfg = get("email")
    if cfg:
        return cfg
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "config", "user.email"], stderr=subprocess.DEVNULL, text=True
        )
        return out.strip()
    except Exception:
        return ""
