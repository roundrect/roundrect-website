# Sharing: the link preview (the thumbnail card)

What makes a roundrect.download link show a card (title, description and picture) when it is pasted into iMessage,
Slack, WhatsApp, Discord, Telegram, X, LinkedIn or Facebook, and how to check it.

## What a link preview needs

| Needed | Here |
|---|---|
| **Open Graph tags** in each page's `<head>` | every page, including every blog page |
| **Twitter/X card tags**: `twitter:card = summary_large_image` and `twitter:image` | every page |
| **An image at an absolute `https://` URL, 1200x630**, under about 300 KB (WhatsApp is the strictest) | `og-image.png`, 1200x630, about 100 KB |
| **The crawlers can fetch the page and the image** (a CDN's bot protection can block them) | to be checked once the site is live (below) |
| A small square icon (iMessage and iPhone home screens use it) | `apple-touch-icon.png` 180x180, plus `favicon.png` 64x64 |

## The tags on every page

- `<link rel="canonical">` and `<meta name="description">` (the page's own)
- `og:type`: `website` (home, Shorty, privacy, blog list) or `article` (a post)
- `og:site_name` (RoundRect), `og:locale` (en_US)
- `og:title`, `og:description`: the page's own (a post: "Title — RoundRect blog")
- `og:url`, equal to the canonical URL
- `og:image` = `og:image:secure_url` = `https://roundrect.download/og-image.png`, `og:image:type` (image/png),
  `og:image:width` 1200, `og:image:height` 630, `og:image:alt`
- `twitter:card` (`summary_large_image`), `twitter:title`, `twitter:description`, `twitter:image`,
  `twitter:image:alt`
- `<link rel="icon">` and `<link rel="apple-touch-icon">`
- Posts also carry `article:published_time` and one `article:tag` per topic.

The root pages are hand-written, so a tag change is made in each. The blog pages' tags live in `head()` in
`tools/blog-build.py`: change it and rebuild, never the generated `blog/*.html`.

## The picture

- `og-image.png`: 1200x630, the wordmark with the orange rounded-rectangle mark, "Small apps for the Mac.", a line
  about Shorty, and a `roundrect.download` pill. All pages share it. It does not say anything that goes stale (it
  does not say a release state).
- It was drawn with Pillow (no source file is kept in the repo): re-make it the same way, keep it 1200x630 and
  under about 200 KB. `apple-touch-icon.png` and `favicon.png` are the mark on white.
- The alt text is "RoundRect: small apps for the Mac, with an orange rounded-rectangle mark."

## Checking it

1. **Every page has the full set**: parse each page's `<head>` and assert the tags above, absolute `https://` image
   URLs, and `og:url` equal to the canonical.
2. **The crawlers can fetch**: the page and the image must return 200 for each crawler's user agent:
   ```sh
   for ua in "facebookexternalhit/1.1" "Twitterbot/1.0" "Slackbot-LinkExpanding 1.0" "LinkedInBot/1.0" \
             "Mozilla/5.0 (compatible; Discordbot/2.0)" "WhatsApp/2.23.20.0" "TelegramBot (like TwitterBot)"; do
     echo "$ua: page $(curl -s -o /dev/null -w '%{http_code}' -A "$ua" https://roundrect.download/)" \
          "image $(curl -s -o /dev/null -w '%{http_code}' -A "$ua" https://roundrect.download/og-image.png)"
   done
   ```
   Bot protection at the CDN can block generic clients (Python's default user agent gets 403); if a platform stops
   showing cards, run this first.
3. **What a platform will show**: a preview service such as `https://api.microlink.io/?url=https://roundrect.download/`
   returns the title, description and image it extracts.

## When a card is stale

Platforms cache a URL's card, often for days. iMessage, Slack, WhatsApp, Discord, Telegram and X cache per exact
URL: paste it with a query string (`https://roundrect.download/?v=2`) and they fetch afresh. Facebook:
https://developers.facebook.com/tools/debug/ ("Scrape Again"). LinkedIn: https://www.linkedin.com/post-inspector/.
