from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "essays.json"
OUTPUT_DIR = ROOT / "output"

FORBIDDEN_PHRASES = [
    "delve into",
    "tapestry",
    "nuanced landscape",
    "in today's fast-paced world",
    "it is important to note",
    "unlock the power",
    "seamlessly",
    "robust",
    "transformative journey",
]


def fail(message: str) -> None:
    print(f"QA failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    essays = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if len(essays) < 1:
        fail("expected at least 1 essay")

    slugs = set()
    for essay in essays:
        for field in ("slug", "title_en", "published_at", "summary", "body"):
            if not essay.get(field):
                fail(f"{essay.get('slug', '<unknown>')} missing {field}")
        if bool(essay.get("title_es")) != bool(essay.get("source_url")):
            fail(f"{essay['slug']} has incomplete translation metadata")
        if essay["slug"] in slugs:
            fail(f"duplicate slug {essay['slug']}")
        slugs.add(essay["slug"])
        if not re.fullmatch(r"[a-z0-9-]+", essay["slug"]):
            fail(f"bad slug {essay['slug']}")
        if len(essay["body"]) < 3:
            fail(f"{essay['slug']} has too few paragraphs")
        text = "\n".join(essay["body"]).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                fail(f"{essay['slug']} contains forbidden phrase: {phrase}")
        if " as an ai " in f" {text} ":
            fail(f"{essay['slug']} contains AI self-reference")

    feed = OUTPUT_DIR / "feed.xml"
    if not feed.exists():
        fail("feed.xml does not exist; run scripts/build_site.py first")
    root = ET.parse(feed).getroot()
    channel = root.find("channel")
    if channel is None:
        fail("feed.xml missing channel")
    language = channel.findtext("language")
    if language != "en":
        fail(f"feed language is {language!r}, expected 'en'")
    items = channel.findall("item")
    if len(items) != len(essays):
        fail(f"feed expected {len(essays)} items, found {len(items)}")
    for item in items:
        for field in ("title", "link", "guid", "pubDate", "description"):
            if not item.findtext(field):
                fail(f"feed item missing {field}")

    for slug in slugs:
        path = OUTPUT_DIR / "essays" / slug / "index.html"
        if not path.exists():
            fail(f"missing HTML for {slug}")

    print("QA passed")


if __name__ == "__main__":
    main()
