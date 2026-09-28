from __future__ import annotations

import argparse
import email.utils
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "essays.json"
OUTPUT_DIR = ROOT / "output"

SITE_DOMAIN = "en.impermanente.es"
SITE_URL = f"https://{SITE_DOMAIN}"
PARENT_URL = "https://impermanente.es"
PHOTOS_URL = "https://fotos.impermanente.es"
AUTHOR_NAME = "J.R. Cruciani"
AUTHOR_ID = "https://impermanente.es/#person"
# La Persona se declara completa solo en la portada de impermanente.es; aquí solo se referencia.
AUTHOR_REF = {"@id": AUTHOR_ID, "name": AUTHOR_NAME, "url": PARENT_URL + "/"}
BIO_EN = ("J.R. Cruciani is a Madrid-based photographer and member of the Royal Photographic Society "
          "who photographs thresholds: arches, tunnels, passages and shorelines as spaces of transit.")
REL_ME = [
    "https://masto.impermanente.es/@jrcruciani",
    "https://bsky.app/profile/jrcruciani.eurosky.social",
    "https://pixelfed.social/HispaniaObscura",
    "https://commons.wikimedia.org/wiki/User:JRCruciani",
    "https://github.com/Jrcruciani",
]
INDEXNOW_KEY = "9a557e4dd0c2248c42cd8c5cee901aa3"
# El avatar se sirve desde el propio blog. Antes apuntaba a
# avatars.micro.blog, que deja de existir al cancelar la cuenta de Micro.blog.
AVATAR_URL = f"{PARENT_URL}/uploads/avatar.jpg"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


def esc(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def xml(value: str | None) -> str:
    return xml_escape(value or "", {'"': "&quot;"})


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fmt_date(value: str) -> str:
    return parse_dt(value).strftime("%-d %b %Y")


def rfc822(value: str) -> str:
    return email.utils.format_datetime(parse_dt(value))


def essay_url(essay: dict) -> str:
    return f"{SITE_URL}/essays/{essay['slug']}/"


def canonical_es(url: str | None) -> str | None:
    # Los originales en español son canónicos en blog.impermanente.es; las rutas
    # /AAAA/ del apex redirigen con 301. hreflang debe apuntar a la URL canónica.
    if url and url.startswith(PARENT_URL + "/2"):
        return "https://blog.impermanente.es" + url[len(PARENT_URL):]
    return url


def load_essays() -> list[dict]:
    essays = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for essay in essays:
        if essay.get("source_url"):
            essay["source_url"] = canonical_es(essay["source_url"])
    essays.sort(key=lambda item: item["published_at"], reverse=True)
    return essays


CSS = """
/* English edition: small textual overrides on top of the Magnum theme. */
main {
  max-width: var(--text-width, 720px);
  padding: 60px var(--gutter, 24px) 40px;
}
.edition-kicker {
  font-family: var(--sans);
  font-size: 1.1rem;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--muted);
  text-align: center;
  margin: 0 0 16px;
}
.page-intro {
  font-family: var(--serif);
  font-size: 1.75rem;
  font-weight: var(--weight-light, 300);
  line-height: 1.6;
  color: var(--text);
  text-align: center;
  margin: 0 auto 44px;
}
.essay-list {
  list-style: none;
  padding: 0;
  margin: 48px 0;
}
.essay-list li {
  border-top: 1px solid var(--separator);
  padding: 28px 0;
}
.essay-list li:last-child {
  border-bottom: 1px solid var(--separator);
}
.essay-list h2 {
  font-family: var(--serif);
  font-size: 2.6rem;
  font-weight: var(--weight-light, 300);
  line-height: 1.2;
  margin: 0 0 10px;
}
.essay-list h2 a {
  color: var(--heading);
  text-decoration: none;
  border: 0;
}
.essay-list h2 a:hover {
  color: var(--accent);
}
.essay-meta,
.source-note,
.tag-list {
  font-family: var(--sans);
  font-size: 1.1rem;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--muted);
}
.essay-summary {
  font-family: var(--serif);
  font-size: 1.55rem;
  line-height: 1.55;
  color: var(--text);
  margin: 12px 0 0;
}
article h1 {
  font-family: var(--serif);
  font-size: clamp(3rem, 7vw, 5rem);
  font-weight: var(--weight-light, 300);
  line-height: 1.08;
  text-align: center;
  margin: 18px auto 14px;
}
.article-body {
  margin-top: 44px;
}
.article-body p {
  font-family: var(--serif);
  font-size: 1.85rem;
  font-weight: var(--weight-light, 300);
  line-height: 1.62;
  color: var(--text);
  margin: 0 0 1.45em;
}
.article-nav {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin: 70px 0 0;
  padding-top: 28px;
  border-top: 1px solid var(--separator);
  font-family: var(--sans);
  font-size: 1.1rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.article-nav a,
.source-note a {
  color: var(--accent);
  text-decoration: none;
  border: 0;
}
.article-nav a:hover,
.source-note a:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
}
@media (max-width: 768px) {
  main { padding: 40px 16px 30px; }
  .article-body p { font-size: 1.65rem; }
  .essay-list h2 { font-size: 2.2rem; }
}
"""


def jsonld_website() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Blog",
        "@id": SITE_URL + "/#blog",
        "name": "Impermanente — Selected Essays in English",
        "url": SITE_URL + "/",
        "inLanguage": "en",
        "author": AUTHOR_REF,
        "publisher": {"@id": AUTHOR_ID},
        "license": LICENSE_URL,
    }


