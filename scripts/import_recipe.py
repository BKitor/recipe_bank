#!/usr/bin/env python3
# pyright: basic
"""import_recipe.py — Import a recipe file (HTML or PDF) into src/recipes/<slug>.json"""

import datetime
import json
import os
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependency: pip install beautifulsoup4 lxml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def get_text(el, sep=" "):
    return el.get_text(separator=sep, strip=True) if el else ""


def safe_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def extract_saved_url(content):
    """Pull the original page URL out of the browser-saved HTML comment."""
    m = re.search(r'<!-- saved from url=\(\d+\)(https?://[^\s<"]+)', content[:600])
    saved = m.group(1) if m else None
    # Prefer wprm_print_url which is the actual recipe page (not the /wprm_print/ URL)
    m2 = re.search(r'wprm_print_url\s*=\s*"([^"]+)"', content)
    if m2:
        return m2.group(1).replace("\\/", "/")
    return saved


def parse_time_str(text):
    """Convert strings like '25 minutes', '1 hr 30 min', '1:30' to total minutes."""
    if not text:
        return None
    text = text.lower().strip()
    total = 0
    for h_match in re.finditer(r"(\d+)\s*h", text):
        total += int(h_match.group(1)) * 60
    for m_match in re.finditer(r"(\d+)\s*m", text):
        total += int(m_match.group(1))
    # Handle "1:30" format
    colon = re.match(r"^(\d+):(\d+)$", text)
    if colon and total == 0:
        total = int(colon.group(1)) * 60 + int(colon.group(2))
    return total if total > 0 else None


def parse_iso_duration(iso):
    """Convert ISO 8601 duration like PT1H30M or PT45M to minutes."""
    if not iso:
        return None
    h = re.search(r"(\d+)H", iso)
    m = re.search(r"(\d+)M", iso)
    total = (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)
    return total if total > 0 else None


def unique_list(lst):
    seen = set()
    out = []
    for x in lst:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ---------------------------------------------------------------------------
# Strategy detection
# ---------------------------------------------------------------------------

def detect_strategy(content, soup):
    if re.search(r"wprmpuc_recipe_\d+", content):
        return "wprm_js"
    if soup.select_one(".wprm-recipe-ingredient"):
        return "wprm_html"
    if soup.select_one(".structured-ingredients__list-item"):
        return "serious_eats"
    if soup.select(".tasty-recipes-ingredients li"):
        return "tasty"
    for script in soup.find_all("script", type="application/ld+json"):
        data = safe_json(script.get_text())
        if not data:
            continue
        if isinstance(data, dict) and data.get("@type") == "Recipe":
            return "json_ld"
        for item in (data.get("@graph", []) if isinstance(data, dict) else []):
            if item.get("@type") == "Recipe":
                return "json_ld"
    return "claude_api"


# ---------------------------------------------------------------------------
# WPRM helpers (shared by wprm_js and wprm_html)
# ---------------------------------------------------------------------------

def extract_wprm_time(soup, field):
    h_el = soup.select_one(f".wprm-recipe-{field}_time-hours")
    m_el = soup.select_one(f".wprm-recipe-{field}_time-minutes")
    hours = int(h_el.get_text().strip().split()[0]) if h_el and h_el.get_text().strip() else 0
    mins  = int(m_el.get_text().strip().split()[0]) if m_el and m_el.get_text().strip() else 0
    return hours * 60 + mins if (hours or mins) else None


def extract_wprm_tags(soup):
    tags = []
    for sel in [".wprm-recipe-course-container", ".wprm-recipe-cuisine-container",
                ".wprm-recipe-keyword-container", ".wprm-recipe-diet-container"]:
        el = soup.select_one(sel)
        if el:
            # The actual value spans sit inside; get comma-separated text
            text = el.get_text(separator=",", strip=True)
            # Strip label prefix like "Course: " by splitting on the value spans
            # Simpler: just take text after the first colon if present
            if ":" in text:
                text = text.split(":", 1)[1]
            tags.extend([t.strip() for t in text.split(",") if t.strip()])
    return unique_list(tags)


