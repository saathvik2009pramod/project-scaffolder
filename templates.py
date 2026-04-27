"""
Built-in project templates.

Each template is a dict with:
  name        - short id used on CLI
  description - one-liner shown in `forge list`
  requires    - pip packages to mention in README
  tree        - FileTree dict (nested dicts = dirs, str leaves = file contents)

Context variables available everywhere:
  {name}       - project name as given
  {slug}       - name lowercased, spaces/hyphens → underscores (valid pkg name)
  {author}     - resolved author name
  {email}      - resolved email
  {year}       - current year
  {python}     - python version string e.g. "3.12"
  {license}    - license spdx id
"""

# ── helpers ──────────────────────────────────────────────────────────────────

_PYPROJECT_COMMON = """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = ""
authors = [{{ name = "{author}", email = "{email}" }}]
readme = "README.md"
license = {{ text = "{license}" }}
requires-python = ">={python}"
dependencies = {deps}

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

_GITIGNORE = """\
# python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# env
.venv/
venv/
.env
.env.*
!.env.example

# tools
.ruff_cache/
.mypy_cache/
.pytest_cache/
.coverage
htmlcov/

# editors
.idea/
.vscode/
*.swp
"""

_MAKEFILE = """\
.PHONY: install test lint fmt check clean

install:
\tpip install -e ".[dev]"

test:
\tpytest -v

lint:
\truff check .

fmt:
\truff format .

check: lint test

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {{}} +
\trm -rf dist build .coverage htmlcov
"""

_PRE_COMMIT = """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
"""

# ── plain python ─────────────────────────────────────────────────────────────

PY = {
    "name": "py",
    "description": "plain python package — src layout, ruff, pytest, pre-commit",
    "requires": [],
    "tree": {
        "src": {
            "{slug}": {
                "__init__.py": '"""\\n{name}\\n"""\n\n__version__ = "0.1.0"\n',
                "main.py": '"""Entry point."""\n\n\ndef run():\n    print("hello from {name}")\n\n\nif __name__ == "__main__":\n    run()\n',
            }
        },
        "tests": {
            "__init__.py": "",
            "test_{slug}.py": 'from {slug} import __version__\n\n\ndef test_version():\n    assert __version__ == "0.1.0"\n',
        },
        "pyproject.toml": _PYPROJECT_COMMON.replace("{deps}", "[]") + """
[project.optional-dependencies]
dev = ["pytest", "ruff"]
""",
        "README.md": "# {name}\n\n> {description_placeholder}\n\n## setup\n\n```bash\npython -m venv .venv && source .venv/bin/activate\npip install -e \".[dev]\"\n```\n\n## usage\n\n```python\nfrom {slug} import run\nrun()\n```\n\n## dev\n\n```bash\nmake test\nmake lint\n```\n",
        ".gitignore": _GITIGNORE,
        "Makefile": _MAKEFILE,
        ".pre-commit-config.yaml": _PRE_COMMIT,
    },
}

# ── fastapi ──────────────────────────────────────────────────────────────────

FASTAPI = {
    "name": "fastapi",
    "description": "fastapi service — routers, pydantic schemas, settings, dockerfile",
    "requires": ["fastapi", "uvicorn[standard]", "pydantic-settings"],
    "tree": {
        "src": {
            "{slug}": {
                "__init__.py": '"""\\n{name} API\\n"""\n\n__version__ = "0.1.0"\n',
                "main.py": '''\
"""Application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers import health, items
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(items.router, prefix="/items")
    return app


app = create_app()
''',
                "settings.py": '''\
