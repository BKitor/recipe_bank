"""Regenerate test fixtures from the current parser output.

Run this after any intentional parser change to update snapshots:
    python scripts/tests/gen_fixtures.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup

from recipe_importer.importer import normalize
from recipe_importer.parsers import (
    parse_based_cooking,
    parse_generic_html,
    parse_jetpack,
    parse_json_ld,
    parse_serious_eats,
    parse_tasty,
    parse_wprm_html,
    parse_wprm_js,
)

FIXTURES = Path(__file__).parent / "fixtures"
RECIPES = Path(__file__).parent.parent.parent / "Recipes"

CASES = [
    ("wprm_js",               "Arayes.html",                                      parse_wprm_js),
    ("wprm_html",             "ChickenTikkaMasala.html",                           parse_wprm_html),
    ("serious_eats",          "risotto-serious-eats.html",                         parse_serious_eats),
    ("tasty",                 "Beef Stroganoff.html",                              parse_tasty),
    ("json_ld",               "ChickenMarsala.html",                              parse_json_ld),
    ("json_ld_list",          "Coconut-LimeChicken.html",                         parse_json_ld),
    ("jetpack",               "turkey meatloaf for skeptics.html",                parse_jetpack),
    ("based_cooking",         "Tajine Maadnous _ Based Cooking.html",             parse_based_cooking),
    ("generic_html_multi",    "carnitas_bowl_meal_prep.OpenClanker.html",         parse_generic_html),
    ("generic_html_flat",     "CauliflowerChickenAlfredo.html",                   parse_generic_html),
    ("generic_html_korean",   "korean_red_beans_rice_bulgogi.OpenClanker.html",   parse_generic_html),
    ("generic_html_meatballs","high_protein_sweet_sour_meatballs.html",           parse_generic_html),
]


def main():
    FIXTURES.mkdir(exist_ok=True)
    for name, filename, parser_fn in CASES:
        path = RECIPES / filename
        content = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "lxml")
        data = normalize(parser_fn(content, soup))
        data.pop("image_url", None)
        out = FIXTURES / f"{name}.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        n_ingrs = sum(len(g["ingredients"]) for g in data.get("ingredient_groups", []))
        n_steps = sum(len(g["steps"]) for g in data.get("instruction_groups", []))
        print(f"  {name}: ingrs={n_ingrs}, steps={n_steps}, title={data.get('title', '')[:45]}")
    print(f"\nWrote {len(CASES)} fixtures to {FIXTURES}")


if __name__ == "__main__":
    main()
