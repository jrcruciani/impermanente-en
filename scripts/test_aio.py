"""Tests mínimos: llms.txt, alternates del sitemap y robots.txt. Ejecutar tras build_site.py."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
sys.path.insert(0, str(ROOT / "scripts"))
import build_site  # noqa: E402

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}


def check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"TEST failed: {msg}", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    essays = build_site.load_essays()

    llms = (OUT / "llms.txt").read_text(encoding="utf-8")
    check(llms.splitlines()[2].startswith("> J.R. Cruciani is a Madrid-based photographer"), "llms bio blockquote")
    for e in essays:
        check(build_site.essay_url(e) in llms, f"llms missing {e['slug']}")
        if e.get("source_url"):
            check(e["source_url"] in llms, f"llms missing source for {e['slug']}")
    for needle in ("https://fotos.impermanente.es/", "https://impermanente.es/llms.txt",
                   "https://impermanente.es/publicaciones/", "CC BY 4.0", "ai-train=no"):
        check(needle in llms, f"llms missing {needle}")

    root = ET.parse(OUT / "sitemap.xml").getroot()
    urls = {u.findtext("s:loc", namespaces=NS): u for u in root.findall("s:url", NS)}
    for e in essays:
        if not e.get("source_url"):
            continue
        for loc in (build_site.essay_url(e), e["source_url"]):
            check(loc in urls, f"sitemap missing {loc}")
            alts = {l.get("hreflang"): l.get("href") for l in urls[loc].findall("x:link", NS)}
            check(alts == {"en": build_site.essay_url(e), "es": e["source_url"]}, f"alternates for {loc}")
            check(urls[loc].findtext("s:lastmod", namespaces=NS) == (e.get("updated_at") or e["published_at"])[:10],
                  f"lastmod for {loc}")

    robots = (OUT / "robots.txt").read_text(encoding="utf-8")
    check(robots == build_site.ROBOTS_TEMPLATE.replace("<HOST>", "en.impermanente.es"), "robots template")
    check("Sitemap: https://en.impermanente.es/sitemap.xml" in robots, "robots sitemap")
    check((OUT / f"{build_site.INDEXNOW_KEY}.txt").exists(), "indexnow key file")

    home = (OUT / "index.html").read_text(encoding="utf-8")
    check('og:type" content="website"' in home, "home og:type")
    check('hreflang="x-default" href="https://impermanente.es/"' in home, "home x-default")
    for f in [OUT / "index.html", *OUT.glob("essays/*/index.html")]:
        t = f.read_text(encoding="utf-8")
        check('"@type": "Person"' not in t, f"Person redeclared in {f}")
        check("about/#person" not in t, f"stale AUTHOR_ID in {f}")
    print("AIO tests passed")


if __name__ == "__main__":
    main()