def jsonld_essay(essay: dict) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "@id": essay_url(essay) + "#post",
        "headline": essay["title_en"],
        "name": essay["title_en"],
        "description": essay["summary"],
        "url": essay_url(essay),
        "datePublished": essay["published_at"],
        "dateModified": essay.get("updated_at") or essay["published_at"],
        "inLanguage": "en",
        "author": AUTHOR_REF,
        "creator": {"@id": AUTHOR_ID},
        "publisher": {"@id": AUTHOR_ID},
        "license": LICENSE_URL,
        "keywords": essay.get("tags", []),
    }
    if essay.get("source_url") and essay.get("title_es"):
        data["isBasedOn"] = essay["source_url"]
        data["translationOfWork"] = {
            "@type": "BlogPosting",
            "@id": essay["source_url"],
            "name": essay["title_es"],
            "url": essay["source_url"],
            "inLanguage": "es",
        }
    return data


def head(title: str, description: str, canonical: str, *, jsonld: list[dict] | None = None,
         source_url: str | None = None, body_class: str = "",
         og_type: str = "article", x_default: str | None = None) -> str:
    jsonld_blocks = ""
    for block in jsonld or []:
        jsonld_blocks += f'\n<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>'
    alternate_es = f'<link rel="alternate" hreflang="es" href="{esc(source_url)}">' if source_url else ""
    if x_default:
        alternate_es += f'\n<link rel="alternate" hreflang="x-default" href="{esc(x_default)}">'
    rel_me = "\n".join(f'<link rel="me" href="{esc(u)}">' for u in REL_ME)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="{esc(AUTHOR_NAME)}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="{esc(canonical)}">
<link rel="alternate" hreflang="en" href="{esc(canonical)}">
{alternate_es}
<link rel="preload stylesheet" as="style" href="{PARENT_URL}/css/fonts.css">
<link rel="preload stylesheet" as="style" href="{PARENT_URL}/css/main.css">
<link rel="preload stylesheet" as="style" href="{PARENT_URL}/css/photos-masonry.css">
<link rel="preload stylesheet" as="style" href="{PARENT_URL}/custom.css">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="en_US">
<meta property="og:site_name" content="Impermanente — Selected Essays in English">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<link rel="alternate" type="application/rss+xml" href="{SITE_URL}/feed.xml" title="Impermanente — Selected Essays in English">
{rel_me}
<link rel="alternate" type="text/plain" href="{SITE_URL}/llms.txt" title="llms.txt">
<style>{CSS}</style>{jsonld_blocks}
</head>
<body class="{esc(body_class)}">
<header class="header">
  <nav class="site-nav">
    <h1 class="site-title"><a href="{PARENT_URL}/" class="u-url">
      <img src="{AVATAR_URL}" alt="" class="u-photo" id="avatar" width="28" height="28">impermanente
    </a></h1>
    <ul class="nav-menu">
      <li class="nav-item"><a href="{PARENT_URL}/about/">About</a></li>
      <li class="nav-item"><a href="{PHOTOS_URL}/">Photos</a></li>
      <li class="nav-item"><a href="{PARENT_URL}/viajes/">Travel</a></li>
      <li class="nav-item"><a href="{PARENT_URL}/lecturas/">Reading</a></li>
      <li class="nav-item"><a href="{PARENT_URL}/mastodon/">Shorts</a></li>
      <li class="nav-item"><a href="{PARENT_URL}/hispania-obscura/">Books</a></li>
      <li class="nav-item"><a href="{PARENT_URL}/loops/">Loops</a></li>
    </ul>
    <div class="hamburger" aria-label="Open menu" role="button" tabindex="0">
      <span class="bar"></span>
      <span class="bar"></span>
      <span class="bar"></span>
    </div>
  </nav>
