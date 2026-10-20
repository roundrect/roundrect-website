#!/usr/bin/env python3
"""tools/markdown.py — the small dependency-free Markdown renderer that tools/blog-build.py imports.

Stdlib only, a converter for exactly the Markdown a post uses: ATX headings, paragraphs, **bold**, *italic*, `code`,
links, bare URLs, images (a paragraph of its own), nested bullet/numbered lists, pipe tables, blockquotes, fenced code,
rules and HTML comments (dropped). It FAILS (BuildError, with file:line) on anything else. Adapted from the renderer
that backs another static site; the manual-specific parts (chapters, sidebar, diagrams, twins) are removed."""
import html, os, posixpath, re, struct, unicodedata
from collections import Counter

# A blockquote whose bold lead-in is one of these is a warning callout; any other bold lead-in is a note, and a quote
# with no bold lead-in is an example. Compared without the trailing full stop.
WARNING_LEADS = ('Warning',)
KEY_RE = re.compile(r'^(?:(?:Ctrl|Cmd|Shift|Alt|Option)(?:[-+]\S+)*|Enter|Esc|Escape|Return|Tab)$')
PUNCT = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')

class BuildError(Exception):
    pass


def fail(where, msg):
    raise BuildError('%s: %s' % (where, msg))


def esc(s):
    return html.escape(s, quote=True)


def slugify(text):
    """GitHub's heading id: lower case, keep letters/marks/numbers/connectors, spaces and hyphens; spaces -> '-'."""
    out = []
    for ch in text.lower():
        cat = unicodedata.category(ch)
        if ch in ' -' or cat[0] in 'LMN' or cat == 'Pc':
            out.append('-' if ch == ' ' else ch)
    return ''.join(out)


def strip_tags(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h))


# ------------------------------------------------------------------------------------------------ inline Markdown
class Inline:
    def __init__(self, page, where):
        self.page, self.where = page, where

    def render(self, s):
        toks = self.tokens(s)
        self.emphasis(toks)
        out = []
        for t in toks:
            if t[0] == 'd':
                out.append(t[1]['pre'] + '*' * t[1]['n'] + t[1]['post'])
            else:
                out.append(t[1])
        return ''.join(out)

    def tokens(self, s):
        toks, buf, i, n = [], [], 0, len(s)

        def flush():
            if buf:
                toks.append(('h', esc(''.join(buf))))
                buf.clear()

        while i < n:
            c = s[i]
            if c == '\\' and i + 1 < n and s[i + 1] in PUNCT:
                buf.append(s[i + 1]); i += 2
            elif c == '`':
                j = i
                while j < n and s[j] == '`':
                    j += 1
                run = j - i
                m = re.compile(r'(?<!`)`{%d}(?!`)' % run).search(s, j)
                if not m:
                    fail(self.where, 'unclosed code span: %r' % s[i:i + 40])
                code = s[j:m.start()]
                if len(code) > 1 and code[0] == ' ' and code[-1] == ' ' and code.strip():
                    code = code[1:-1]
                flush(); toks.append(('h', '<code>%s</code>' % esc(code))); i = m.end()
            elif c == '!' and s.startswith('![', i):
                fail(self.where, 'an image inside text (images must be a paragraph of their own)')
            elif c == '[':
                end = self.close_bracket(s, i)
                if end is not None and end + 1 < n and s[end + 1] == '(':
                    close = s.find(')', end + 2)
                    url = s[end + 2:close] if close > 0 else ''
                    if close < 0 or not url or re.search(r'\s', url):
                        fail(self.where, 'a link whose target is not a plain URL: %r' % s[i:i + 60])
                    flush()
                    toks.append(('h', '<a href="%s">%s</a>' % (esc(self.page.link(url, self.where)),
                                                               Inline(self.page, self.where).render(s[i + 1:end]))))
                    i = close + 1
                else:
                    if s.startswith('](', i) or (end is not None and s[end + 1:end + 2] == '['):
                        fail(self.where, 'reference-style link: %r' % s[i:i + 40])
                    buf.append(c); i += 1
            elif c == '*':
                j = i
                while j < n and s[j] == '*':
                    j += 1
                before = s[i - 1] if i else ' '
                after = s[j] if j < n else ' '
                lf = not after.isspace() and (after not in PUNCT or before.isspace() or before in PUNCT)
                rf = not before.isspace() and (before not in PUNCT or after.isspace() or after in PUNCT)
                flush(); toks.append(('d', {'n': j - i, 'open': lf, 'close': rf, 'pre': '', 'post': '', 'at': i}))
                i = j
            elif c == '<' and s.startswith('<!--', i):
                fail(self.where, 'an HTML comment inside text')
            elif re.compile(r'https?://[\w-]').match(s, i) and (i == 0 or not s[i - 1].isalnum()) and \
                    (i == 0 or s[i - 1] not in '(<'):
                m = re.compile(r'https?://[^\s<]+').match(s, i)
                url = m.group(0)
                while url and (url[-1] in '.,:;!?\'"*' or (url[-1] == ')' and url.count('(') < url.count(')'))):
                    url = url[:-1]
                flush(); toks.append(('h', '<a href="%s">%s</a>' % (esc(url), esc(url)))); i += len(url)
            else:
                buf.append(c); i += 1
        flush()
        return toks

    def close_bracket(self, s, i):
        depth, j = 0, i
        while j < len(s):
            c = s[j]
            if c == '\\':
                j += 2; continue
            if c == '`':
                k = j
                while k < len(s) and s[k] == '`':
                    k += 1
                m = re.compile(r'(?<!`)`{%d}(?!`)' % (k - j)).search(s, k)
                j = m.end() if m else k
                continue
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return j
            j += 1
        return None

    def emphasis(self, toks):
        """CommonMark's delimiter matching for '*' runs (no '_' emphasis: the manual uses none)."""
        k = 0
        while k < len(toks):
            t = toks[k]
            if t[0] == 'd' and t[1]['close'] and t[1]['n']:
                o = k - 1
                while o >= 0:
                    d = toks[o]
                    if d[0] == 'd' and d[1]['open'] and d[1]['n']:
                        both = (d[1]['open'] and d[1]['close']) or (t[1]['open'] and t[1]['close'])
                        if not (both and (d[1]['n'] + t[1]['n']) % 3 == 0 and (d[1]['n'] % 3 or t[1]['n'] % 3)):
                            break
                    o -= 1
                if o >= 0:
                    d = toks[o]
                    for m in range(o + 1, k):        # delimiters in between can no longer match
                        if toks[m][0] == 'd':
                            toks[m] = ('h', toks[m][1]['pre'] + '*' * toks[m][1]['n'] + toks[m][1]['post'])
                    use = 2 if d[1]['n'] >= 2 and t[1]['n'] >= 2 else 1
                    inner = toks[o + 1:k]
                    if use == 2 and len(inner) == 1 and inner[0][0] == 'h' and KEY_RE.match(strip_tags(inner[0][1])) \
                            and '<' not in inner[0][1]:
                        key = html.unescape(inner[0][1])
                        parts = re.split(r'(?<=[A-Za-z])([-+])(?=.)', key)
                        toks[o + 1] = ('h', ''.join(esc(p) if p in '-+' else '<kbd>%s</kbd>' % esc(p) for p in parts))
                    else:
                        tag = 'strong' if use == 2 else 'em'
                        d[1]['post'] = '<%s>' % tag + d[1]['post']
                        t[1]['pre'] = t[1]['pre'] + '</%s>' % tag
                    d[1]['n'] -= use
                    t[1]['n'] -= use
                    continue                          # the closer may close more
            k += 1
        for t in toks:
            if t[0] == 'd' and t[1]['n'] and (t[1]['open'] or t[1]['close']):
                fail(self.where, 'an unmatched * (emphasis that does not close)')


