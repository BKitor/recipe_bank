"""Snapshot tests for each recipe parser strategy.

Each test parses a representative HTML file and compares the output against a
stored JSON fixture.  The fixtures capture the known-good parser output; any
future change that alters the output will fail these tests so regressions are
caught before they land.

To regenerate a fixture after an intentional change:
    python scripts/tests/gen_fixtures.py
"""

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from recipe_importer.importer import normalize
from recipe_importer.parsers import (
    detect_strategy,
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


def _parse(parser_fn, filename):
    """Parse a recipe file and return a normalized dict without image_url."""
    path = RECIPES / filename
    content = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(content, "lxml")
    data = normalize(parser_fn(content, soup))
    data.pop("image_url", None)
    return data


def _fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename,expected_strategy", [
    ("Arayes.html", "wprm_js"),
    ("ChickenTikkaMasala.html", "wprm_html"),
    ("turkey meatloaf for skeptics.html", "jetpack"),
    ("risotto-serious-eats.html", "serious_eats"),
    ("Beef Stroganoff.html", "tasty"),
    ("Tajine Maadnous _ Based Cooking.html", "based_cooking"),
    ("ChickenMarsala.html", "json_ld"),
    ("Coconut-LimeChicken.html", "json_ld"),
    ("carnitas_bowl_meal_prep.OpenClanker.html", "generic_html"),
    ("CauliflowerChickenAlfredo.html", "generic_html"),
    ("korean_red_beans_rice_bulgogi.OpenClanker.html", "generic_html"),
    ("high_protein_sweet_sour_meatballs.html", "generic_html"),
])
def test_detect_strategy(filename, expected_strategy):
    path = RECIPES / filename
    content = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(content, "lxml")
    assert detect_strategy(content, soup) == expected_strategy


# ---------------------------------------------------------------------------
# Parser snapshot tests
# ---------------------------------------------------------------------------

def test_wprm_js_arayes():
    result = _parse(parse_wprm_js, "Arayes.html")
    assert result == _fixture("wprm_js")


def test_wprm_html_tikka_masala():
    result = _parse(parse_wprm_html, "ChickenTikkaMasala.html")
    assert result == _fixture("wprm_html")


def test_serious_eats_risotto():
    result = _parse(parse_serious_eats, "risotto-serious-eats.html")
    assert result == _fixture("serious_eats")


def test_tasty_stroganoff():
    result = _parse(parse_tasty, "Beef Stroganoff.html")
    assert result == _fixture("tasty")


def test_json_ld_chicken_marsala():
    result = _parse(parse_json_ld, "ChickenMarsala.html")
    assert result == _fixture("json_ld")


def test_json_ld_list_coconut_lime_chicken():
    """json_ld parser handles a list-type JSON-LD (not a dict)."""
    result = _parse(parse_json_ld, "Coconut-LimeChicken.html")
    assert result == _fixture("json_ld_list")


def test_jetpack_turkey_meatloaf():
    result = _parse(parse_jetpack, "turkey meatloaf for skeptics.html")
    assert result == _fixture("jetpack")


def test_based_cooking_tajine():
    result = _parse(parse_based_cooking, "Tajine Maadnous _ Based Cooking.html")
    assert result == _fixture("based_cooking")


def test_generic_html_multicomponent_carnitas():
    """generic_html handles multi-component recipes (OpenClanker A format)."""
    result = _parse(parse_generic_html, "carnitas_bowl_meal_prep.OpenClanker.html")
    assert result == _fixture("generic_html_multi")


def test_generic_html_flat_cauliflower():
    """generic_html handles flat single-recipe format."""
    result = _parse(parse_generic_html, "CauliflowerChickenAlfredo.html")
    assert result == _fixture("generic_html_flat")


def test_generic_html_korean_bowl():
    """generic_html handles hierarchical format with h2 sections and h3 sub-groups."""
    result = _parse(parse_generic_html, "korean_red_beans_rice_bulgogi.OpenClanker.html")
    assert result == _fixture("generic_html_korean")


def test_generic_html_meatballs():
    """generic_html handles multi-group ingredients and numbered instruction groups."""
    result = _parse(parse_generic_html, "high_protein_sweet_sour_meatballs.html")
    assert result == _fixture("generic_html_meatballs")


# ---------------------------------------------------------------------------
# Sanity checks on parsed structure
# ---------------------------------------------------------------------------

def test_all_fixtures_have_required_fields():
    required = {
        "title", "source_url", "description",
        "prep_time_min", "cook_time_min", "total_time_min",
        "servings", "tags", "ingredient_groups", "instruction_groups", "notes",
    }
    for fixture_file in FIXTURES.glob("*.json"):
        data = json.loads(fixture_file.read_text(encoding="utf-8"))
        missing = required - data.keys()
        assert not missing, f"{fixture_file.name} missing fields: {missing}"


def test_all_fixtures_have_non_empty_title():
    for fixture_file in FIXTURES.glob("*.json"):
        data = json.loads(fixture_file.read_text(encoding="utf-8"))
        assert data.get("title"), f"{fixture_file.name} has empty title"


def test_all_fixtures_have_ingredients():
    for fixture_file in FIXTURES.glob("*.json"):
        data = json.loads(fixture_file.read_text(encoding="utf-8"))
        total_ingrs = sum(len(g["ingredients"]) for g in data.get("ingredient_groups", []))
        assert total_ingrs > 0, f"{fixture_file.name} has no ingredients"


def test_all_fixtures_have_steps():
    for fixture_file in FIXTURES.glob("*.json"):
        data = json.loads(fixture_file.read_text(encoding="utf-8"))
        total_steps = sum(len(g["steps"]) for g in data.get("instruction_groups", []))
        assert total_steps > 0, f"{fixture_file.name} has no instruction steps"