def extract_wprm_image(soup):
    img = soup.select_one(".wprm-recipe-image img")
    if not img:
        return None
    srcset = img.get("srcset", "")
    if srcset:
        abs_urls = [parts[0] for u in srcset.split(",") if (parts := u.strip().split()) and parts[0].startswith("http")]
        if abs_urls:
            return abs_urls[-1]
    src = img.get("src", "")
    return src if src.startswith("http") else None


def extract_wprm_instruction_groups(soup):
    groups = []
    group_els = soup.select(".wprm-recipe-instruction-group")
    if not group_els:
        # No groups — flat list
        steps = [get_text(el) for el in soup.select(".wprm-recipe-instruction-text") if get_text(el)]
        if steps:
            groups.append({"name": "", "steps": steps})
        return groups
    for g in group_els:
        name_el = g.select_one(".wprm-recipe-instruction-group-name")
        name = get_text(name_el) if name_el else ""
        steps = [get_text(el) for el in g.select(".wprm-recipe-instruction-text") if get_text(el)]
        groups.append({"name": name, "steps": steps})
    return groups


def extract_wprm_notes(soup):
    el = soup.select_one(".wprm-recipe-notes-container")
    if not el:
        el = soup.select_one(".wprm-recipe-notes")
    return get_text(el, "\n") if el else None


# ---------------------------------------------------------------------------
# Strategy 1: wprm_js
# ---------------------------------------------------------------------------

def parse_wprm_js(content, soup):
    # Ingredients from commented-out JS var (raw regex on full content string)
    m = re.search(r"var wprmpuc_recipe_\d+\s*=\s*(\{.*?\});\s*(?:<!--|//)", content, re.DOTALL)
    if not m:
        # Some pages don't have the closing comment pattern, try without
        m = re.search(r"var wprmpuc_recipe_\d+\s*=\s*(\{[^;]+\});", content, re.DOTALL)

    raw_js = safe_json(m.group(1)) if m else {}
    raw_ingrs = raw_js.get("ingredients", []) if raw_js else []
    # Build uid → raw ingredient map
    uid_map = {i.get("uid"): i for i in raw_ingrs if isinstance(i, dict)}

    # Ingredient groups from HTML
    ingredient_groups = []
    group_els = soup.select(".wprm-recipe-ingredient-group")
    if not group_els:
        # No groups — flat list
        ingrs = []
        for el in soup.select(".wprm-recipe-ingredient"):
            uid = el.get("data-uid")
            uid = int(uid) if uid and uid.isdigit() else -1
            raw = uid_map.get(uid, {})
            ingrs.append({
                "amount": str(raw.get("amount", get_text(el.select_one(".wprm-recipe-ingredient-amount")))).strip(),
                "unit":   str(raw.get("unit",   get_text(el.select_one(".wprm-recipe-ingredient-unit")))).strip(),
                "name":   get_text(el.select_one(".wprm-recipe-ingredient-name")),
                "notes":  str(raw.get("notes",  get_text(el.select_one(".wprm-recipe-ingredient-notes")))).strip(),
            })
        ingredient_groups = [{"name": "", "ingredients": ingrs}]
    else:
        for g in group_els:
            name_el = g.select_one(".wprm-recipe-ingredient-group-name")
            name = get_text(name_el) if name_el else ""
            ingrs = []
            for el in g.select(".wprm-recipe-ingredient"):
                uid = el.get("data-uid")
                uid = int(uid) if uid and uid.isdigit() else -1
                raw = uid_map.get(uid, {})
                ingrs.append({
                    "amount": str(raw.get("amount", get_text(el.select_one(".wprm-recipe-ingredient-amount")))).strip(),
                    "unit":   str(raw.get("unit",   get_text(el.select_one(".wprm-recipe-ingredient-unit")))).strip(),
                    "name":   get_text(el.select_one(".wprm-recipe-ingredient-name")),
                    "notes":  str(raw.get("notes",  get_text(el.select_one(".wprm-recipe-ingredient-notes")))).strip(),
                })
            ingredient_groups.append({"name": name, "ingredients": ingrs})

    return {
        "title":               get_text(soup.select_one(".wprm-recipe-name")),
        "source_url":          extract_saved_url(content),
        "description":         get_text(soup.select_one(".wprm-recipe-summary")),
        "prep_time_min":       extract_wprm_time(soup, "prep"),
        "cook_time_min":       extract_wprm_time(soup, "cook"),
        "total_time_min":      extract_wprm_time(soup, "total"),
        "servings":            get_text(soup.select_one(".wprm-recipe-servings")),
        "tags":                extract_wprm_tags(soup),
        "ingredient_groups":   ingredient_groups,
        "instruction_groups":  extract_wprm_instruction_groups(soup),
        "notes":               extract_wprm_notes(soup),
        "image_url":           extract_wprm_image(soup),
    }


