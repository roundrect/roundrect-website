# Design guide (roundrect.download)

The rules for the RoundRect site: the home page, the Shorty page, the privacy policy and the blog. The tokens live
in `:root` of `site.css`; where this file and the CSS differ, the CSS is the detail.

## 1. Principles

1. **One site, one look.** Black on white, 1px black borders, pills, a hard black shadow (`0 4px 0 #000`) on cards,
   code blocks and figures, and a single accent with two tints. The header and footer are the same on every page.
2. **Built for reading and scanning.** One column, 70ch wide, 17px body at line-height 1.65 (16px under 600px).
   Bands (a full-width block, white or `--tint`) on the home page, one reading column everywhere else.
3. **Fast.** Static HTML and `site.css`, nothing else. No JavaScript at all, no web fonts, no third-party requests.
   Every page is fully readable and usable as plain HTML.
4. **Accessible.** A skip link to `#main` on every page, one `h1`, no skipped heading levels, a 3px black focus
   ring, scroll boxes (tables, code) that are keyboard-focusable and labelled, nothing conveyed by colour alone.
5. **Works at 390px.** No sideways page scroll ever; wide content scrolls inside its own box.

## 2. Colour tokens

| token | value | used for |
|---|---|---|
| `--accent` | `#ff7a1a` (a warm orange) | the logo mark, pills, link-hover highlight, chip fill source |
| `--tint` | accent 55% on white (`#94bfff` fallback) | the hero band, chips, table heads, notices |
| `--tint-soft` | accent 24% on white (`#d8e8ff` fallback) | inline code, code caption bars, contents box |
| `--ink` | `#000` | text, borders, shadows, focus ring |
| `--ink-2` | `#2b2b2d` | secondary text, summaries, captions |
| `--hair` | black 22% | hairlines, row lines, h2 rules |
| grey | `#555` | shell comments, heading anchors (the lightest text) |

**Contrast rule: text on the accent or a tint is always black (or `--ink-2` on a tint).** Black on `--accent` is
8.05:1; black on `--tint` about 12:1; `--ink-2` on `--tint` about 8:1; `#555` on `--tint-soft` about 5.9:1 (tints are
sRGB estimates of the `color-mix` result). The accent is never used as a text colour on white (it is 2.6:1 there). Any new accent must keep black-on-accent at
4.5:1 or better. No other hue: no blue links, no red warnings, no syntax colours.

## 3. Typography

System stacks only (`--font`, `--mono`).

| element | spec |
|---|---|
| band `h1` | clamp(40px, 8vw, 80px), 700, -0.035em |
| `.prose h1` | clamp(34px, 6vw, 46px), 700, -0.03em, balanced |
| `h2` | 28px (24px under 600px), 700, 1px hairline above, 2.2em space above |
| `h3` | 21px, 700 |
| body | 17px / 1.65 in `.prose`; 17px / 1.5 elsewhere; paragraphs 1.1em apart |
| table text | 15px / 1.45; small labels 12-14px |
| code | mono; inline 0.88em on `--tint-soft`; blocks 14.5px (13px under 600px) |

## 4. Components

- **Header** `.nav`: sticky, 1px black bottom rule, the wordmark (a CSS rounded-rectangle `.mark` in the accent with
  a hard shadow, then "RoundRect"), a few text links (`aria-current="page"` underlines the current one), an Atom
  feed pill. It wraps on narrow screens; there is no menu button and no script.
- **Footer** `.foot`: a link list and two small lines (status and copyright).
- **Pill** `.pill`: accent fill, black text, 1px black border, fully round; hover = black with white text.
  `.pill.big` for the main call to action, `.pill.plain` for a white one.
- **Band** `.band`; `.tone` bands use `--tint` with a black bottom rule.
- **Card** `.card`: white, 1px black border, 18px radius, hard shadow. `.status` is its small round label
  (for example "Not yet released").
- **Notice** `.notice`: a `--tint` panel with a black border, for the one thing a reader must not miss.
- **Chip** `.chip`: a topic label on a post, `--tint` fill.
- **Code block** `figure.code`: white panel, black border, 14px radius, hard shadow, a `--tint-soft` caption bar with
  the language in mono. `pre` never wraps; it scrolls inside the block and is focusable. No syntax colours; only
  shell comments are grey.
- **Table** `.tablewrap`: bordered, `overflow-x: auto`, `tabindex="0"`, `role="region"` and an `aria-label`.
- **Blockquote** (from the Markdown renderer): a bold lead-in makes a *note* (4px black left rule); "Warning" makes a
  `--tint` callout; no lead-in is an *example* (mono on `--tint-soft`).
- **Links**: black, underlined, 3px offset; in the reading column a hover fills with the accent.
- **Figure** `figure.shot`: image in a black frame with the hard shadow and a caption; `width` and `height` set.
- **Print**: header hidden, shadows removed.

## 5. Pages and URLs

- Root pages are hand-written: `index.html` (`/`), `shorty.html` (`/shorty`), `privacy.html` (`/privacy`),
  `404.html`. Links to them are clean (no `.html`); GitHub Pages serves `/shorty` from `shorty.html`.
- `404.html` uses root-absolute links, because it is served at whatever path was missing.
- `blog/index.html` is `/blog/`; each post is `blog/<slug>.html` served at `/blog/<slug>`. A link to a blog page
  ending `.html` is refused by the build. Images are `blog/images/<slug>/…`.
- `sitemap.xml` keeps the root entries; `blog-build.py` rewrites the blog entries. `robots.txt` allows all.
- `tools/stamp.sh` appends `?v=<hash>` to every `site.css` link, because the host's cache can keep the old file for
  hours. Run it after any change to `site.css` or any page.

## 6. The blog

Generated by `python3 tools/blog-build.py ../roundrect-posts` from the private posts repo (front matter and writing
rules are in its README and STYLE.md). It writes `blog/index.html`, `blog/<slug>.html`, `blog/images/<slug>/`,
`blog/feed.xml` (Atom, full content, absolute URLs) and the blog entries of `sitemap.xml`.

- Feed `<id>`s are `ID_BASE + 'blog/' + slug` and **never change**; `ID_BASE` is pinned to
  `https://roundrect.download/` in `blog-build.py`.
- A published address never disappears or changes hands without `--retire` or `--replace`.
- Posts render with the same components as the pages (code, tables, notes, figures). Headings are `##` and below.
- Drafts are built only with `--drafts --out <dir outside this repo>`.

## 7. Link previews

See `SHARING-LINK-PREVIEW.md`: every page carries the Open Graph and Twitter tags and shares one 1200x630
`og-image.png`.
