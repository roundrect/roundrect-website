#!/bin/bash
# tools/stamp.sh — run (after tools/blog-build.py) before every commit that changes site.css or a page.
# Fingerprints the stylesheet link in every page — the root pages and blog/*.html, each by its own relative path
# (?v=<8 hex of the file's sha256>): the host tells browsers to keep the file for hours, so a page published with a
# NEW stylesheet could otherwise be shown with the OLD one. Idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
import hashlib, os, re, glob
def fp(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:8]
n = 0
for page in sorted(glob.glob('*.html') + glob.glob('blog/*.html')):
    s = open(page, encoding='utf-8').read()
    for asset in ('site.css',):
        rel = os.path.relpath(asset, os.path.dirname(page) or '.')
        new = re.sub(r'(href|src)="(/?)%s(\?v=[0-9a-f]+)?"' % re.escape(rel),
                     lambda m: '%s="%s%s?v=%s"' % (m.group(1), m.group(2), rel, fp(asset)), s)
        n += new != s
        s = new
    open(page, 'w', encoding='utf-8').write(s)
print('stamped: site.css = %s, %d page(s) changed' % (fp('site.css'), n))
PY