# ------------------------------------------------------------------------------------------------- block Markdown
FENCE = re.compile(r'^(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$')
BULLET = re.compile(r'^([-*+])( +)(?=\S)')
ORDERED = re.compile(r'^(\d{1,9})([.)])( +)(?=\S)')
HR = re.compile(r'^(?:-{3,}|\*{3,}|_{3,})\s*$')
TABLE_SEP = re.compile(r'^\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$')


def starts_block(lines, i, in_para):
    l = lines[i]
    if FENCE.match(l) or HEADING.match(l) or l.startswith('>') or HR.match(l) or l.startswith('<!--'):
        return True
    if BULLET.match(l):
        return True
    m = ORDERED.match(l)
    if m and (not in_para or m.group(1) == '1'):
        return True
    if l.startswith('|') and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
        return True
    return False


def parse_blocks(lines, ln0, page):
    """lines are already de-indented to this container's content column; ln0 = the source line of lines[0]."""
    blocks, i, n = [], 0, len(lines)
    where = lambda k: '%s:%d' % (page.name, ln0 + k)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line[0] in ' \t':
            fail(where(i), 'unexpected indentation (an indented code block, or a lazy continuation line): %r' % line[:60])
        m = FENCE.match(line)
        if m:
            mark = m.group(1)
            j = i + 1
            while j < n and not re.match(r'^%s%s*\s*$' % (re.escape(mark), re.escape(mark[0])), lines[j]):
                j += 1
            if j >= n:
                fail(where(i), 'unclosed code fence')
            blocks.append({'t': 'code', 'lang': m.group(2).lower(), 'text': '\n'.join(lines[i + 1:j]), 'ln': ln0 + i})
            i = j + 1; continue
        m = HEADING.match(line)
        if m:
            blocks.append({'t': 'h', 'level': len(m.group(1)), 'src': m.group(2), 'ln': ln0 + i})
            i += 1; continue
        if line.startswith('#'):
            fail(where(i), 'a heading without a space after the #')
        if HR.match(line):
            blocks.append({'t': 'hr'}); i += 1; continue
        if line.startswith('<!--'):
            j = i
            while '-->' not in lines[j]:
                j += 1
                if j >= n:
                    fail(where(i), 'unclosed HTML comment')
            if not lines[j].rstrip().endswith('-->'):
                fail(where(j), 'text after an HTML comment')
            i = j + 1; continue
        if line.startswith('<') and re.match(r'<[A-Za-z/]', line):
            fail(where(i), 'raw HTML: %r' % line[:60])
        if line.startswith('>'):
            j, inner = i, []
            while j < n and lines[j].startswith('>'):
                inner.append(re.sub(r'^> ?', '', lines[j])); j += 1
            if j < n and lines[j].strip():
                fail(where(j), 'a lazy continuation line after a blockquote')
            blocks.append({'t': 'quote', 'children': parse_blocks(inner, ln0 + i, page), 'ln': ln0 + i,
                           'raw': inner})
            i = j; continue
        if line.startswith('|') and i + 1 < n and TABLE_SEP.match(lines[i + 1]):
            if ':' in lines[i + 1]:
                fail(where(i + 1), 'table column alignment is not supported')
            head = split_row(line)
            rows, j = [], i + 2
            while j < n and lines[j].startswith('|'):
                r = split_row(lines[j])
                if len(r) != len(head):
                    fail(where(j), 'a ragged table row: %d cells, the header has %d' % (len(r), len(head)))
                rows.append((r, ln0 + j)); j += 1
            if len(split_row(lines[i + 1])) != len(head):
                fail(where(i + 1), 'the table separator does not match the header')
            if j < n and lines[j].strip():
                fail(where(j), 'a line straight after a table that is not a table row')
            blocks.append({'t': 'table', 'head': head, 'rows': rows, 'ln': ln0 + i})
            i = j; continue
        if BULLET.match(line) or ORDERED.match(line):
            i = parse_list(lines, i, ln0, page, blocks); continue
        # a paragraph
        j = i + 1
        while j < n and lines[j].strip() and not starts_block(lines, j, True):
            if re.match(r'^(=+|-+)\s*$', lines[j]):
                fail(where(j), 'a setext heading (underlined)')
            if lines[j][0] in ' \t':
                fail(where(j), 'an indented continuation line in a paragraph')
            j += 1
        text = ' '.join(l.strip() for l in lines[i:j])
        img = re.match(r'^!\[([^\]]*)\]\(([^)\s]+)\)$', text)
        if img:
            blocks.append({'t': 'img', 'alt': img.group(1), 'src': img.group(2), 'ln': ln0 + i})
        else:
            blocks.append({'t': 'p', 'src': text, 'ln': ln0 + i})
        i = j
    return blocks


