"""Build uberblick.ai from pages into out.

Standard library only:

    python3 build.py

Every pages/<path>.html is one page. It starts with a <head> block (title,
description, the page's own stylesheet) and continues with the page's main
content. The build wraps it in the document skeleton and the shell every page
shares (top bar, a sidebar for its section, footer), links the shared stylesheet and writes it to
out/<path>/index.html, so the page is served at /<path> with no extension
(Cloudflare redirects /<path>/ there, see wrangler.jsonc). pages/index.html is
/, and pages/404.html is the not-found page served as out/404.html. Everything
in static/ is copied to out/ as it is: the shared stylesheet, the page
stylesheets, the fonts and the _headers and _redirects files.

The sidebar marks the page whose path matches the link; the top bar shows the
newest release tag when git can name one (a shallow checkout shows none).
A page's <!-- recent changes --> line becomes the five newest entries from
the repository's CHANGELOG.md (each section's date and summary paragraph) and
the blog, newest first. The site has no changelog page of its own; links go to
CHANGELOG.md on GitHub. The changelog is read from ../CHANGELOG.md when a uberblick-2
checkout sits beside this one and fetched from GitHub otherwise, so the build also
works from a checkout of the site alone; the release tag falls back the same way.

Blog posts live in pages/blog/<year>/<slug>.html and carry, in their <head>,
<meta name="date">, <meta name="author"> and <meta name="kind"> (release, design
note or building note); <meta name="draft" content="yes"> keeps a post out of
the index, the feed and the recent changes but still builds its page. The build
writes the post list into pages/blog/index.html's <!-- posts --> line, an Atom
feed to /blog/feed.xml, and gives blog pages a sidebar of posts.

Links inside the site are root-relative (/compare, /css/landing.css), so the
output is meant to be served, not opened as files:

    python3 -m http.server 8000 --directory site/out

SITE_URL sets the origin the canonical links name (default https://uberblick.ai),
so a second Pages project can serve the same pages on another host; SITE_NOINDEX,
set to anything, adds a robots noindex meta tag for a host that search engines
should not index.
"""
import html, json, os, re, shutil, subprocess, sys, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES, STATIC, OUT = ROOT / 'pages', ROOT / 'static', ROOT / 'out'
CHANGELOG, RECENT, POSTS = ROOT.parent / 'CHANGELOG.md', '<!-- recent changes -->', '<!-- posts -->'
CHANGELOG_URL = 'https://github.com/uberblick-ai/uberblick-2/blob/main/CHANGELOG.md'
REPO = 'https://github.com/uberblick-ai/uberblick-2'
RAW_CHANGELOG = 'https://raw.githubusercontent.com/uberblick-ai/uberblick-2/main/CHANGELOG.md'
API_CHANGELOG = 'https://api.github.com/repos/uberblick-ai/uberblick-2/contents/CHANGELOG.md'
TAGS = 'https://api.github.com/repos/uberblick-ai/uberblick-2/tags?per_page=100'
SITE = os.environ.get('SITE_URL', 'https://uberblick.ai').rstrip('/')
NOINDEX = '<meta name="robots" content="noindex">\n' if os.environ.get('SITE_NOINDEX') else ''

SKELETON = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/shared.css">
{head}{canonical}{noindex}</head>
<body>
<header class="top">
  <a class="mark" href="/">uberblick</a>
  {version}<nav aria-label="Site">
    <a href="/docs/install">Docs</a>
    <a href="/guides">Guides</a>
    <a href="/blog">Blog</a>
    <a href="/compare">Compare</a>
    <a href="https://github.com/uberblick-ai/uberblick-2">GitHub</a>
{legacy}  </nav>
</header>
<div class="layout{solo}">
{aside}  <main class="main">
{body}
{about}  </main>
</div>
<footer class="foot">
  <div><h3>Projects</h3><ul>
    <li><a href="/">Uberblick</a></li>
    <li><a href="https://agents.uberblick.ai">ub-agents</a></li>
    <li><a href="https://skills.uberblick.ai">Skills</a></li>
    <li><a href="https://github.com/uberblick-ai/ablauf">ablauf</a></li>
    <li><a href="https://github.com/uberblick-ai/wireframe-md">wireframe</a></li>
  </ul></div>
  <div><h3>Learn</h3><ul>
    <li><a href="/docs/install">Docs</a></li>
    <li><a href="/guides">Guides</a></li>
    <li><a href="/blog">Blog</a></li>
    <li><a href="/docs/faq">FAQ</a></li>
    <li><a href="/compare">Compare</a></li>
  </ul></div>
  <div><h3>GitHub</h3><ul>
    <li><a href="https://github.com/uberblick-ai/uberblick-2">Source</a></li>
    <li><a href="https://github.com/uberblick-ai/uberblick-2/blob/main/SECURITY.md">Security</a></li>
    <li><a href="https://github.com/uberblick-ai/uberblick-2/blob/main/CHANGELOG.md">Changelog</a></li>
    <li><a href="https://github.com/uberblick-ai/uberblick-2/blob/main/LICENSE">MIT license</a></li>
  </ul></div>
