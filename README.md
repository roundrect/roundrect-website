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

## Update feeds

Each app's Sparkle feed is `https://roundrect.download/updates/<app>/appcast.xml`. No such file exists in this repo:
one Cloudflare **Single Redirect** rule on the `roundrect.download` zone sends every app's feed to the `appcast.xml`
attached to that app's latest GitHub release.

| | |
|---|---|
| Name | `Update feeds → GitHub latest release` |
| When | `http.request.full_uri wildcard "https://roundrect.download/updates/*/appcast.xml"` |
| Then | dynamic, `wildcard_replace(http.request.full_uri, "https://roundrect.download/updates/*/appcast.xml", "https://github.com/roundrect/${1}/releases/latest/download/appcast.xml")` |
| Status | **302**, query string not kept |

It is a 302 and never a 301: a client may cache a 301 for good, and the point of the indirection is being able to move
the feeds off GitHub later. The rule lives in the Cloudflare dashboard (Rules ▸ Redirect Rules), not in this repo.
Check it with:

    curl -sI https://roundrect.download/updates/swurl/appcast.xml    # 302, location: …/roundrect/swurl/releases/latest/download/appcast.xml
