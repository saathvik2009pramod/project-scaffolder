# project-scaffolder

forge

I got tired of starting every new project the same way every time. Setting up the src folder, configuring ruff, rewriting the same pyproject.toml again and again. It felt repetitive and honestly a waste of time, so I made this.

$ forge new my-api --template fastapi

  scaffolding my-api using fastapi

  ├─ src/
     ├─ my_api/
        ├─ __init__.py
        ├─ main.py
        ├─ settings.py
        ├─ routers/
           ├─ health.py
           └─ items.py
  ├─ tests/
  ├─ pyproject.toml
  ├─ .env.example
  ├─ Dockerfile
  └─ .gitignore

  ✓ git init + initial commit
  ✓ creating .venv
  ✓ created /Users/you/my-api

  next steps
  ─────────────────────────────
  · cd my-api
  · source .venv/bin/activate
  · pip install -e ".[dev]"
  · make test

This is not meant to replace something like cookiecutter or be some big framework. It is just a simple tool that sets up projects the way I like them. Everything is in one file, and I keep it in my dotfiles so I can use it anywhere. You can change it however you want.

install
git clone https://github.com/you/forge
cd forge && pip install -e .

Or just add it to your dotfiles. That is kind of the whole point.

usage
forge new my-service --template fastapi
forge new my-scraper --template scraper
forge new my-lib     --template py
forge new my-cli     --template cli

forge new my-api --template fastapi --dry-run

--author "Your Name"
--email  you@x.com
--no-git
--no-venv

forge list
forge info fastapi

forge config author "Your Name"
forge config email  you@example.com
forge config
templates

py
A basic Python package with a clean structure. It includes ruff, pytest, and pre commit setup. Just a simple and correct starting point.

fastapi
A proper FastAPI setup, not just a hello world. It has routers, config handling, and a working Dockerfile.

scraper
Uses async httpx with retries and a fast HTML parser. Also includes exporting to JSON and CSV.

cli
Built with click and rich, with config already set up so it works right after install.

making your own templates

Templates are just Python dictionaries in templates.py. You can add your own easily.

MY_TEMPLATE = {
    "name": "mytemplate",
    "description": "does a thing",
    "requires": ["requests"],
    "tree": {
        "src": {
            "{slug}": {
                "__init__.py": '__version__ = "0.1.0"\n',
                "main.py": "# {name}\n\ndef run():\n    pass\n",
            }
        },
        "README.md": "# {name}\n\n> todo\n",
    },
}

Add it to the list and it shows up immediately.

config

Stored in ~/.forge/config.toml. You can edit it directly or use the command.

If you do not set author or email, it just uses your git config automatically.

no dependencies

This tool is intentionally simple. No external libraries, just argparse and basic Python. It installs fast and does not break randomly.

contributing

This is mainly a personal tool, so I am not really looking for big changes. But if something is broken, feel free to report it.

project layout
forge/
├─ forge/
│  ├─ cli.py
│  ├─ commands.py
│  ├─ engine.py
│  ├─ templates.py
│  ├─ config.py
│  └─ output.py
└─ tests/
   └─ test_forge.py
