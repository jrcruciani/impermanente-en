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
AUTHOR_ID = "https://impermanente.es/about/#person"
AVATAR_URL = "https://avatars.micro.blog/avatars/2025/36/1810674.jpg"
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


def load_essays() -> list[dict]:
    essays = json.loads(DATA_PATH.read_text(encoding="utf-8"))
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
        "author": {"@id": AUTHOR_ID},
        "publisher": {"@id": AUTHOR_ID},
        "license": LICENSE_URL,
    }


def jsonld_essay(essay: dict) -> dict:
    return {
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
        "author": {"@id": AUTHOR_ID},
        "creator": {"@id": AUTHOR_ID},
        "publisher": {"@id": AUTHOR_ID},
        "license": LICENSE_URL,
        "isBasedOn": essay["source_url"],
        "translationOfWork": {
            "@type": "BlogPosting",
            "name": essay["title_es"],
            "url": essay["source_url"],
            "inLanguage": "es",
        },
        "keywords": essay.get("tags", []),
    }


def head(title: str, description: str, canonical: str, *, jsonld: list[dict] | None = None,
         source_url: str | None = None, body_class: str = "") -> str:
    jsonld_blocks = ""
    for block in jsonld or []:
        jsonld_blocks += f'\n<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>'
    alternate_es = f'<link rel="alternate" hreflang="es" href="{esc(source_url)}">' if source_url else ""
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
<meta property="og:type" content="article">
<meta property="og:locale" content="en_US">
<meta property="og:site_name" content="Impermanente — Selected Essays in English">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<link rel="alternate" type="application/rss+xml" href="{SITE_URL}/feed.xml" title="Impermanente — Selected Essays in English">
<link rel="me" href="{PARENT_URL}/">
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
    desc = "Seven selected essays by J.R. Cruciani, translated and edited from the Spanish originals."
    body = head(title, desc, SITE_URL + "/", jsonld=[jsonld_website()])
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
    body = head(title, essay["summary"], essay_url(essay), jsonld=[jsonld_essay(essay)],
                source_url=essay["source_url"], body_class="essay-page")
    body += f"""<article>
  <p class="edition-kicker">{fmt_date(essay['published_at'])}</p>
  <h1>{esc(essay['title_en'])}</h1>
  <p class="source-note">Translated and edited from <a href="{esc(essay['source_url'])}">{esc(essay['title_es'])}</a>.</p>
  <div class="article-body">
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
        items += f"""    <item>
      <title>{xml(essay['title_en'])}</title>
      <link>{essay_url(essay)}</link>
      <guid isPermaLink="true">{essay_url(essay)}</guid>
      <pubDate>{rfc822(essay['published_at'])}</pubDate>
      <description><![CDATA[{content}]]></description>
      <source url="{xml(essay['source_url'])}">{xml(essay['title_es'])}</source>
    </item>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Impermanente — Selected Essays in English</title>
    <link>{SITE_URL}/</link>
    <description>Selected essays by J.R. Cruciani, translated and edited from the Spanish originals.</description>
    <language>en</language>
    <lastBuildDate>{rfc822(last)}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{items}  </channel>
</rss>
"""


def render_sitemap(essays: list[dict]) -> str:
    urls = [(SITE_URL + "/", essays[0]["published_at"][:10], "weekly", "1.0")]
    for essay in essays:
        urls.append((essay_url(essay), essay["published_at"][:10], "monthly", "0.8"))
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for loc, lastmod, changefreq, priority in urls:
        body += f"  <url><loc>{xml(loc)}</loc><lastmod>{lastmod}</lastmod><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>\n"
    body += "</urlset>\n"
    return body


def render_robots() -> str:
    return f"""# robots.txt — en.impermanente.es
# Policy: SEO open + AIO allowed with attribution (CC BY 4.0)

User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: Claude-User
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: CopilotBot
Allow: /

User-agent: BingPreview
Allow: /

User-agent: MicrosoftPreview
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: GoogleOther
Allow: /

User-agent: Google-Agent
Allow: /

User-agent: Google-NotebookLM
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: CCBot
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

User-agent: Meta-ExternalFetcher
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: YouBot
Allow: /

User-agent: MistralAI-User
Allow: /

User-agent: MistralAI-Index
Allow: /

User-agent: DuckAssistBot
Allow: /

User-agent: Bytespider
Disallow: /

Sitemap: {SITE_URL}/sitemap.xml
"""


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
