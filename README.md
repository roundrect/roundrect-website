# roundrect-website

The public static site for **roundrect.download**: the RoundRect home page, the Shorty page, the privacy policy
and the blog. Plain HTML and one stylesheet, no scripts, no analytics.

- `index.html`, `shorty.html`, `privacy.html`, `404.html` — hand-written pages.
- `blog/` — **generated** from the private posts repo (`roundrect-posts`); never edit by hand.
- `site.css` — the one stylesheet and the design tokens. `DESIGN.md` is the guide; `SHARING-LINK-PREVIEW.md` the
  link-preview rules.
- `tools/blog-build.py` (+ `tools/markdown.py`, its Markdown renderer) and `tools/stamp.sh`.
- `CNAME`, `.nojekyll`, `robots.txt`, `sitemap.xml`, icons and `og-image.png`.

## Build

With the posts repo checked out beside this one:

    python3 tools/blog-build.py ../roundrect-posts && tools/stamp.sh

Then commit the result. Drafts: `python3 tools/blog-build.py ../roundrect-posts --drafts --out <dir outside this repo>`.

## Deploy

Push to `main`; GitHub Pages serves the repo root at the custom domain in `CNAME`. There is no CI and no build on
the server: the generated pages are committed.
