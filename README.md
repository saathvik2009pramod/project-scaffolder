# project-scaffolder

# forge
 
I got tired of spending the first 20 minutes of every new project doing the same thing (creating the src layout, wiring up ruff, writing the same pyproject.toml for the fifth time). So I wrote this:
 
```
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
```
 
It's not trying to be the next "cookiecutter". It's a single file of templates that reflect *my* opinions, living in my dotfiles, installed with `pip install -e .`. Fork it and make it yours.
 
## install
 
```bash
git clone https://github.com/you/forge
cd forge && pip install -e .
```
 
Or if you keep a dotfiles repo, just drop it in there. The point is that it "travels" with you.
 
## usage
 
```bash
# the main thing
forge new my-service --template fastapi
forge new my-scraper --template scraper
forge new my-lib     --template py
forge new my-cli     --template cli
 
# see what you're getting before it writes anything
forge new my-api --template fastapi --dry-run
 
# other flags
--author "Your Name"   # override author (defaults to git config)
--email  you@x.com     # same for email
--no-git               # skip git init
--no-venv              # skip .venv creation
 
# explore what's available
forge list
forge info fastapi
 
# set your defaults once so you never pass --author again
forge config author "Your Name"
forge config email  you@example.com
forge config        # show everything
```
 
## templates
 
**`py`** --> a plain Python package. src layout, ruff configured, pytest, pre-commit hook. The boring correct way to start a library.
 
**`fastapi`** --> an actual FastAPI service, not a hello world. App factory pattern, routers in their own files, pydantic-settings for config, `.env.example` so you don't accidentally commit secrets, and a Dockerfile that works.
 
**`scraper`** --> async httpx with automatic retries via tenacity, selectolax for parsing (much faster than BeautifulSoup), and export helpers for both JSON and CSV. The stuff I reach for every time.
 
**`cli`** --> click + rich, with a per-user config file at `~/.config/{name}/config.toml` already wired up. The `[project.scripts]` entrypoint is set so `pip install` just works.
 
## making your own templates
 
Templates are Python dicts in `forge/templates.py`. Nested dicts become directories, string leaves become files. Everything supports variable substitution.
 
```python
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
```
 
Add to `ALL` at the bottom of the file and it shows up in `forge list` immediately.
 
Available in every template --> `{name}`, `{slug}`, `{author}`, `{email}`, `{year}`, `{python}`, `{license}`.
 
## config
 
Lives at `~/.forge/config.toml`, plain TOML, edit it directly if you want. If `author` or `email` aren't set, forge falls back to `git config user.name` and `git config user.email` automatically.
 
## no dependencies
 
Deliberately. No click, no rich, no jinja. Just argparse and some hand-rolled ANSI codes. It installs in seconds and will never break because some transitive dependency released a bad version.
 
## contributing
 
It's a personal tool so I'm not really looking for PRs that add templates reflecting your opinions rather than mine. But if something is broken or the engine has a bug, please do open an issue.
 
## project layout
 
```
forge/
├─ forge/
│  ├─ cli.py          argparse entry point
│  ├─ commands.py     new, list, info, config
│  ├─ engine.py       walks the tree dict and writes files
│  ├─ templates.py    all the templates live here
│  ├─ config.py       reads and writes ~/.forge/config.toml
│  └─ output.py       colours, spinner, prompts
└─ tests/
   └─ test_forge.py
```