# ---------------------------------------------------------------------------
# Strategy 2: wprm_html (no JS var)
# ---------------------------------------------------------------------------

def parse_wprm_html(content, soup):
    def ingr_from_el(el):
        return {
            "amount": get_text(el.select_one(".wprm-recipe-ingredient-amount")),
            "unit":   get_text(el.select_one(".wprm-recipe-ingredient-unit")),
            "name":   get_text(el.select_one(".wprm-recipe-ingredient-name")),
            "notes":  get_text(el.select_one(".wprm-recipe-ingredient-notes")),
        }

    ingredient_groups = []
    group_els = soup.select(".wprm-recipe-ingredient-group")
    if not group_els:
        ingrs = [ingr_from_el(el) for el in soup.select(".wprm-recipe-ingredient")]
        ingredient_groups = [{"name": "", "ingredients": ingrs}]
    else:
        for g in group_els:
            name_el = g.select_one(".wprm-recipe-ingredient-group-name")
            ingredient_groups.append({
                "name": get_text(name_el) if name_el else "",
                "ingredients": [ingr_from_el(el) for el in g.select(".wprm-recipe-ingredient")],
            })

    return {
        "title":               get_text(soup.select_one(".wprm-recipe-name")),
        "source_url":          extract_saved_url(content),
        "description":         get_text(soup.select_one(".wprm-recipe-summary")),
        "prep_time_min":       extract_wprm_time(soup, "prep"),
        "cook_time_min":       extract_wprm_time(soup, "cook"),
        "total_time_min":      extract_wprm_time(soup, "total"),
        "servings":            get_text(soup.select_one(".wprm-recipe-servings")),
        "tags":                extract_wprm_tags(soup),
        "ingredient_groups":   ingredient_groups,
        "instruction_groups":  extract_wprm_instruction_groups(soup),
        "notes":               extract_wprm_notes(soup),
        "image_url":           extract_wprm_image(soup),
    }


# ---------------------------------------------------------------------------
# Strategy 3: serious_eats
# ---------------------------------------------------------------------------

