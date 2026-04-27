"""forge — spin up projects with your opinions baked in."""

import sys
import argparse
from forge import commands


def main():
    parser = argparse.ArgumentParser(
        prog="forge",
        description="spin up projects with your opinions baked in",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  forge new my-api --template fastapi
  forge new scraper --template scraper --author "Jane Smith"
  forge list
  forge info fastapi
        """,
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # forge new
    p_new = sub.add_parser("new", help="scaffold a new project")
    p_new.add_argument("name", help="project name (used for directory + package)")
    p_new.add_argument(
        "--template", "-t",
        default="py",
        metavar="TEMPLATE",
        help="template to use (default: py)",
    )
    p_new.add_argument("--author", "-a", metavar="NAME", help="author name")
    p_new.add_argument("--email", "-e", metavar="EMAIL", help="author email")
    p_new.add_argument(
        "--no-git", action="store_true", help="skip git init"
    )
    p_new.add_argument(
        "--no-venv", action="store_true", help="skip virtual environment creation"
    )
    p_new.add_argument(
        "--dry-run", action="store_true", help="show what would be created without writing"
    )

    # forge list
    sub.add_parser("list", help="list available templates")

    # forge info
    p_info = sub.add_parser("info", help="show template details")
    p_info.add_argument("template", help="template name")

    # forge config
    p_cfg = sub.add_parser("config", help="get/set default config values")
    p_cfg.add_argument("key", nargs="?", help="config key (e.g. author)")
    p_cfg.add_argument("value", nargs="?", help="value to set")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "new":    commands.cmd_new,
        "list":   commands.cmd_list,
        "info":   commands.cmd_info,
        "config": commands.cmd_config,
    }

    try:
        dispatch[args.command](args)
    except KeyboardInterrupt:
        print("\naborted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