"""App-wide settings via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "{name}"
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()
''',
                "routers": {
                    "__init__.py": "",
                    "health.py": '''\
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}
''',
                    "items.py": '''\
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["items"])

_store: dict[int, dict] = {}
_seq = 0


class ItemIn(BaseModel):
    name: str
    description: str = ""


class ItemOut(ItemIn):
    id: int


@router.get("/", response_model=list[ItemOut])
async def list_items():
    return list(_store.values())


@router.post("/", response_model=ItemOut, status_code=201)
async def create_item(body: ItemIn):
    global _seq
    _seq += 1
    item = {"id": _seq, **body.model_dump()}
    _store[_seq] = item
    return item


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: int):
    if item_id not in _store:
        raise HTTPException(404, "item not found")
    return _store[item_id]


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int):
    if item_id not in _store:
        raise HTTPException(404, "item not found")
    del _store[item_id]
''',
                },
            }
        },
        "tests": {
            "__init__.py": "",
            "test_health.py": '''\
from fastapi.testclient import TestClient
from {slug}.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
''',
        },
        "pyproject.toml": _PYPROJECT_COMMON.replace(
            "{deps}", '[\n  "fastapi",\n  "uvicorn[standard]",\n  "pydantic-settings",\n]'
        ) + """
[project.optional-dependencies]
dev = ["pytest", "httpx", "ruff"]

[project.scripts]
serve = "{slug}.main:app"
""",
        ".env.example": "APP_NAME={name}\nDEBUG=false\nLOG_LEVEL=INFO\n",
        "README.md": "# {name}\n\nFastAPI service.\n\n## setup\n\n```bash\npython -m venv .venv && source .venv/bin/activate\npip install -e \".[dev]\"\n```\n\n## run\n\n```bash\nuvicorn {slug}.main:app --reload\n```\n\nDocs at http://localhost:8000/docs\n\n## test\n\n```bash\nmake test\n```\n",
        ".gitignore": _GITIGNORE,
        "Makefile": _MAKEFILE + "\nserve:\n\tuvicorn {slug}.main:app --reload\n",
        ".pre-commit-config.yaml": _PRE_COMMIT,
        "Dockerfile": '''\
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/

EXPOSE 8000
CMD ["uvicorn", "{slug}.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
    },
}

# ── scraper ──────────────────────────────────────────────────────────────────

SCRAPER = {
    "name": "scraper",
    "description": "async scraper — httpx, playwright ready, rate limiting, csv/json export",
    "requires": ["httpx", "selectolax", "tenacity", "rich"],
    "tree": {
        "src": {
            "{slug}": {
                "__init__.py": '"""\\n{name} scraper\\n"""\n\n__version__ = "0.1.0"\n',
                "http.py": '''\
"""Shared async HTTP client with retries and rate limiting."""

import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; {name}/0.1)",
    "Accept-Language": "en-US,en;q=0.9",
}


def make_client(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(10.0),
        **kwargs,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch(client: httpx.AsyncClient, url: str) -> httpx.Response:
    resp = await client.get(url)
    resp.raise_for_status()
    return resp
''',
                "parse.py": '''\
"""HTML parsing helpers using selectolax."""

from selectolax.parser import HTMLParser


def parse_html(html: str) -> HTMLParser:
    return HTMLParser(html)


def text(node, selector: str, default: str = "") -> str:
    el = node.css_first(selector)
    return el.text(strip=True) if el else default


def attr(node, selector: str, attribute: str, default: str = "") -> str:
    el = node.css_first(selector)
    return el.attributes.get(attribute, default) if el else default
''',
                "export.py": '''\
"""Write results to CSV or JSON."""

import csv
import json
from pathlib import Path
from typing import Any


def to_json(data: list[dict[str, Any]], path: Path):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def to_csv(data: list[dict[str, Any]], path: Path):
    if not data:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
''',
                "main.py": '''\
"""CLI entry point."""

import asyncio
import argparse
from pathlib import Path

from .http import make_client, fetch
from .parse import parse_html, text
from .export import to_json, to_csv


async def scrape(urls: list[str]) -> list[dict]:
    results = []
    async with make_client() as client:
        for url in urls:
            resp = await fetch(client, url)
            doc = parse_html(resp.text)
            results.append({
                "url": url,
                "title": text(doc, "title"),
                "h1": text(doc, "h1"),
            })
    return results


def main():
    p = argparse.ArgumentParser(prog="{slug}")
    p.add_argument("urls", nargs="+", help="URLs to scrape")
    p.add_argument("-o", "--output", default="results.json")
    args = p.parse_args()

    results = asyncio.run(scrape(args.urls))
    out = Path(args.output)

    if out.suffix == ".csv":
        to_csv(results, out)
    else:
        to_json(results, out)

    print(f"saved {len(results)} results → {out}")


if __name__ == "__main__":
    main()
''',
            }
        },
        "tests": {
            "__init__.py": "",
            "test_parse.py": '''\
from {slug}.parse import parse_html, text


def test_parse_title():
    html = "<html><head><title>Hello</title></head><body><h1>World</h1></body></html>"
    doc = parse_html(html)
    assert text(doc, "title") == "Hello"
    assert text(doc, "h1") == "World"
    assert text(doc, "p", "fallback") == "fallback"
''',
        },
        "pyproject.toml": _PYPROJECT_COMMON.replace(
            "{deps}", '[\n  "httpx",\n  "selectolax",\n  "tenacity",\n  "rich",\n]'
        ) + """