def parse_serious_eats(content, soup):
    title = get_text(soup.select_one("h1") or soup.select_one(".recipe-title"))

    # Times and servings from meta label/data pairs
    meta = {}
    labels = soup.select(".meta-text__label")
    datas  = soup.select(".meta-text__data")
    for lbl, dat in zip(labels, datas):
        meta[lbl.get_text(strip=True).lower().rstrip(":")] = dat.get_text(strip=True)

    prep_min  = parse_time_str(meta.get("prep", meta.get("prep time", "")))
    cook_min  = parse_time_str(meta.get("cook", meta.get("cook time", "")))
    total_min = parse_time_str(meta.get("total", meta.get("total time", "")))
    yield_txt = meta.get("serves", meta.get("yield", meta.get("servings", "")))

    # Ingredients — full string per line-item (SE spans aren't consistently labeled)
    ingrs = []
    for el in soup.select(".structured-ingredients__list-item"):
        text = el.get_text(separator=" ", strip=True)
        if text:
            ingrs.append({"amount": "", "unit": "", "name": text, "notes": ""})

    # Instructions — exclude photographer credits and very short lines
    steps = []
    notes_lines = []
    in_notes = False
    for el in soup.select(".structured-project__steps li, .structured-project__steps p"):
        text = el.get_text(separator=" ", strip=True)
        if not text or len(text) < 15:
            continue
        if re.match(r"^Serious Eats\s*/\s*\w", text):
            continue
        if re.match(r"^note", text, re.IGNORECASE):
            in_notes = True
        if in_notes:
            notes_lines.append(text)
        else:
            steps.append(text)

    # Image: first absolute URL in srcset or src within .figure--constrained
    image_url = None
    for img in soup.select("img"):
        src = img.get("src", "")
        if "seriouseats.com" in src and src.startswith("http"):
            image_url = src
            break
        srcset = img.get("srcset", "")
        for part in srcset.split(","):
            parts = part.strip().split()
            if not parts:
                continue
            url = parts[0]
            if "seriouseats.com" in url and url.startswith("http"):
                image_url = url
                break
        if image_url:
            break

    return {
        "title":               title,
        "source_url":          extract_saved_url(content),
        "description":         "",
        "prep_time_min":       prep_min,
        "cook_time_min":       cook_min,
        "total_time_min":      total_min,
        "servings":            yield_txt,
        "tags":                [],
        "ingredient_groups":   [{"name": "", "ingredients": ingrs}],
        "instruction_groups":  [{"name": "", "steps": steps}],
        "notes":               "\n".join(notes_lines) if notes_lines else None,
        "image_url":           image_url,
    }


# ---------------------------------------------------------------------------
# Strategy 4: tasty
# ---------------------------------------------------------------------------

def parse_tasty(content, soup):
    title_el = (soup.select_one(".tasty-recipes-title") or
                soup.select_one("h2.tasty-recipes-title") or
                soup.select_one("h1"))

    ingrs = [{"amount": "", "unit": "", "name": li.get_text(strip=True), "notes": ""}
             for li in soup.select(".tasty-recipes-ingredients li") if li.get_text(strip=True)]

    steps = [li.get_text(separator=" ", strip=True)
             for li in soup.select(".tasty-recipes-instructions-body li") or
                        soup.select(".tasty-recipes-instructions li")
             if li.get_text(strip=True)]

    def tasty_time(sel):
        el = soup.select_one(sel)
        return parse_time_str(get_text(el)) if el else None

    return {
        "title":               get_text(title_el),
        "source_url":          extract_saved_url(content),
        "description":         get_text(soup.select_one(".tasty-recipes-description")),
        "prep_time_min":       tasty_time(".tasty-recipes-prep-time"),
        "cook_time_min":       tasty_time(".tasty-recipes-cook-time"),
        "total_time_min":      tasty_time(".tasty-recipes-total-time"),
        "servings":            get_text(soup.select_one(".tasty-recipes-yield-value") or
                                        soup.select_one(".tasty-recipes-yield")),
        "tags":                [],
        "ingredient_groups":   [{"name": "", "ingredients": ingrs}],
        "instruction_groups":  [{"name": "", "steps": steps}],
        "notes":               get_text(soup.select_one(".tasty-recipes-notes"), "\n") or None,
        "image_url":           None,
    }


# ---------------------------------------------------------------------------
# Strategy 5: json_ld
# ---------------------------------------------------------------------------