</header>
<main>
"""


def footer() -> str:
    return f"""</main>
<footer>
  <p>&copy;2023&nbsp;-&nbsp;2026 J.R. Cruciani</p>
  <p>Selected essays in English. Original site: <a href="{PARENT_URL}/">impermanente.es</a>.</p>
  <p><a href="{LICENSE_URL}">CC BY 4.0</a> · Subscribe by <a href="{SITE_URL}/feed.xml">RSS</a></p>
</footer>
<script>
(function(){{
  const h = document.querySelector('.hamburger');
  const m = document.querySelector('.nav-menu');
  if (!h || !m) return;
  function toggle(){{ h.classList.toggle('active'); m.classList.toggle('active'); }}
  h.addEventListener('click', toggle);
  h.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); toggle(); }} }});
  document.querySelectorAll('.nav-menu a').forEach(a => a.addEventListener('click', () => {{
    h.classList.remove('active'); m.classList.remove('active');
  }}));
}})();
</script>
</body>
</html>
"""


def render_index(essays: list[dict]) -> str:
    title = "Impermanente — Selected Essays in English"
    desc = "Selected essays by J.R. Cruciani in English."
    body = head(title, desc, SITE_URL + "/", jsonld=[jsonld_website()],
                source_url=PARENT_URL + "/", og_type="website", x_default=PARENT_URL + "/")
    body += f"""<p class="edition-kicker">Selected essays in English</p>
<p class="page-intro">A small English edition of Impermanente: memory, tools, cities, photography, systems, and the ways machines try to think on our behalf.</p>
<ul class="essay-list">
"""
    for essay in essays:
        tags = " · ".join(essay.get("tags", []))
        body += f"""  <li>
    <p class="essay-meta">{fmt_date(essay['published_at'])}</p>
    <h2><a href="/essays/{esc(essay['slug'])}/">{esc(essay['title_en'])}</a></h2>
    <p class="essay-summary">{esc(essay['summary'])}</p>
    <p class="tag-list">{esc(tags)}</p>
  </li>
"""
    body += "</ul>\n"
    body += footer()
    return body


def render_essay(essay: dict, prev_essay: dict | None, next_essay: dict | None) -> str:
    title = f"{essay['title_en']} | Impermanente"
    source_note = ""
    if essay.get("source_url") and essay.get("title_es"):
        source_note = f'  <p class="source-note">Translated and edited from <a href="{esc(essay["source_url"])}">{esc(essay["title_es"])}</a>.</p>\n'
    body = head(title, essay["summary"], essay_url(essay), jsonld=[jsonld_essay(essay)],
                source_url=essay.get("source_url"), body_class="essay-page")
    body += f"""<article>
  <p class="edition-kicker">{fmt_date(essay['published_at'])}</p>
  <h1>{esc(essay['title_en'])}</h1>
{source_note}  <div class="article-body">
"""
    for paragraph in essay["body"]:
        body += f"    <p>{esc(paragraph)}</p>\n"
    body += "  </div>\n"
    body += '  <nav class="article-nav">\n'
    if prev_essay:
        body += f'    <a href="/essays/{esc(prev_essay["slug"])}/">← Newer</a>\n'
    else:
        body += "    <span></span>\n"
    if next_essay:
        body += f'    <a href="/essays/{esc(next_essay["slug"])}/">Older →</a>\n'
    else:
        body += "    <span></span>\n"
    body += "  </nav>\n</article>\n"
    body += footer()
    return body


def render_feed(essays: list[dict]) -> str:
    last = essays[0]["published_at"] if essays else datetime.now(timezone.utc).isoformat()
    items = ""
    for essay in essays:
        content = "".join(f"<p>{esc(p)}</p>" for p in essay["body"])
        source = "\n"
        if essay.get("source_url") and essay.get("title_es"):
            source = f'      <source url="{xml(essay["source_url"])}">{xml(essay["title_es"])}</source>\n'
        items += f"""    <item>
      <title>{xml(essay['title_en'])}</title>
      <link>{essay_url(essay)}</link>
      <guid isPermaLink="true">{essay_url(essay)}</guid>
      <pubDate>{rfc822(essay['published_at'])}</pubDate>
      <description><![CDATA[{content}]]></description>
{source.rstrip()}
    </item>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Impermanente — Selected Essays in English</title>
    <link>{SITE_URL}/</link>
    <description>Selected essays by J.R. Cruciani in English.</description>
    <language>en</language>
    <lastBuildDate>{rfc822(last)}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{items}  </channel>