</footer>
<div class="toast" role="status" aria-live="polite"></div>
<script>
const toast = document.querySelector('.toast');
const copied = async (text, fallback) => {{
  try {{ await navigator.clipboard.writeText(text); toast.textContent = 'Copied'; }}
  catch {{ const r = document.createRange(); r.selectNodeContents(fallback); getSelection().removeAllRanges(); getSelection().addRange(r); toast.textContent = 'Select and copy'; }}
  toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 1400);
}};
for (const b of document.querySelectorAll('[data-copy]')) b.addEventListener('click', () => copied(b.getAttribute('data-copy'), b.closest('.block, .tabs').querySelector('pre')));
for (const b of document.querySelectorAll('.copy:not([data-copy])')) b.addEventListener('click', () => {{ const code = b.parentNode.querySelector('code'); copied(code.textContent, code); }});
for (const box of document.querySelectorAll('.tabs')) {{
  const tabs = box.querySelectorAll('[role="tab"]');
  for (const tab of tabs) tab.addEventListener('click', () => {{
    for (const t of tabs) {{ const on = t === tab; t.setAttribute('aria-selected', on); document.getElementById(t.getAttribute('aria-controls')).hidden = !on; }}
  }});
}}
(() => {{
  const side = document.querySelector('details.side'), wide = matchMedia('(min-width: 900px)');
  if (!side) return;
  const sync = () => {{ if (wide.matches) side.open = true; }};
  sync(); wide.addEventListener('change', sync);
}})();
</script>
</body>
</html>
"""

# The landing page links the legacy Rails app's sign-in from the top bar while
# that app still runs behind uberblick.ai (worker/index.js passes /sign-in to
# it). Remove this with the app.
LEGACY_LOGIN = '    <a class="legacy" href="/sign-in">Legacy login</a>\n'

ABOUT = """    <section class="blk about" id="about">
      <h2>Who builds this.</h2>
      <p>Uberblick, ub-agents and the small libraries beside them, such as wireframe and ablauf, are made by a team in Berlin that likes to find out how far AI engineering can go. What holds up in our own work becomes a framework and a few products that run on GitHub alone, so a team no longer needs Notion, Linear or Jira beside it. Take them as a starting point for your own variant. <a href="/docs/motivation">Why each of them exists</a>.</p>
      <div class="cols">
        <div><h3>Docs</h3><ul><li><a href="/docs/install">Install</a></li><li><a href="/docs/workspaces">Workspaces</a></li><li><a href="/docs/documents">Documents</a></li><li><a href="/docs/hub">Run a hub</a></li><li><a href="/docs/cli">CLI reference</a></li><li><a href="/docs/faq">FAQ</a></li></ul></div>
        <div><h3>Agents</h3><ul><li><a href="/docs/agents">Agents over MCP</a></li><li><a href="/docs/guidance">Guidance pages</a></li><li><a href="/docs/decisions">Decision records</a></li><li><a href="https://agents.uberblick.ai">ub-agents</a></li><li><a href="https://skills.uberblick.ai">Skills</a></li></ul></div>
        <div><h3>Project</h3><ul><li><a href="/blog">Blog</a></li><li><a href="https://github.com/uberblick-ai/uberblick-2/blob/main/CHANGELOG.md">Changelog</a></li><li><a href="/guides">Guides</a></li><li><a href="/compare">Compare</a></li><li><a href="https://github.com/uberblick-ai/uberblick-2">GitHub</a></li><li><a href="https://github.com/uberblick-ai/uberblick-2/blob/main/SECURITY.md">Security</a></li></ul></div>
      </div>
    </section>
"""

ASIDE = """  <details class="side" open>
    <summary>{side_title}</summary>
    <div class="side-in">
{side}    </div>
  </details>