def split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'):
        s = s[:-1]
    cells = re.split(r'(?<!\\)\|', s)
    return [c.strip().replace('\\|', '|') for c in cells]


def parse_list(lines, i, ln0, page, blocks):
    n = len(lines)
    first = BULLET.match(lines[i]) or ORDERED.match(lines[i])
    ordered = bool(ORDERED.match(lines[i]))
    kind = first.group(2) if ordered else first.group(1)
    items, loose, start = [], False, int(first.group(1)) if ordered else 1
    while i < n:
        m = (ORDERED.match(lines[i]) if ordered else BULLET.match(lines[i]))
        if not m or (m.group(2) if ordered else m.group(1)) != kind:
            break
        indent = len(m.group(0))
        if len(m.group(m.lastindex)) > 4:
            fail('%s:%d' % (page.name, ln0 + i), 'a list item with more than 4 spaces after its marker')
        body, j = [lines[i][indent:]], i + 1
        while j < n:
            l = lines[j]
            if not l.strip():
                body.append(''); j += 1; continue
            ind = len(l) - len(l.lstrip(' '))
            if ind >= indent:
                body.append(l[indent:]); j += 1; continue
            if lines[j - 1].strip() and ind == 0 and not (starts_block(lines, j, True) or ORDERED.match(l)):
                fail('%s:%d' % (page.name, ln0 + j), 'a lazy continuation line in a list item (indent it)')
            if ind > 0:
                fail('%s:%d' % (page.name, ln0 + j), 'a list line indented less than its item\'s text')
            break
        while body and not body[-1].strip():
            body.pop()
        if any(not b.strip() for b in body):
            loose = True
        items.append(parse_blocks(body, ln0 + i, page))
        k = j
        while k < n and not lines[k].strip():
            k += 1
        if k < n and k > j and (ORDERED.match(lines[k]) if ordered else BULLET.match(lines[k])):
            loose = True
        if k < n and (ORDERED.match(lines[k]) if ordered else BULLET.match(lines[k])):
            i = k
        else:
            i = j
            break
    blocks.append({'t': 'list', 'ordered': ordered, 'start': start, 'items': items, 'loose': loose})
    return i