</rss>
"""


def render_sitemap(essays: list[dict]) -> str:
    # (loc, lastmod, alternates[(lang, href)]) ; lastmod = fecha del contenido, no del build.
    def lastmod(e: dict) -> str:
        return (e.get("updated_at") or e["published_at"])[:10]
    entries = [(SITE_URL + "/", max(lastmod(e) for e in essays), [])]
    for essay in essays:
        en = essay_url(essay)
        es = essay.get("source_url")
        alts = [("en", en), ("es", es)] if es else []
        entries.append((en, lastmod(essay), alts))
        if es:
            entries.append((es, lastmod(essay), alts))
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    for loc, mod, alts in entries:
        body += f"  <url><loc>{xml(loc)}</loc><lastmod>{mod}</lastmod>"
        for lang, href in alts:
            body += f'<xhtml:link rel="alternate" hreflang="{lang}" href="{xml(href)}"/>'
        body += "</url>\n"
    body += "</urlset>\n"
    return body


ROBOTS_TEMPLATE = """# Política: CC BY 4.0. Indexar, citar, resumir y enlazar con atribución: sí.
# Entrenar modelos: no. Declarado también en /llms.txt.

User-agent: *
Allow: /
Content-Signal: search=yes, ai-input=yes, ai-train=no

# Crawlers de entrenamiento
User-agent: GPTBot
User-agent: CCBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: meta-externalagent
User-agent: ClaudeBot
User-agent: anthropic-ai
User-agent: cohere-ai
User-agent: Bytespider
Disallow: /

# Búsqueda y respuesta en tiempo real (permitidos)
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
User-agent: DuckAssistBot
User-agent: MistralAI-User
User-agent: Bingbot
User-agent: Googlebot
Allow: /
Content-Signal: search=yes, ai-input=yes, ai-train=no

Sitemap: https://<HOST>/sitemap.xml
"""


def render_robots() -> str:
    return ROBOTS_TEMPLATE.replace("<HOST>", SITE_DOMAIN)


def render_llms(essays: list[dict]) -> str:
    out = ["# Impermanente — Selected Essays in English", "", f"> {BIO_EN}", "",
           "English edition of selected essays by J.R. Cruciani, translated and edited from the Spanish originals on impermanente.es.",
           "", "## Essays", ""]
    for e in essays:
        line = f"- {e['published_at'][:10]} [{e['title_en']}]({essay_url(e)})"
        if e.get("source_url"):
            line += f" (Spanish original: {e['source_url']})"
        out.append(line)
    out += ["", "## Related", "",
            f"- [Photography (fotos.impermanente.es)]({PHOTOS_URL}/)",
            f"- [Main site llms.txt (Spanish)]({PARENT_URL}/llms.txt)",
            f"- [Publications]({PARENT_URL}/publicaciones/)",
            f"- [RSS feed]({SITE_URL}/feed.xml)",
            "", "## Policy", "",
            f"- License: CC BY 4.0 ({LICENSE_URL}). Quote, summarise and link with attribution to J.R. Cruciani.",
            "- AI training: not permitted. Search and real-time answers with attribution: permitted.",
            "- Content-Signal: search=yes, ai-input=yes, ai-train=no", ""]
    return "\n".join(out)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(output_dir: Path) -> None:
    essays = load_essays()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    write(output_dir / "index.html", render_index(essays))
    for i, essay in enumerate(essays):
        prev_essay = essays[i - 1] if i > 0 else None
        next_essay = essays[i + 1] if i + 1 < len(essays) else None
        write(output_dir / "essays" / essay["slug"] / "index.html", render_essay(essay, prev_essay, next_essay))

    write(output_dir / "feed.xml", render_feed(essays))
    write(output_dir / "sitemap.xml", render_sitemap(essays))
    write(output_dir / "robots.txt", render_robots())
    write(output_dir / "llms.txt", render_llms(essays))
    write(output_dir / f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY + "\n")
    write(output_dir / "CNAME", SITE_DOMAIN + "\n")
    write(output_dir / "404.html", head("Not found | Impermanente", "This page does not exist.", SITE_URL + "/404.html") + "<h1>404</h1><p>This page does not exist. Return to <a href=\"/\">the English edition</a>.</p>" + footer())
    print(f"Built {len(essays)} essays in {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    build(args.output_dir)


if __name__ == "__main__":
    main()