"""

# Each section has its own sidebar and sees nothing else: docs pages the docs tree, guides the
# guides, blog pages the posts. The landing page, Compare and Not found have none.
DOCS = [
    ('Get started', '/docs/motivation', [('/docs/motivation', 'Motivation'), ('/docs/install', 'Install'), ('/docs/workspaces', 'Workspaces'), ('/docs/hub', 'Run a hub')]),
    ('Core concepts', '/docs/documents', [('/docs/documents', 'Documents'), ('/docs/decisions', 'Decision records'), ('/docs/guidance', 'Guidance pages'), ('/docs/agents', 'Agents over MCP')]),
    ('CLI reference', '/docs/cli', [('/docs/cli/auth', 'ub auth'), ('/docs/cli/workspace', 'ub workspace'), ('/docs/cli/mcp', 'ub mcp'), ('/docs/cli/open', 'ub open'), ('/docs/cli/status', 'ub status'), ('/docs/cli/doctor', 'ub doctor'), ('/docs/cli/data', 'ub data'), ('/docs/cli/update', 'ub update'), ('/docs/cli/uninstall', 'ub uninstall'), ('/docs/cli/binding', 'Project binding')]),
    ('Custom Markdown', '/docs/markdown', [('/docs/markdown', 'Markdown baseline'), ('/docs/markdown/extensions', 'Markdown extensions'), ('/docs/markdown/diagrams', 'Diagrams'), ('/docs/markdown/wireframes', 'Wireframes'), ('/docs/markdown/charts', 'Charts'), ('/docs/markdown/embeds', 'Embeds')]),
    (None, None, [('/docs/faq', 'FAQ'), (CHANGELOG_URL, 'Changelog')]),
]
GUIDES = [
    (None, None, [('/guides', 'All guides')]),
    ('Start', None, [('/guides/first-workspace', 'Your first workspace'), ('/guides/hub', 'Set up a hub')]),
    ('Jobs', None, [('/guides/product-intent', 'Product intent'), ('/guides/decisions', 'Decisions that stay decided'), ('/guides/reports', 'Reports with the numbers'), ('/guides/flows', 'Flows and screens as text')]),
]
KINDS = {'release': 'Release', 'design note': 'Design note', 'building note': 'Building note'}


def fetch(url, accept=None):
    """Text from a public GitHub URL, or None when the network is not there."""
    headers = {'User-Agent': 'uberblick.ai build'}
    if accept:
        headers['Accept'] = accept
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as r:
            return r.read().decode()
    except (OSError, ValueError):
        return None


def version():
    try:
        tag = subprocess.run(['git', 'describe', '--tags', '--abbrev=0', '--match', 'v[0-9]*'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        # A shallow checkout has no tags: ask GitHub for them and take the highest client version.
        body = fetch(TAGS)
        found = [t['name'] for t in json.loads(body) if re.fullmatch(r'v\d+\.\d+\.\d+', t.get('name', ''))] if body else []
        if not found:
            return ''
        tag = max(found, key=lambda t: tuple(int(n) for n in t[1:].split('.')))
    return f'<a class="count" href="{REPO}/releases/tag/{tag}">{tag}</a>\n  '


def changelog():
    """The changelog text: the repository's file beside the site, else fetched from GitHub."""
    if CHANGELOG.is_file():
        return CHANGELOG.read_text()
    # raw.githubusercontent.com first; the contents API serves the same file where only api.github.com is reachable.
    text = fetch(RAW_CHANGELOG) or fetch(API_CHANGELOG, 'application/vnd.github.raw+json')
    if text is None:
        sys.exit(f'CHANGELOG.md: neither {CHANGELOG} nor {RAW_CHANGELOG} nor {API_CHANGELOG} is readable')
    return text


def inline(text):
    """Escaped HTML with Markdown code spans, links and issue numbers resolved."""
    out = html.escape(' '.join(text.split()), quote=False)
    out = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', out)
    out = re.sub(r'`([^`]+)`', r'<code>\1</code>', out)
    return re.sub(r'(?<![\w/])#(\d+)\b', rf'<a href="{REPO}/issues/\1">#\1</a>', out)


def releases(text):
    found = re.findall(r'^## (v\S+) — (\d{4}-\d{2}-\d{2})\n\n(.+?)\n\n', text, re.M | re.S)
    if len(found) < 5:
        sys.exit(f'CHANGELOG.md: expected five "## vX.Y.Z — YYYY-MM-DD" sections with a summary paragraph, found {len(found)}')
    return found