def parse_json_ld(content, soup):
    recipe = None
    for script in soup.find_all("script", type="application/ld+json"):
        data = safe_json(script.get_text())
        if not data:
            continue
        if isinstance(data, dict) and data.get("@type") == "Recipe":
            recipe = data
            break
        for item in (data.get("@graph", []) if isinstance(data, dict) else []):
            if item.get("@type") == "Recipe":
                recipe = item
                break
        if recipe:
            break

    if not recipe:
        return None

    # Instructions
    steps = []
    for step in recipe.get("recipeInstructions", []):
        if isinstance(step, str):
            steps.append(step.strip())
        elif isinstance(step, dict):
            steps.append(step.get("text", "").strip())

    # Ingredients
    ingrs = [{"amount": "", "unit": "", "name": s.strip(), "notes": ""}
             for s in recipe.get("recipeIngredient", []) if s.strip()]

    # Tags
    tags = []
    for field in ["keywords", "recipeCategory", "recipeCuisine"]:
        val = recipe.get(field, "")
        if isinstance(val, list):
            tags.extend(val)
        elif val:
            tags.extend([t.strip() for t in str(val).split(",")])
    tags = unique_list(tags)

    # Image
    img = recipe.get("image")
    if isinstance(img, str):
        image_url = img
    elif isinstance(img, dict):
        image_url = img.get("url", "")
    elif isinstance(img, list) and img:
        first = img[0]
        image_url = first if isinstance(first, str) else first.get("url", "")
    else:
        image_url = None

    # Servings
    yield_val = recipe.get("recipeYield", "")
    servings = (yield_val[0] if isinstance(yield_val, list) else str(yield_val)).strip()

    return {
        "title":               recipe.get("name", "").strip(),
        "source_url":          extract_saved_url(content),
        "description":         recipe.get("description", "").strip(),
        "prep_time_min":       parse_iso_duration(recipe.get("prepTime")),
        "cook_time_min":       parse_iso_duration(recipe.get("cookTime")),
        "total_time_min":      parse_iso_duration(recipe.get("totalTime")),
        "servings":            servings,
        "tags":                tags,
        "ingredient_groups":   [{"name": "", "ingredients": ingrs}],
        "instruction_groups":  [{"name": "", "steps": steps}],
        "notes":               "",
        "image_url":           image_url or None,
    }


# ---------------------------------------------------------------------------
# Strategy 6: claude_api
# ---------------------------------------------------------------------------

CLAUDE_SYSTEM = """\
You are a recipe data extractor. Extract recipe information and return ONLY valid JSON — no markdown, no explanation.

Schema:
{
  "title": "string",
  "description": "string or null",
  "prep_time_min": integer or null,
  "cook_time_min": integer or null,
  "total_time_min": integer or null,
  "servings": "string or null",
  "tags": ["tag1"],
  "ingredient_groups": [{"name": "string", "ingredients": [{"amount": "string", "unit": "string", "name": "string", "notes": "string"}]}],
  "instruction_groups": [{"name": "string", "steps": ["string"]}],
  "notes": "string or null"
}

Rules:
- Groups with no section name use empty string ""
- amounts are strings (fractions like "1/2" are fine)
- do not invent data not present in the source
- for multi-component recipes, use named ingredient_groups and instruction_groups for each component
"""


def parse_with_claude(text, source_url=None):
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed — run: pip install anthropic")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "This recipe format requires the Claude API to parse.\n"
            "  Set your API key and retry:\n\n"
            "    export ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=CLAUDE_SYSTEM,
        messages=[{"role": "user", "content": text[:40000]}],
    )
    data = safe_json(response.content[0].text)
    if not data:
        raise ValueError(f"Claude returned non-JSON: {response.content[0].text[:200]}")
    data["source_url"] = source_url
    return data


