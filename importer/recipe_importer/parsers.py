"""Recipe parsers for each detected HTML format."""

import re

from .utils import (
    extract_saved_url, get_text, parse_iso_duration, parse_time_str, safe_json, unique_list,
)

# ---------------------------------------------------------------------------
# Strategy detection
# ---------------------------------------------------------------------------

_INGR_RE = re.compile(r"\bingredient", re.IGNORECASE)
_INST_RE = re.compile(r"\b(instruction|direction|method|step)", re.IGNORECASE)


def detect_strategy(content, soup):
    if re.search(r"wprmpuc_recipe_\d+", content):
        return "wprm_js"
    if soup.select_one(".wprm-recipe-ingredient"):
        return "wprm_html"
    if soup.select_one(".jetpack-recipe"):
        return "jetpack"
    if soup.select_one(".structured-ingredients__list-item"):
        return "serious_eats"
    if soup.select(".tasty-recipes-ingredients li"):
        return "tasty"
    saved_url = extract_saved_url(content)
    if saved_url and "based.cooking" in saved_url:
        return "based_cooking"
    for script in soup.find_all("script", type="application/ld+json"):
        data = safe_json(script.get_text())
        if not data:
            continue
        if isinstance(data, dict) and data.get("@type") == "Recipe":
            return "json_ld"
        items = (
            data.get("@graph", []) if isinstance(data, dict)
            else (data if isinstance(data, list) else [])
        )
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Recipe":
                return "json_ld"
    return "generic_html"


# ---------------------------------------------------------------------------
# WPRM helpers
# ---------------------------------------------------------------------------

def _wprm_time(soup, field):
    h_el = soup.select_one(f".wprm-recipe-{field}_time-hours")
    m_el = soup.select_one(f".wprm-recipe-{field}_time-minutes")
    hours = int(h_el.get_text().strip().split()[0]) if h_el and h_el.get_text().strip() else 0
    mins = int(m_el.get_text().strip().split()[0]) if m_el and m_el.get_text().strip() else 0
    return hours * 60 + mins if (hours or mins) else None


def _wprm_tags(soup):
    tags = []
    for sel in [
        ".wprm-recipe-course-container",
        ".wprm-recipe-cuisine-container",
        ".wprm-recipe-keyword-container",
        ".wprm-recipe-diet-container",
    ]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator=",", strip=True)
            if ":" in text:
                text = text.split(":", 1)[1]
            tags.extend([t.strip() for t in text.split(",") if t.strip()])
    return unique_list(tags)


def _wprm_image(soup):
    img = soup.select_one(".wprm-recipe-image img")
    if not img:
        return None
    srcset = img.get("srcset", "")
    if srcset:
        abs_urls = [
            parts[0]
            for u in srcset.split(",")
            if (parts := u.strip().split()) and parts[0].startswith("http")
        ]
        if abs_urls:
            return abs_urls[-1]
    src = img.get("src", "")
    return src if src.startswith("http") else None


def _wprm_instruction_groups(soup):
    groups = []
    group_els = soup.select(".wprm-recipe-instruction-group")
    if not group_els:
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


def _wprm_notes(soup):
    el = soup.select_one(".wprm-recipe-notes-container") or soup.select_one(".wprm-recipe-notes")
    return get_text(el, "\n") if el else None


# ---------------------------------------------------------------------------
# Strategy 1: wprm_js
# ---------------------------------------------------------------------------