def recent(text, posts, count=5):
    """Releases and posts, newest first; a release post (its title starts with the tag) joins its release's row."""
    live = [p for p in posts if not p['draft']]
    items = []
    for tag, day, summary in releases(text)[:count]:
        more = next((p for p in live if p['kind'] == 'release' and p['title'].startswith(tag)), None)
        items.append((day, 'Release', f'<a href="{REPO}/releases/tag/{tag}">{tag}</a>: {inline(summary)}' + (f' <a href="{more["path"]}">Read the post</a>' if more else '')))
        live = [p for p in live if p is not more]
    items += [(p['date'], KINDS[p['kind']], f'<a href="{p["path"]}">{html.escape(p["title"], quote=False)}</a>') for p in live]
    items.sort(key=lambda i: i[0], reverse=True)
    return '\n  '.join(f'<li><time>{day}</time><span class="tag">{kind}</span><span>{text}</span></li>' for day, kind, text in items[:count])


def meta(head, name):
    m = re.search(rf'<meta name="{name}" content="([^"]*)">', head)
    return html.unescape(m[1]) if m else ''


def post(page, head, body):
    """A blog post's record from its page: path, date, author, kind, title, summary and body."""
    name = page.relative_to(ROOT).as_posix()
    path, _ = route(page)
    title = html.unescape(re.search(r'<title>(.*?)(?: · [^<]*)?</title>', head)[1])
    day, author, kind = meta(head, 'date'), meta(head, 'author'), meta(head, 'kind')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day) or not author or kind not in KINDS:
        sys.exit(f'{name}: a post needs <meta name="date"> (YYYY-MM-DD), <meta name="author"> and <meta name="kind"> (one of {", ".join(KINDS)})')
    if not path.startswith(f'/blog/{day[:4]}/'):
        sys.exit(f'{name}: a post from {day} lives in pages/blog/{day[:4]}/')
    return {'path': path, 'date': day, 'author': author, 'kind': kind, 'title': title, 'summary': meta(head, 'description'),
            'draft': meta(head, 'draft') != '', 'body': body}


def post_list(posts):
    items = []
    for p in posts:
        if p['draft']:
            continue
        items.append(f'<li><time>{p["date"]}</time><span class="tag">{KINDS[p["kind"]]}</span><span><a href="{p["path"]}">{html.escape(p["title"], quote=False)}</a><small>{html.escape(p["summary"], quote=False)} · {html.escape(p["author"], quote=False)}</small></span></li>')
    return '\n  '.join(items)


def feed(posts):
    entries = []
    for p in posts:
        if p['draft']:
            continue
        content = re.sub(r'(href|src)="/', rf'\1="{SITE}/', p['body'])
        entries.append(f"""<entry>
<title>{html.escape(p['title'])}</title>
<link href="{SITE}{p['path']}"/>
<id>{SITE}{p['path']}</id>
<updated>{p['date']}T00:00:00Z</updated>
<author><name>{html.escape(p['author'])}</name></author>
<category term="{html.escape(p['kind'])}"/>
<summary>{html.escape(p['summary'])}</summary>
<content type="html">{html.escape(content)}</content>
</entry>""")
    newest = posts[0]['date'] if posts else date.today().isoformat()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Uberblick blog</title>
