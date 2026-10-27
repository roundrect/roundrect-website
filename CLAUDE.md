# CLAUDE.md — roundrect-website

The public static site for **roundrect.download**. Plain HTML and `site.css`, served by GitHub Pages. This repo is
**public**: everything committed here, this file included, is visible to anyone.

Read [`README.md`](README.md) for the layout and [`DESIGN.md`](DESIGN.md) before touching a page or `site.css`. Blog
posts are written in the private sibling repo `../roundrect-posts` (its `README.md` has the front matter, its
`STYLE.md` the writing rules).

## Rules

- **Generated files are never edited by hand.** `blog/` is the output of `tools/blog-build.py`; change the post or
  the tool, then rebuild. The `?v=` fingerprints on stylesheet links come from `tools/stamp.sh`.
- **Drafts never land here.** Preview with `--drafts --out <a dir outside this repo>`; the build refuses an `--out`
  inside it.
- **A published slug never changes.** The build refuses to drop or re-use one without `--retire SLUG` or
  `--replace SLUG`; say why in the commit.
- **No JavaScript except `copy.js`, no web fonts, no third-party requests, no analytics.** `copy.js` (same host, no
  requests, nothing stored) adds a Copy button to code blocks; a page loads it only if it has one (`blog-build.py` does
  this for posts; a hand-written page adds `<script src="copy.js" defer></script>` after its stylesheet link), and
  without it one click still selects a whole block. Any other script needs the owner's say-so. One accent (`--accent`, orange `#ff7a1a`);
  text on the accent or a tint is always black.
- **Nothing private goes in this repo:** no tokens, no draft text, no links to private repos.
- **Commit as the GitHub noreply address.** Check `git config user.email` before the first commit in a new clone.

## Build, verify, deploy

```bash
python3 tools/blog-build.py ../roundrect-posts && tools/stamp.sh   # after any post, page or site.css change
git status                                                         # commit the generated output with the change
```

Machine-verifiable: the build succeeds (it validates front matter, images, links and heading levels) and
`tools/stamp.sh` leaves no further diff on a second run.

Needs a human looking at a browser: layout at 390px and desktop width, the hard shadows and focus ring, link
previews (`SHARING-LINK-PREVIEW.md`). Serve locally with `python3 -m http.server` from the repo root. **Do not
claim a page change is done because the build passed.**

Deploy is a push to `main`. There is no CI and no server-side build: what is committed is what is served.