def parse_wprm_js(content, soup):
    m = re.search(r"var wprmpuc_recipe_\d+\s*=\s*(\{.*?\});\s*(?:<!--|//)", content, re.DOTALL)
    if not m:
        m = re.search(r"var wprmpuc_recipe_\d+\s*=\s*(\{[^;]+\});", content, re.DOTALL)

    raw_js = safe_json(m.group(1)) if m else {}
    raw_ingrs = raw_js.get("ingredients", []) if raw_js else []
    uid_map = {i.get("uid"): i for i in raw_ingrs if isinstance(i, dict)}

    def ingr_from_el(el):
        uid = el.get("data-uid")
        uid = int(uid) if uid and uid.isdigit() else -1
        raw = uid_map.get(uid, {})
        return {
            "amount": str(raw.get("amount", get_text(el.select_one(".wprm-recipe-ingredient-amount")))).strip(),
            "unit":   str(raw.get("unit",   get_text(el.select_one(".wprm-recipe-ingredient-unit")))).strip(),
            "name":   get_text(el.select_one(".wprm-recipe-ingredient-name")),
            "notes":  str(raw.get("notes",  get_text(el.select_one(".wprm-recipe-ingredient-notes")))).strip(),
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
        "title":              get_text(soup.select_one(".wprm-recipe-name")),
        "source_url":         extract_saved_url(content),
        "description":        get_text(soup.select_one(".wprm-recipe-summary")),
        "prep_time_min":      _wprm_time(soup, "prep"),
        "cook_time_min":      _wprm_time(soup, "cook"),
        "total_time_min":     _wprm_time(soup, "total"),
        "servings":           get_text(soup.select_one(".wprm-recipe-servings")),
        "tags":               _wprm_tags(soup),
        "ingredient_groups":  ingredient_groups,
        "instruction_groups": _wprm_instruction_groups(soup),
        "notes":              _wprm_notes(soup),
        "image_url":          _wprm_image(soup),
    }


# ---------------------------------------------------------------------------
# Strategy 2: wprm_html
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
        "title":              get_text(soup.select_one(".wprm-recipe-name")),
        "source_url":         extract_saved_url(content),
        "description":        get_text(soup.select_one(".wprm-recipe-summary")),
        "prep_time_min":      _wprm_time(soup, "prep"),
        "cook_time_min":      _wprm_time(soup, "cook"),
        "total_time_min":     _wprm_time(soup, "total"),
        "servings":           get_text(soup.select_one(".wprm-recipe-servings")),
        "tags":               _wprm_tags(soup),
        "ingredient_groups":  ingredient_groups,
        "instruction_groups": _wprm_instruction_groups(soup),
        "notes":              _wprm_notes(soup),
        "image_url":          _wprm_image(soup),
    }


# ---------------------------------------------------------------------------
# Strategy 3: serious_eats
# ---------------------------------------------------------------------------

def parse_serious_eats(content, soup):
    title = get_text(soup.select_one("h1") or soup.select_one(".recipe-title"))

    meta = {}
    labels = soup.select(".meta-text__label")
    datas = soup.select(".meta-text__data")
    for lbl, dat in zip(labels, datas):
        meta[lbl.get_text(strip=True).lower().rstrip(":")] = dat.get_text(strip=True)

    ingrs = []
    for el in soup.select(".structured-ingredients__list-item"):
        text = el.get_text(separator=" ", strip=True)
        if text:
            ingrs.append({"amount": "", "unit": "", "name": text, "notes": ""})

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
        "title":              title,
        "source_url":         extract_saved_url(content),
        "description":        "",
        "prep_time_min":      parse_time_str(meta.get("prep", meta.get("prep time", ""))),
        "cook_time_min":      parse_time_str(meta.get("cook", meta.get("cook time", ""))),
        "total_time_min":     parse_time_str(meta.get("total", meta.get("total time", ""))),
        "servings":           meta.get("serves", meta.get("yield", meta.get("servings", ""))),
        "tags":               [],
        "ingredient_groups":  [{"name": "", "ingredients": ingrs}],
        "instruction_groups": [{"name": "", "steps": steps}],
        "notes":              "\n".join(notes_lines) if notes_lines else None,
        "image_url":          image_url,
    }


# ---------------------------------------------------------------------------
# Strategy 4: tasty
# ---------------------------------------------------------------------------