<subtitle>Releases, design notes and notes on how Uberblick builds itself.</subtitle>
<link href="{SITE}/blog"/>
<link rel="self" href="{SITE}/blog/feed.xml"/>
<id>{SITE}/blog</id>
<updated>{newest}T00:00:00Z</updated>
{chr(10).join(entries)}
</feed>
"""


def section(path, posts=()):
    """The sidebar title and groups for a page, or None for a page without a sidebar."""
    if path.startswith('/docs/'):
        return 'Docs', DOCS
    if path == '/guides' or path.startswith('/guides/'):
        return 'Guides', GUIDES
    if path == '/blog' or path.startswith('/blog/'):
        return 'Posts', [(None, None, [('/blog', 'All posts')]), ('Posts', None, [(p['path'], p['title']) for p in posts if not p['draft']]), (None, None, [('/blog/feed.xml', 'Atom feed')])]
    return None


def sidebar(path, groups):
    """Groups of links. A group with a page of its own is a link that stays folded until the
    reader is inside it, like a docs tree that opens where you are; its page is not repeated
    among the children when it only introduces them. A group without a page is a plain heading
    and always open. A link may carry sub-pages as a third item; they are listed only while the
    reader is on the topic or one of its sub-pages."""
    def link(href, label):
        on = ' class="on"' if href == path else ''
        return f'<a{on} href="{href}">{label}</a>'
    def item(entry):
        href, label, *rest = entry
        subs = rest[0] if rest else []
        inside = subs and (path == href or any(path == h for h, _ in subs))
        on = ' class="on"' if path == href and not inside else (' class="in"' if inside else '')
        html = f'<a{on} href="{href}">{label}</a>'
        if inside:
            html += '<ul class="sub">' + ''.join(f'<li>{link(h, l)}</li>' for h, l in subs) + '</ul>'
        return f'<li>{html}</li>'
    def covers(entry):
        href, _, *rest = entry
        return path == href or any(path == h for h, _ in (rest[0] if rest else []))
    def group(title, href, links):
        if href is None:
            return f'<li><span class="grp">{title}</span><ul>' + ''.join(item(e) for e in links) + '</ul></li>'
        inside = path == href or any(covers(e) for e in links)
        on = ' on' if path == href and not any(e[0] == href for e in links) else ''
        html = f'<a class="grp{on}" href="{href}">{title}</a>'
        if inside:
            html += '<ul>' + ''.join(item(e) for e in links) + '</ul>'
        return f'<li>{html}</li>'
    out, groups_html = [], []
    for title, href, links in groups:
        if title is None:
            if groups_html:
                out.append('      <ul>' + ''.join(groups_html) + '</ul>\n')
                groups_html = []
            out.append('      <ul class="plain">' + ''.join(item(e) for e in links) + '</ul>\n')
        else:
            groups_html.append(group(title, href, links))
    if groups_html:
        out.append('      <ul>' + ''.join(groups_html) + '</ul>\n')
    return ''.join(out)


def split(text, name):
    m = re.match(r'\s*<head>\n(.*?)</head>\n(.*)$', text, re.S)
    if not m:
        sys.exit(f'{name}: a page starts with a <head> block')
    head, body = m.groups()
    if '<title>' not in head:
        sys.exit(f'{name}: the <head> block has no <title>')
    return head, body.strip('\n')


def route(page):
    rel = page.relative_to(PAGES).with_suffix('')
    if rel.name == '404':
        return '/404', OUT / '404.html'
    if rel.name == 'index':
        rel = rel.parent
    path = '/' + rel.as_posix().strip('.')
    path = path.rstrip('/') or '/'
    return path, OUT / rel / 'index.html'


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    built, hrefs, tag, log = set(), set(), version(), changelog()
    pages = sorted(PAGES.rglob('*.html'))
    posts = sorted((post(p, *split(p.read_text(), p.relative_to(ROOT).as_posix())) for p in pages if re.fullmatch(r'\d{4}', p.parent.name) and p.parent.parent == PAGES / 'blog'),
                   key=lambda p: (p['date'], p['path']), reverse=True)
    for page in pages:
        name = page.relative_to(ROOT).as_posix()
        head, body = split(page.read_text(), name)
        if RECENT in body:
            body = body.replace(RECENT, recent(log, posts))
        if POSTS in body:
            body = body.replace(POSTS, post_list(posts))
        path, target = route(page)
        blog = path == '/blog' or path.startswith('/blog/')
        noindex = NOINDEX or ('<meta name="robots" content="noindex">\n' if blog and meta(head, 'draft') else '')
        head = re.sub(r'<meta name="(date|author|kind|draft)" content="[^"]*">\n', '', head)
        if blog:
            head += '<link rel="alternate" type="application/atom+xml" title="Uberblick blog" href="/blog/feed.xml">\n'
        canonical = '' if path == '/404' else f'<link rel="canonical" href="{SITE}{path}">\n'
        target.parent.mkdir(parents=True, exist_ok=True)
        found = section(path, posts)
        side = sidebar(path, found[1]) if found else ''
        aside = ASIDE.format(side_title=found[0], side=side) if found else ''
        about = ABOUT if path == '/' else ''
        legacy = LEGACY_LOGIN if path == '/' else ''
        target.write_text(SKELETON.format(head=head, canonical=canonical, noindex=noindex, version=tag, solo='' if found else ' solo', aside=aside, about=about, legacy=legacy, body=body))
        built.add(path)
        hrefs |= {h.split('#')[0] for h in re.findall(r'href="(/[^"]*)"', body + side + about)}
    (OUT / 'blog').mkdir(parents=True, exist_ok=True)
    (OUT / 'blog' / 'feed.xml').write_text(feed(posts))
    built.add('/blog/feed.xml')
    missing = sorted(h for h in hrefs if h and h not in built and not (OUT / h.lstrip('/')).is_file())
    print(f'built {len(built)} pages into {OUT.relative_to(ROOT.parent)}')
    if missing:
        print('linked but not written yet: ' + ', '.join(missing))


if __name__ == '__main__':
    main()
