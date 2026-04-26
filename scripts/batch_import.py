#!/usr/bin/env python3
# pyright: basic
"""batch_import.py — Import all recipe files from the Recipes/ directory."""

import sys
import traceback
from pathlib import Path
from import_recipe import import_file

RECIPES_DIR = Path(__file__).parent.parent / "Recipes"

def main():
    dry_run = "--dry-run" in sys.argv
    files = sorted(RECIPES_DIR.glob("*.html")) + sorted(RECIPES_DIR.glob("*.pdf"))

    if not files:
        print(f"No recipe files found in {RECIPES_DIR}")
        sys.exit(1)

    print(f"Found {len(files)} files to import.\n")
    errors = []

    for f in files:
        try:
            import_file(f, dry_run=dry_run)
        except Exception:
            traceback.print_exc()
            errors.append(f.name)
        print()

    print(f"\nDone. {len(files) - len(errors)}/{len(files)} imported successfully.")
    if errors:
        print("\nFailed files:")
        for name in errors:
            print(f"  {name}")

if __name__ == "__main__":
    main()