def parse_tasty(content, soup):
    title_el = (
        soup.select_one(".tasty-recipes-title")
        or soup.select_one("h2.tasty-recipes-title")
        or soup.select_one("h1")
    )

    ingrs = [
        {"amount": "", "unit": "", "name": li.get_text(strip=True), "notes": ""}
        for li in soup.select(".tasty-recipes-ingredients li")
        if li.get_text(strip=True)
    ]

    steps = [
        li.get_text(separator=" ", strip=True)
        for li in (
            soup.select(".tasty-recipes-instructions-body li")
            or soup.select(".tasty-recipes-instructions li")
        )
        if li.get_text(strip=True)
    ]

    def tasty_time(sel):
        el = soup.select_one(sel)
        return parse_time_str(get_text(el)) if el else None

    return {
        "title":              get_text(title_el),
        "source_url":         extract_saved_url(content),
        "description":        get_text(soup.select_one(".tasty-recipes-description")),
        "prep_time_min":      tasty_time(".tasty-recipes-prep-time"),
        "cook_time_min":      tasty_time(".tasty-recipes-cook-time"),
        "total_time_min":     tasty_time(".tasty-recipes-total-time"),
        "servings":           get_text(
            soup.select_one(".tasty-recipes-yield-value")
            or soup.select_one(".tasty-recipes-yield")
        ),
        "tags":               [],
        "ingredient_groups":  [{"name": "", "ingredients": ingrs}],
        "instruction_groups": [{"name": "", "steps": steps}],
        "notes":              get_text(soup.select_one(".tasty-recipes-notes"), "\n") or None,
        "image_url":          None,
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
        items = (
            data.get("@graph", []) if isinstance(data, dict)
            else (data if isinstance(data, list) else [])
        )
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Recipe":
                recipe = item
                break
        if recipe:
            break

    if not recipe:
        return None

    steps = []
    for step in recipe.get("recipeInstructions", []):
        if isinstance(step, str):
            steps.append(step.strip())
        elif isinstance(step, dict):
            steps.append(step.get("text", "").strip())

    ingrs = [
        {"amount": "", "unit": "", "name": s.strip(), "notes": ""}
        for s in recipe.get("recipeIngredient", [])
        if s.strip()
    ]

    tags = []
    for field in ["keywords", "recipeCategory", "recipeCuisine"]:
        val = recipe.get(field, "")
        if isinstance(val, list):
            tags.extend(val)
        elif val:
            tags.extend([t.strip() for t in str(val).split(",")])
    # Filter out metadata-style "key: value" entries sometimes embedded in JSON-LD keywords
    tags = unique_list([t for t in tags if t and ": " not in t and len(t) <= 50])

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

    yield_val = recipe.get("recipeYield", "")
    servings = (yield_val[0] if isinstance(yield_val, list) else str(yield_val)).strip()

    return {
        "title":              recipe.get("name", "").strip(),
        "source_url":         extract_saved_url(content),
        "description":        recipe.get("description", "").strip(),
        "prep_time_min":      parse_iso_duration(recipe.get("prepTime")),
        "cook_time_min":      parse_iso_duration(recipe.get("cookTime")),
        "total_time_min":     parse_iso_duration(recipe.get("totalTime")),
        "servings":           servings,
        "tags":               tags,
        "ingredient_groups":  [{"name": "", "ingredients": ingrs}],
        "instruction_groups": [{"name": "", "steps": steps}],
        "notes":              "",
        "image_url":          image_url or None,
    }


# ---------------------------------------------------------------------------
# Strategy 6: jetpack
# ---------------------------------------------------------------------------

def parse_jetpack(content, soup):
    title = get_text(soup.select_one(".jetpack-recipe-title"))

    # Ingredient groups: h5 elements inside the ingredients ul act as group headers
    ingr_container = soup.select_one(".jetpack-recipe-ingredients")
    ingredient_groups = []
    if ingr_container:
        cur_group = {"name": "", "ingredients": []}
        for child in ingr_container.find_all(["h5", "li"]):
            if child.name == "h5":
                if cur_group["ingredients"]:
                    ingredient_groups.append(cur_group)
                cur_group = {"name": get_text(child), "ingredients": []}
            elif "jetpack-recipe-ingredient" in child.get("class", []):
                text = get_text(child)
                if text:
                    cur_group["ingredients"].append(
                        {"amount": "", "unit": "", "name": text, "notes": ""}
                    )
        if cur_group["ingredients"]:
            ingredient_groups.append(cur_group)

    # Instructions: paragraphs inside .jetpack-recipe-directions
    dir_container = soup.select_one(".jetpack-recipe-directions")
    steps = []
    if dir_container:
        for p in dir_container.find_all("p"):
            text = get_text(p)
            if text:
                steps.append(text)
        if not steps:
            for li in dir_container.find_all("li"):
                text = get_text(li)
                if text:
                    steps.append(text)

    # Intro note (first p in .jetpack-recipe-content, before the ingredient/direction divs)
    notes = None
    content_div = soup.select_one(".jetpack-recipe-content")
    if content_div:
        first_p = content_div.find("p")
        if first_p:
            notes = get_text(first_p) or None

    def jetpack_time(sel):
        el = soup.select_one(sel)
        return parse_time_str(get_text(el)) if el else None

    return {
        "title":              title,
        "source_url":         extract_saved_url(content),
        "description":        None,
        "prep_time_min":      jetpack_time(".jetpack-recipe-prep-time"),
        "cook_time_min":      jetpack_time(".jetpack-recipe-cook-time"),
        "total_time_min":     jetpack_time(".jetpack-recipe-total-time"),
        "servings":           get_text(soup.select_one(".jetpack-recipe-yield")),
        "tags":               [],
        "ingredient_groups":  ingredient_groups or [{"name": "", "ingredients": []}],
        "instruction_groups": [{"name": "", "steps": steps}],
        "notes":              notes,
        "image_url":          None,
    }


# ---------------------------------------------------------------------------
# Strategy 7: based_cooking
# ---------------------------------------------------------------------------

def parse_based_cooking(content, soup):
    title = get_text(soup.select_one("h1"))
    source_url = extract_saved_url(content)

    # Description: first plain paragraph (not the time/emoji list)
    description = None
    article = soup.select_one("article") or soup.find("main")
    if article:
        for el in article.find_all(["p", "ul", "h2"], limit=10):
            if el.name in ("h2",):
                break
            if el.name == "p":
                text = get_text(el)
                if text and not re.search(r"[⏲🍳🍽]", text):
                    description = text
                    break

    # Times from emoji bullet list (⏲️ Prep time: 20 min, 🍳 Cook time: 35 min, 🍽️ Servings: 12)
    prep_min = cook_min = total_min = None
    servings = None
    body_text = soup.get_text(" ", strip=True)
    for line in re.split(r"[⏲🍳🍽]", body_text):
        line = line.strip()
        if re.search(r"prep\s*time", line, re.IGNORECASE):
            prep_min = prep_min or parse_time_str(line)
        elif re.search(r"cook\s*time", line, re.IGNORECASE):
            cook_min = cook_min or parse_time_str(line)
        elif re.search(r"total\s*time", line, re.IGNORECASE):
            total_min = total_min or parse_time_str(line)
        elif re.search(r"servings?", line, re.IGNORECASE):
            m = re.search(r"(\d+)", line)
            if m and not servings:
                servings = m.group(1)

    # Ingredient groups: all h2 sections that are NOT directions/instructions
    ingredient_groups = []
    steps = []
    for h2 in soup.select("h2"):
        heading = h2.get_text(strip=True)
        # Find the immediately following list sibling
        ul = h2.find_next_sibling("ul")
        ol = h2.find_next_sibling("ol")
        next_h2 = h2.find_next_sibling("h2")

        if re.search(r"\b(direction|instruction)", heading, re.IGNORECASE):
            if ol:
                steps = [get_text(li) for li in ol.select("li") if get_text(li)]
            elif ul:
                steps = [get_text(li) for li in ul.select("li") if get_text(li)]
        elif ul:
            # Stop before the next h2 boundary
            ingrs = []
            for li in ul.select("li"):
                text = get_text(li)
                if text:
                    ingrs.append({"amount": "", "unit": "", "name": text, "notes": ""})
            if ingrs:
                group_name = "" if re.search(r"\bingredient", heading, re.IGNORECASE) else heading
                ingredient_groups.append({"name": group_name, "ingredients": ingrs})

    # Tags from .taglist links
    tags = [get_text(a) for a in soup.select(".taglist a") if get_text(a)]

    return {
        "title":              title,
        "source_url":         source_url,
        "description":        description,
        "prep_time_min":      prep_min,
        "cook_time_min":      cook_min,
        "total_time_min":     total_min,
        "servings":           servings,
        "tags":               tags,
        "ingredient_groups":  ingredient_groups or [{"name": "", "ingredients": []}],
        "instruction_groups": [{"name": "", "steps": steps}],
        "notes":              None,
        "image_url":          None,
    }


# ---------------------------------------------------------------------------
# Strategy 8: generic_html  (replaces claude_api fallback)
# ---------------------------------------------------------------------------

def _generic_times_and_servings(body_text):
    """Extract prep/cook/total times and servings from free-form body text."""
    prep_min = cook_min = total_min = None
    servings = None

    for m in re.finditer(r"(?i)prep\s*(?:time)?\s*:?\s*([^\n:,]{2,30})", body_text):
        if not prep_min:
            prep_min = parse_time_str(m.group(1))
    for m in re.finditer(r"(?i)cook\s*(?:time)?\s*:?\s*([^\n:,]{2,30})", body_text):
        if not cook_min:
            cook_min = parse_time_str(m.group(1))
    for m in re.finditer(r"(?i)total\s*(?:time)?\s*:?\s*([^\n:,]{2,30})", body_text):
        if not total_min:
            total_min = parse_time_str(m.group(1))
    for m in re.finditer(r"(?i)(?:yield|serving[s]?)\s*:?\s*([^\n:]{2,30}?)(?=\s+[A-Z]\w+:|\n|$)", body_text):
        if not servings:
            servings = m.group(1).strip().rstrip(".,;")

    return prep_min, cook_min, total_min, servings


def parse_generic_html(content, soup):
    title = get_text(soup.select_one("h1"))
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
    source_url = extract_saved_url(content)

    body_text = soup.get_text(" ", strip=True)
    prep_min, cook_min, total_min, servings = _generic_times_and_servings(body_text)

    ingredient_groups = []
    instruction_groups = []
    notes = None

    body = soup.find("body") or soup

    # Detect if this is an OpenClanker multi-component format:
    # Each div.section has an h2 that is NOT an ingredient/instruction heading.
    top_h2_texts = [h2.get_text(strip=True) for h2 in soup.select("h2")]
    has_ingr_h2 = any(_INGR_RE.search(t) for t in top_h2_texts)
    has_inst_h2 = any(_INST_RE.search(t) for t in top_h2_texts)
    component_sections = soup.select("div.section")
    is_multicomponent = (
        bool(component_sections)
        and not has_ingr_h2
        and not has_inst_h2
        and all(s.select_one("h2") for s in component_sections)
    )

    if is_multicomponent:
        # Each div.section = one dish component with h3 Ingredients + h3 Method sub-sections
        for section in component_sections:
            h2 = section.select_one("h2")
            if not h2:
                continue
            component = get_text(h2)
            mode = None
            cur_ingrs = []
            cur_steps = []

            for el in section.find_all(["h3", "ul", "ol", "p"]):
                if el.name == "h3":
                    text = el.get_text(strip=True)
                    if _INGR_RE.search(text):
                        mode = "ingredients"
                    elif _INST_RE.search(text):
                        mode = "instructions"
                    else:
                        mode = None
                elif el.name in ("ul", "ol"):
                    lis = [get_text(li) for li in el.select("li") if get_text(li)]
                    if mode == "ingredients":
                        cur_ingrs.extend(lis)
                    elif mode == "instructions":
                        cur_steps.extend(lis)
                elif el.name == "p" and mode == "instructions":
                    text = get_text(el)
                    if text:
                        cur_steps.append(text)

            if cur_ingrs:
                ingredient_groups.append({
                    "name": component,
                    "ingredients": [
                        {"amount": "", "unit": "", "name": t, "notes": ""} for t in cur_ingrs
                    ],
                })
            if cur_steps:
                instruction_groups.append({"name": component, "steps": cur_steps})

    else:
        # Flat or hierarchical: h2 headings = Ingredients / Instructions / Notes
        # h3 headings = sub-groups within each section
        mode = None
        cur_ingr_group = None
        cur_inst_group = None
        notes_parts = []

        for el in body.find_all(["h2", "h3", "ul", "ol", "p"]):
            if el.name == "h2":
                text = el.get_text(strip=True)
                # Flush pending groups before switching
                if mode == "ingredients" and cur_ingr_group and cur_ingr_group["ingredients"]:
                    ingredient_groups.append(cur_ingr_group)
                    cur_ingr_group = None
                elif mode == "instructions" and cur_inst_group and cur_inst_group["steps"]:
                    instruction_groups.append(cur_inst_group)
                    cur_inst_group = None

                if _INGR_RE.search(text):
                    mode = "ingredients"
                    cur_ingr_group = {"name": "", "ingredients": []}
                elif _INST_RE.search(text):
                    mode = "instructions"
                    cur_inst_group = {"name": "", "steps": []}
                elif re.search(r"\bnote", text, re.IGNORECASE):
                    mode = "notes"
                else:
                    mode = None

            elif el.name == "h3":
                text = el.get_text(strip=True)
                if mode == "ingredients":
                    if cur_ingr_group and cur_ingr_group["ingredients"]:
                        ingredient_groups.append(cur_ingr_group)
                    cur_ingr_group = {"name": text, "ingredients": []}
                elif mode == "instructions":
                    if cur_inst_group and cur_inst_group["steps"]:
                        instruction_groups.append(cur_inst_group)
                    cur_inst_group = {"name": text, "steps": []}

            elif el.name in ("ul", "ol"):
                lis = [get_text(li) for li in el.select("li") if get_text(li)]
                if mode == "ingredients" and cur_ingr_group is not None:
                    cur_ingr_group["ingredients"].extend(
                        [{"amount": "", "unit": "", "name": t, "notes": ""} for t in lis]
                    )
                elif mode == "instructions" and cur_inst_group is not None:
                    cur_inst_group["steps"].extend(lis)

            elif el.name == "p":
                text = get_text(el)
                if mode == "instructions" and cur_inst_group is not None and text:
                    cur_inst_group["steps"].append(text)
                elif mode == "notes" and text:
                    notes_parts.append(text)

        # Flush final groups
        if mode == "ingredients" and cur_ingr_group and cur_ingr_group["ingredients"]:
            ingredient_groups.append(cur_ingr_group)
        elif mode == "instructions" and cur_inst_group and cur_inst_group["steps"]:
            instruction_groups.append(cur_inst_group)
        if notes_parts:
            notes = "\n".join(notes_parts)

    return {
        "title":              title,
        "source_url":         source_url,
        "description":        None,
        "prep_time_min":      prep_min,
        "cook_time_min":      cook_min,
        "total_time_min":     total_min,
        "servings":           servings,
        "tags":               [],
        "ingredient_groups":  ingredient_groups or [{"name": "", "ingredients": []}],
        "instruction_groups": instruction_groups or [{"name": "", "steps": []}],
        "notes":              notes,
        "image_url":          None,
    }
