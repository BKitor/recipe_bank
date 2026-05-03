"""CLI entry point for recipe-importer."""

import argparse
import sys
import traceback
from pathlib import Path

from .importer import import_file


def main():
    parser = argparse.ArgumentParser(
        prog="recipe-importer",
        description="Import recipe HTML files into src/recipes/*.json",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="FILE_OR_DIR",
        help=".html files or a directory of .html files (e.g. Recipes/)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="DIR",
        help="output directory for JSON files (default: src/recipes/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="parse and print without writing files or downloading images",
    )
    args = parser.parse_args()

    out_dir = Path(args.output) if args.output else None

    files = []
    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            files.extend(sorted(p.glob("*.html")))
            files.extend(sorted(p.glob("*.htm")))
            files.extend(sorted(p.glob("*.pdf")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"ERROR: not found: {inp}", file=sys.stderr)
            sys.exit(1)

    if not files:
        print("No recipe files found.", file=sys.stderr)
        sys.exit(1)

    errors = []
    for f in files:
        try:
            import_file(f, out_dir=out_dir, dry_run=args.dry_run)
        except Exception:
            traceback.print_exc()
            errors.append(f.name)
        print()

    if len(files) > 1:
        print(f"Done: {len(files) - len(errors)}/{len(files)} imported successfully.")
    if errors:
        print("Failed:", ", ".join(errors))
        sys.exit(1)


if __name__ == "__main__":
    main()
