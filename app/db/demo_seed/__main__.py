"""CLI entrypoint for demo seeding.

Usage:

    python -m app.db.demo_seed --seed-surf-demo
    python -m app.db.demo_seed --seed-surf-demo --replace
"""
# Parse the demo-seed CLI flags and delegate all writes to the seed helper.

from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS — DEMO-SEED CLI ENTRY POINT
# --------------------------------------------------------------------------- #
# Simple explanation:
# This file is what runs when you type `python -m app.db.demo_seed`. It
# parses command-line flags, then hands all real database work to the
# seeding helper.
import argparse
import json
import sys

from app.db.demo_seed import seed_surf_demo_class


# --------------------------------------------------------------------------- #
# CLI FLAG BUILDER AND MAIN
# --------------------------------------------------------------------------- #
# Simple explanation:
# `_build_parser` declares the two flags: `--seed-surf-demo` to run the
# seeder, and `--replace` to refresh an existing marked demo graph. `main`
# parses the flags, calls the seed function, prints the result as JSON, and
# returns the exit code.


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed helper commands")
    parser.add_argument(
        "--seed-surf-demo",
        action="store_true",
        help="Seed or refresh the official local demo class named Surf",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing marked Surf demo class graph",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.seed_surf_demo:
        parser.print_help()
        return 0

    result = seed_surf_demo_class(replace=args.replace)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
