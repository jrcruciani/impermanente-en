# impermanente-en

Static English edition for `https://en.impermanente.es/`.

It publishes selected essays by J.R. Cruciani in English, including translated and edited pieces from the Spanish originals at `https://impermanente.es/`. The site is independent from the Spanish Micro.blog feed and from `fotos.impermanente.es`.

## Build

```bash
python3 scripts/build_site.py
python3 scripts/qa_translation.py
```

Generated output goes to `output/` and includes:

- `index.html`
- `essays/<slug>/index.html`
- `feed.xml`
- `sitemap.xml`
- `robots.txt`
- `CNAME`
- `404.html`

## Deployment

GitHub Actions deploys `output/` to `gh-pages` with the custom domain `en.impermanente.es`.

After creating the GitHub repository and pushing `main`, configure GitHub Pages for the `gh-pages` branch and add the DNS `CNAME` record for `en.impermanente.es`.