# --------------------------------------------------------------------------------------------------------- pages
class Page:
    """Base of blog-build.py's Post: the block renderer. A subclass sets .build (warnings, images), .name, .blocks."""

    @staticmethod
    def walk(blocks):
        for b in blocks:
            yield b
            if b['t'] == 'quote':
                yield from Page.walk(b['children'])
            elif b['t'] == 'list':
                for it in b['items']:
                    yield from Page.walk(it)

    def link(self, url, where):
        raise NotImplementedError

    # ---- rendering
    def inline(self, src, ln):
        return Inline(self, '%s:%d' % (self.name, ln)).render(src)

    def render(self, blocks, top=False):
        out, prev_heading = [], self.title_src
        for b in blocks:
            t = b['t']
            if t == 'h':
                if b['level'] == 1:
                    continue
                prev_heading = b['plain']
                tag = 'h%d' % b['level']
                out.append('<%s id="%s">%s<a class="anchor" href="#%s" aria-label="Link to this section">#</a></%s>'
                           % (tag, b['id'], self.inline(b['src'], b['ln']), b['id'], tag))
            elif t == 'p':
                out.append('<p>%s</p>' % self.inline(b['src'], b['ln']))
            elif t == 'hr':
                out.append('<hr>')
            elif t == 'code':
                out.append(self.code(b))
            elif t == 'img':
                out.append(self.image(b))
            elif t == 'table':
                out.append(self.table(b, prev_heading))
            elif t == 'quote':
                out.append(self.quote(b))
            elif t == 'list':
                out.append(self.list(b))
        return '\n'.join(out)

    def code(self, b):
        self.code_blocks.append(b['text'])
        lang = b['lang'] or 'text'
        body = esc(b['text'])
        if lang in ('sh', 'bash', 'shell', 'zsh'):
            body = '\n'.join(shell_line(l) for l in b['text'].split('\n'))
        diagram = not b['lang'] and re.search(r'[─│┌┐└┘├┤┬┴┼═║╔╗╚╝]', b['text'])
        return ('<figure class="code%s"><figcaption>%s</figcaption><pre tabindex="0" role="region" aria-label="Code (%s)">'
                '<code>%s</code></pre></figure>' % (' diagram' if diagram else '', esc(lang), esc(lang), body))

    def image(self, b):
        raise NotImplementedError

    def table(self, b, label):
        head = ''.join('<th scope="col">%s</th>' % self.inline(c, b['ln']) for c in b['head'])
        rows = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % self.inline(c, ln) for c in r) for r, ln in b['rows'])
        wide = ' wide' if len(b['head']) >= 5 else ''
        return ('<div class="tablewrap%s" tabindex="0" role="region" aria-label="%s"><table>\n<thead><tr>%s</tr></thead>'
                '\n<tbody>\n%s\n</tbody></table></div>' % (wide, esc('Table: ' + label), head, rows))

    def quote(self, b):
        kids = b['children']
        first = kids[0] if kids else None
        lead = re.match(r'^\*\*(.+?)\*\*', first['src']) if first and first['t'] == 'p' else None
        inner = self.render(kids)
        if lead and lead.group(1).rstrip('.').strip() in WARNING_LEADS:
            self.build.warnings.append('%s: %s' % (self.name, lead.group(1)))
            return '<blockquote class="callout warn">\n%s\n</blockquote>' % inner
        return '<blockquote class="%s">\n%s\n</blockquote>' % ('note' if lead else 'example', inner)

    def list(self, b):
        tag = 'ol' if b['ordered'] else 'ul'
        attr = ' start="%d"' % b['start'] if b['ordered'] and b['start'] != 1 else ''
        items = []
        for it in b['items']:
            parts = []
            for k, c in enumerate(it):
                if c['t'] == 'p' and k == 0 and not b['loose']:
                    parts.append(self.inline(c['src'], c['ln']))
                else:
                    parts.append(self.render([c]))
            items.append('<li>%s</li>' % '\n'.join(parts))
        return '<%s%s>\n%s\n</%s>' % (tag, attr, '\n'.join(items), tag)


def shell_line(line):
    """Escape a shell line and grey its comment (a # at the start or after a space, outside quotes)."""
    q = None
    for k, c in enumerate(line):
        if q:
            if c == q:
                q = None
        elif c in '\'"':
            q = c
        elif c == '#' and (k == 0 or line[k - 1] in ' \t'):
            return esc(line[:k]) + '<span class="c">%s</span>' % esc(line[k:])
    return esc(line)


