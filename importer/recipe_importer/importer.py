"""Core import logic: file detection, normalize, image download, write output."""

import datetime
import json
import sys
import urllib.request
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependency: pip install beautifulsoup4 lxml")
    sys.exit(1)

from .parsers import (
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
from .utils import extract_saved_url, slugify


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

    for field in ["description", "servings", "notes", "source_url"]:
        if data.get(field) == "":
            data[field] = None

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


def _extract_text_from_pdf(filepath):
    try:
        import pypdf
    except ImportError:
        raise ImportError("pypdf not installed — run: pip install pypdf")
    reader = pypdf.PdfReader(str(filepath))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def import_file(filepath, out_dir=None, dry_run=False):
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"  ERROR: file not found: {filepath}")
        return None

    if out_dir is None:
        out_dir = Path(__file__).parent.parent.parent / "src" / "recipes"
    out_dir = Path(out_dir)
    images_dir = out_dir.parent / "assets" / "images"

    suffix = filepath.suffix.lower()
    print(f"Importing: {filepath.name}")

    if suffix == ".pdf":
        raise NotImplementedError(
            f"PDF import is not supported. Convert {filepath.name} to HTML first."
        )
    elif suffix in (".html", ".htm"):
        content = filepath.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "lxml")
        strategy = detect_strategy(content, soup)
        print(f"  Strategy: {strategy}")

        if strategy == "wprm_js":
            data = parse_wprm_js(content, soup)
        elif strategy == "wprm_html":
            data = parse_wprm_html(content, soup)
        elif strategy == "jetpack":
            data = parse_jetpack(content, soup)
        elif strategy == "serious_eats":
            data = parse_serious_eats(content, soup)
        elif strategy == "tasty":
            data = parse_tasty(content, soup)
        elif strategy == "based_cooking":
            data = parse_based_cooking(content, soup)
        elif strategy == "json_ld":
            data = parse_json_ld(content, soup)
            if data is None:
                print("  json_ld parse failed, falling back to generic_html")
                data = parse_generic_html(content, soup)
        else:
            data = parse_generic_html(content, soup)
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

    image_url = data.pop("image_url", None)
    if dry_run:
        print(f"  [dry-run] Would write: {out_dir}/{slug}.json")
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
