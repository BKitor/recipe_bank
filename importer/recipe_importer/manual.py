"""Interactive manual recipe entry."""

import datetime
import json
from pathlib import Path

from .importer import normalize, unique_output_path
from .utils import slugify


def _ask_optional(prompt):
    return input(prompt).strip() or None


def _ask_required(prompt):
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("  (required, please enter a value)")


def _ask_int(prompt):
    while True:
        val = input(prompt).strip()
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            print("  (please enter a whole number or leave blank)")


def _ask_tags():
    tags = []
    print('\nTags (enter one per line, "done" to finish):')
    while True:
        val = input('  Tag (or "done"): ').strip()
        if val.lower() == "done":
            break
        if val:
            tags.append(val)
    return tags


def _ask_ingredient_groups():
    groups = []
    print('\nIngredient groups — enter "done" as the group name when finished.')
    while True:
        name = input('\n  Group name (blank for ungrouped, "done" to finish): ').strip()
        if name.lower() == "done":
            break
        ingredients = []
        while True:
            ing_name = input('    Ingredient name (or "done" to finish group): ').strip()
            if ing_name.lower() == "done":
                break
            amount = input("      Amount (blank if none): ").strip()
            unit = input("      Unit (blank if none): ").strip()
            notes = input("      Notes (blank if none): ").strip()
            ingredients.append({"amount": amount, "unit": unit, "name": ing_name, "notes": notes})
        groups.append({"name": name, "ingredients": ingredients})
    return groups


def _ask_instruction_groups():
    groups = []
    print('\nInstruction groups — enter "done" as the group name when finished.')
    while True:
        name = input('\n  Group name (blank for ungrouped, "done" to finish): ').strip()
        if name.lower() == "done":
            break
        steps = []
        while True:
            step = input('    Step (or "done" to finish group): ').strip()
            if step.lower() == "done":
                break
            if step:
                steps.append(step)
        groups.append({"name": name, "steps": steps})
    return groups


def _ask_notes():
    print('\nNotes (enter lines, "done" to finish, blank line + "done" to skip):')
    lines = []
    while True:
        line = input("  ").strip()
        if line.lower() == "done":
            break
        lines.append(line)
    return "\n".join(lines) if lines else None


def prompt_recipe():
    """Prompt the user for all recipe fields and return a raw data dict."""
    print("=== Manual Recipe Entry ===\n")

    title = _ask_required("Title: ")
    source_url = _ask_optional("Source URL (blank to skip): ")
    description = _ask_optional("Description (blank to skip): ")
    prep_time_min = _ask_int("Prep time in minutes (blank to skip): ")
    cook_time_min = _ask_int("Cook time in minutes (blank to skip): ")
    total_time_min = _ask_int("Total time in minutes (blank to skip): ")
    servings = _ask_optional("Servings (blank to skip): ")
    tags = _ask_tags()
    ingredient_groups = _ask_ingredient_groups()
    instruction_groups = _ask_instruction_groups()
    notes = _ask_notes()

    return {
        "title": title,
        "source_url": source_url,
        "description": description,
        "prep_time_min": prep_time_min,
        "cook_time_min": cook_time_min,
        "total_time_min": total_time_min,
        "servings": servings,
        "tags": tags,
        "ingredient_groups": ingredient_groups,
        "instruction_groups": instruction_groups,
        "notes": notes,
    }


def run_manual_entry(out_dir=None, dry_run=False):
    if out_dir is None:
        out_dir = Path(__file__).parent.parent.parent / "src" / "recipes"
    out_dir = Path(out_dir)

    data = prompt_recipe()
    data = normalize(data)

    slug = slugify(data["title"])
    data["id"] = slug
    data["date_added"] = datetime.date.today().isoformat()

    if dry_run:
        print(f"\n[dry-run] Would write: {out_dir}/{slug}.json")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path, final_slug = unique_output_path(out_dir, slug)
    if final_slug != slug:
        print(f"WARNING: slug collision, using {final_slug}")
        data["id"] = final_slug

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten: {out_path}")
    return data