def extract_text_from_pdf(filepath):
    try:
        import pypdf
    except ImportError:
        print("  ERROR: pypdf not installed. Run: pip install pypdf")
        sys.exit(1)
    reader = pypdf.PdfReader(str(filepath))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def html_to_text(content):
    soup = BeautifulSoup(content, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


# ---------------------------------------------------------------------------
# Image download
# ---------------------------------------------------------------------------

def download_image(url, slug, images_dir):
    """Download url into images_dir/{slug}.{ext}. Returns the path on success, None on failure."""
    try:
        ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        dest = images_dir / f"{slug}.{ext}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            images_dir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
        return dest
    except Exception as e:
        print(f"  Image download failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Normalize + write
# ---------------------------------------------------------------------------

def normalize(data):
    """Ensure all required fields exist and clean up empty/None values."""
    data.setdefault("description", None)
    data.setdefault("prep_time_min", None)
    data.setdefault("cook_time_min", None)
    data.setdefault("total_time_min", None)
    data.setdefault("servings", None)
    data.setdefault("tags", [])
    data.setdefault("notes", None)
    data.setdefault("source_url", None)

    # Remove empty strings → None for scalar fields
    for field in ["description", "servings", "notes", "source_url"]:
        if data.get(field) == "":
            data[field] = None

    # Ensure ingredient/instruction group structure
    for group in data.get("ingredient_groups", []):
        group.setdefault("name", "")
        for ing in group.get("ingredients", []):
            for f in ["amount", "unit", "name", "notes"]:
                ing.setdefault(f, "")
                if ing[f] is None:
                    ing[f] = ""
                ing[f] = str(ing[f]).strip()

    for group in data.get("instruction_groups", []):
        group.setdefault("name", "")
        group["steps"] = [s.strip() for s in group.get("steps", []) if s and s.strip()]

    data["tags"] = [t for t in data.get("tags", []) if t]
    return data


def unique_output_path(base_dir, slug):
    path = base_dir / f"{slug}.json"
    if not path.exists():
        return path, slug
    for i in range(2, 100):
        candidate_slug = f"{slug}-{i}"
        candidate = base_dir / f"{candidate_slug}.json"
        if not candidate.exists():
            return candidate, candidate_slug
    raise RuntimeError(f"Too many slug collisions for {slug}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def import_file(filepath, out_dir=None, dry_run=False):
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"  ERROR: file not found: {filepath}")
        return None

    if out_dir is None:
        out_dir = Path(__file__).parent.parent / "src" / "recipes"
    images_dir = out_dir.parent / "assets" / "images"

    suffix = filepath.suffix.lower()
    print(f"Importing: {filepath.name}")

    if suffix == ".pdf":
        print("  Strategy: claude_api (PDF)")
        text = extract_text_from_pdf(filepath)
        data = parse_with_claude(text, source_url=None)
    elif suffix in (".html", ".htm"):
        content = filepath.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "lxml")
        strategy = detect_strategy(content, soup)
        print(f"  Strategy: {strategy}")

        if strategy == "wprm_js":
            data = parse_wprm_js(content, soup)
        elif strategy == "wprm_html":
            data = parse_wprm_html(content, soup)
        elif strategy == "serious_eats":
            data = parse_serious_eats(content, soup)
        elif strategy == "tasty":
            data = parse_tasty(content, soup)
        elif strategy == "json_ld":
            data = parse_json_ld(content, soup)
            if data is None:
                print("  json_ld parse failed, falling back to claude_api")
                text = html_to_text(content)
                data = parse_with_claude(text, extract_saved_url(content))
        else:
            print("  Strategy: claude_api (unrecognized HTML)")
            text = html_to_text(content)
            data = parse_with_claude(text, extract_saved_url(content))
    else:
        print(f"  ERROR: unsupported file type: {suffix}")
        return None

    if not data:
        print("  ERROR: parse returned no data")
        return None

    data = normalize(data)

    title = data.get("title", "")
    if not title:
        print("  WARNING: no title extracted, using filename")
        title = filepath.stem
        data["title"] = title

    slug = slugify(title)
    data["id"] = slug
    data["date_added"] = datetime.date.today().isoformat()

    # Download image now that we have the slug; never store the URL in the JSON.
    image_url = data.pop("image_url", None)
    if dry_run:
        print(f"  [dry-run] Would write: src/recipes/{slug}.json")
        print(f"  Title: {data['title']}")
        print(f"  Tags: {data['tags']}")
        if image_url:
            print(f"  Image URL: {image_url} (would download)")
        return data

    if image_url:
        result = download_image(image_url, slug, images_dir)
        print(f"  Image: {result.name if result else 'download failed, skipped'}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path, final_slug = unique_output_path(out_dir, slug)
    if final_slug != slug:
        print(f"  WARNING: slug collision, using {final_slug}")
        data["id"] = final_slug

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Written: {out_path}")
    return data


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    files = [a for a in args if not a.startswith("--")]

    if not files:
        print("Usage: python scripts/import_recipe.py [--dry-run] <file.html|file.pdf> ...")
        sys.exit(1)

    for f in files:
        import_file(f, dry_run=dry_run)


if __name__ == "__main__":
    main()
