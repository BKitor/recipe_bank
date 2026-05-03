"""Shared utilities for recipe parsing."""

import json
import re
import unicodedata


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
