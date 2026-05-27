> **Before you clone**
>
> What you see here is an artifact: the concrete shape my problem took. It almost certainly doesn't fit your personal scenario perfectly, and that's fine. The interesting part isn't the code, it's the pattern of how I thought about the problem — that's what transfers. Read it, steal the idea, write your own. If any of this was useful to you, after clicking on the star, drop by [impermanente.es](https://impermanente.es) — there are posts and photos you might like.
>
> Context: [Seguimos compartiendo el producto, no la idea](https://impermanente.es/2026/05/25/seguimos-compartiendo-el-producto-no.html)

---

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