[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "respx", "ruff"]

[project.scripts]
{slug} = "{slug}.main:main"
""",
        "README.md": "# {name}\n\nAsync web scraper.\n\n## setup\n\n```bash\npython -m venv .venv && source .venv/bin/activate\npip install -e \".[dev]\"\n```\n\n## usage\n\n```bash\n{slug} https://example.com -o results.json\n{slug} https://example.com -o results.csv\n```\n",
        ".gitignore": _GITIGNORE + "\n# scraper output\nresults.json\nresults.csv\n",
        "Makefile": _MAKEFILE,
        ".pre-commit-config.yaml": _PRE_COMMIT,
    },
}

# ── CLI tool ─────────────────────────────────────────────────────────────────

CLI = {
    "name": "cli",
    "description": "polished CLI tool — click, rich output, config file, packaging",
    "requires": ["click", "rich"],
    "tree": {
        "src": {
            "{slug}": {
                "__init__.py": '"""\\n{name}\\n"""\n\n__version__ = "0.1.0"\n',
                "cli.py": '''\
"""CLI commands."""

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option()
def cli():
    """{name} — describe your tool here."""


@cli.command()
@click.argument("name")
@click.option("--count", "-n", default=1, show_default=True, help="how many times")
def greet(name: str, count: int):
    """greet NAME."""
    for _ in range(count):
        console.print(f"[bold green]hello[/], {name}!")


@cli.command()
def status():
    """show current status."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("key")
    table.add_column("value")
    table.add_row("version", "0.1.0")
    table.add_row("status", "[green]ok[/]")
    console.print(table)


def main():
    cli()
''',
                "config.py": '''\
"""Config stored in ~/.config/{name}/config.toml."""

import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "{slug}"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    text = CONFIG_FILE.read_text()
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(text)
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip(\'"\')
    return result


def save(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f\'{k} = "{v}"\\n\' for k, v in data.items()]
    CONFIG_FILE.write_text("".join(lines))
''',
            }
        },
        "tests": {
            "__init__.py": "",
            "test_cli.py": '''\
from click.testing import CliRunner
from {slug}.cli import cli


def test_greet():
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "world"])
    assert result.exit_code == 0
    assert "world" in result.output


def test_status():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
''',
        },
        "pyproject.toml": _PYPROJECT_COMMON.replace(
            "{deps}", '[\n  "click",\n  "rich",\n]'
        ) + """
[project.optional-dependencies]
dev = ["pytest", "ruff"]

[project.scripts]
{slug} = "{slug}.cli:main"
""",
        "README.md": "# {name}\n\n## install\n\n```bash\npip install -e .\n```\n\n## usage\n\n```bash\n{slug} greet world\n{slug} status\n{slug} --help\n```\n",
        ".gitignore": _GITIGNORE,
        "Makefile": _MAKEFILE,
        ".pre-commit-config.yaml": _PRE_COMMIT,
    },
}


# ── registry ─────────────────────────────────────────────────────────────────

ALL: dict[str, dict] = {
    t["name"]: t for t in [PY, FASTAPI, SCRAPER, CLI]
}


def get(name: str) -> dict | None:
    return ALL.get(name)
