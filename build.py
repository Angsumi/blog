"""ANGSUMI blog (blog.angsumi.online): posts/*.md -> dist/ (pages, index, RSS, sitemap, posts.json).

Front-matter between --- lines: title, description, date, updated (optional), cluster, service, guide, guide_title,
faq as `  - q:` / `    a:` pairs. The first paragraph is the 40-60-word direct answer.
Markdown subset: ## / ### headings, paragraphs, - and 1. lists, | tables |, **bold**, `code`, [links](url).
Standard library only:  python3 build.py
"""
from datetime import date
from html import escape, unescape
from pathlib import Path
import json, re, shutil

ROOT = Path(__file__).parent
OUT = ROOT / 'dist'
BLOG = 'https://blog.angsumi.online/'
MAIN = 'https://angsumi.online/'
PERSON = {'@id': MAIN + '#person'}
ORG = {'@type': 'Organization', '@id': MAIN + '#organization', 'name': 'ANGSUMI', 'url': MAIN, 'logo': MAIN + 'logo.png'}


def front_matter(raw):
    _, head, body = raw.split('---\n', 2)
    meta, faq = {}, []
    for line in head.splitlines():
        if line.startswith('  - q:'): faq.append([line[6:].strip(), ''])
        elif line.startswith('    a:'): faq[-1][1] = line[6:].strip()
        elif ':' in line and not line.startswith(' '):
            k, v = line.split(':', 1); meta[k.strip()] = v.strip()
    meta['faq'] = faq
    return meta, body.strip()


def inline(s):
    s = escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{m[2]}">{m[1]}</a>', s)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def render(md):
    out = []
    for block in re.split(r'\n\s*\n', md):
        lines = block.strip().splitlines(); first = lines[0]
        if first.startswith('### '): out.append(f'<h3 id="{slug(first[4:])}">{inline(first[4:])}</h3>')
        elif first.startswith('## '): out.append(f'<h2 id="{slug(first[3:])}">{inline(first[3:])}</h2>')
        elif first.startswith('- '): out.append('<ul>' + ''.join(f'<li>{inline(l[2:])}</li>' for l in lines) + '</ul>')
        elif re.match(r'\d+\. ', first): out.append('<ol>' + ''.join(f'<li>{inline(l.split(". ", 1)[1])}</li>' for l in lines) + '</ol>')
        elif first.startswith('|'):
            rows = [[c.strip() for c in l.strip('|').split('|')] for l in lines if not re.match(r'^\|[\s:|-]+\|$', l)]
            head = ''.join(f'<th scope="col">{inline(c)}</th>' for c in rows[0])
            body = ''.join('<tr>' + f'<th scope="row">{inline(r[0])}</th>' + ''.join(f'<td>{inline(c)}</td>' for c in r[1:]) + '</tr>' for r in rows[1:])
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        else: out.append('<p>' + inline(' '.join(lines)) + '</p>')
    return '\n'.join(out)


def text(fragment):
    return ' '.join(unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def human(d):
    return date.fromisoformat(d).strftime('%-d %B %Y')


def page(path, title, description, body, graph, og='website', head=''):
    url = BLOG + (path + '/' if path else '')
    schema = json.dumps({'@context': 'https://schema.org', '@graph': [ORG, {'@type': 'WebSite', '@id': BLOG + '#website', 'name': 'ANGSUMI blog', 'url': BLOG, 'publisher': {'@id': ORG['@id']}}] + graph}, ensure_ascii=False).replace('</', '<\\/')
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | ANGSUMI blog</title><meta name="description" content="{escape(description, quote=True)}"><link rel="canonical" href="{url}"><meta property="og:title" content="{escape(title, quote=True)}"><meta property="og:description" content="{escape(description, quote=True)}"><meta property="og:type" content="{og}"><meta property="og:url" content="{url}"><meta property="og:image" content="{MAIN}og-icon.png">{head}<link rel="icon" href="{MAIN}favicon.ico"><link rel="alternate" type="application/rss+xml" title="ANGSUMI blog" href="{BLOG}feed.xml"><link rel="stylesheet" href="{MAIN}assets/original-design.css"><link rel="stylesheet" href="{MAIN}assets/growth.css"><script type="application/ld+json">{schema}</script></head><body class="growth"><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="{MAIN}">ANGSUMI</a><nav aria-label="Main navigation"><a href="{MAIN}services/">Services</a><a href="{MAIN}portfolio/">Work &amp; methods</a><a href="{BLOG}">Blog</a><a href="{MAIN}resources/">Resources</a><a href="{MAIN}training/">Learn</a><a href="{MAIN}inquiry/">Discuss my dataset ↗</a></nav></header><main id="main">{body}</main><footer><p><strong>ANGSUMI — Research &amp; Data Analysis</strong><br>Research | Data | Impact</p><p><a href="{MAIN}privacy-policy/">Privacy</a> · <a href="{MAIN}terms/">Terms</a> · <a href="https://wa.me/917896595109">WhatsApp</a> · <a href="{MAIN}about/">About ANGSUMI</a></p></footer></body></html>'''
    target = OUT / path / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)
    return url


def load():
    posts = []
    for f in sorted((ROOT / 'posts').glob('*.md')):
        meta, body = front_matter(f.read_text())
        answer, rest = body.split('\n\n', 1)
        meta.update(slug=f.stem, answer=' '.join(answer.split()), body=rest, updated=meta.get('updated', meta['date']),
                    citations=sorted(set(re.findall(r'\]\((https?://[^)\s]+)\)', body))))
        words = len(meta['answer'].split())
        assert 40 <= words <= 60, f'{f.name}: direct answer must be 40-60 words, has {words}'
        posts.append(meta)
    return sorted(posts, key=lambda p: p['date'], reverse=True)


def build():
    if OUT.exists(): shutil.rmtree(OUT)
    posts, urls = load(), []
    for p in posts:
        url = BLOG + p['slug'] + '/'
        byline = (f'<p class="byline">By <a href="{MAIN}about/">Angsuman Das</a> · Published <time datetime="{p["date"]}">{human(p["date"])}</time>'
                  + (f' · Updated <time datetime="{p["updated"]}">{human(p["updated"])}</time>' if p['updated'] != p['date'] else '') + '</p>')
        faq = ''.join(f'<details><summary>{inline(q)}</summary><p>{inline(a)}</p></details>' for q, a in p['faq'])
        body = (f'<article class="post"><div class="eyebrow"><a href="{BLOG}">Blog</a> · {escape(p["cluster"])}</div><h1>{escape(p["title"])}</h1>{byline}'
                f'<p class="intro answer">{inline(p["answer"])}</p>{render(p["body"])}' + (f'<section><h2>Common questions</h2>{faq}</section>' if faq else '') +
                f'<section class="notice"><h2>Plan your analysis</h2><p>Read the <a href="{MAIN}resources/{p["guide"]}/">{escape(p["guide_title"])}</a> guide, or see the matching <a href="{MAIN}services/{p["service"]}/">analysis service</a>.</p>'
                f'<a class="btn" href="{MAIN}inquiry/?category=research&amp;service={p["service"]}&amp;campaign=blog-{p["slug"]}">Discuss my dataset →</a></section></article>')
        webpage = {'@type': ['WebPage', 'FAQPage'] if p['faq'] else 'WebPage', '@id': url + '#webpage', 'url': url, 'name': p['title'], 'isPartOf': {'@id': BLOG + '#website'},
                   'breadcrumb': {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'ANGSUMI', 'item': MAIN}, {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': BLOG}, {'@type': 'ListItem', 'position': 3, 'name': p['title'], 'item': url}]}}
        if p['faq']: webpage['mainEntity'] = [{'@type': 'Question', 'name': text(inline(q)), 'acceptedAnswer': {'@type': 'Answer', 'text': text(inline(a))}} for q, a in p['faq']]
        article = {'@type': 'BlogPosting', '@id': url + '#article', 'headline': p['title'], 'description': p['description'], 'datePublished': p['date'], 'dateModified': p['updated'],
                   'author': {'@type': 'Person', '@id': PERSON['@id'], 'name': 'Angsuman Das', 'url': MAIN + 'cv/'}, 'publisher': {'@id': ORG['@id']},
                   'mainEntityOfPage': {'@id': url + '#webpage'}, 'image': MAIN + 'og-icon.png', 'articleSection': p['cluster'], 'inLanguage': 'en',
                   'about': {'@id': MAIN + 'services/' + p['service'] + '/#service'}, 'citation': p['citations']}
        meta = f'<meta property="article:published_time" content="{p["date"]}"><meta property="article:modified_time" content="{p["updated"]}"><meta name="author" content="Angsuman Das">'
        urls.append((page(p['slug'], p['title'], p['description'], body, [webpage, article], 'article', meta), p['updated']))
    cards = ''.join(f'<article class="card"><span class="tag">{escape(p["cluster"])}</span><h2 style="font-size:28px"><a href="{BLOG}{p["slug"]}/">{escape(p["title"])}</a></h2><p>{escape(p["description"])}</p><p class="help"><time datetime="{p["date"]}">{human(p["date"])}</time></p></article>' for p in posts)
    index_url = page('', 'Bioinformatics analysis blog', 'Practical, source-cited explanations of RNA-seq, metagenomics and research data analysis decisions.',
                     f'<div class="eyebrow">Blog</div><h1>Analysis decisions, explained.</h1><p class="intro">Practical explanations of bioinformatics methods and choices, with links to the primary documentation behind each claim.</p><div class="grid">{cards}</div>',
                     [{'@type': 'Blog', '@id': BLOG + '#blog', 'name': 'ANGSUMI blog', 'url': BLOG, 'publisher': {'@id': ORG['@id']}}])
    urls.insert(0, (index_url, max((p['updated'] for p in posts), default=None)))
    items = ''.join(f'<item><title>{escape(p["title"])}</title><link>{BLOG}{p["slug"]}/</link><guid>{BLOG}{p["slug"]}/</guid><pubDate>{date.fromisoformat(p["date"]):%a, %d %b %Y} 00:00:00 +0000</pubDate><description>{escape(p["description"])}</description></item>' for p in posts)
    (OUT / 'feed.xml').write_text(f'<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0"><channel><title>ANGSUMI blog</title><link>{BLOG}</link><description>Bioinformatics and research data analysis, explained.</description><language>en</language>{items}</channel></rss>\n')
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{u}</loc>' + (f'<lastmod>{m}</lastmod>' if m else '') + '</url>' for u, m in urls) + '</urlset>\n')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BLOG}sitemap.xml\n')
    # Consumed by angsumi.online at build time (homepage "From the blog", service cluster links, llms.txt, /blog/ stubs).
    (OUT / 'posts.json').write_text(json.dumps([{k: p[k] for k in ('slug', 'title', 'description', 'date', 'updated', 'cluster', 'service', 'guide')} | {'url': BLOG + p['slug'] + '/'} for p in posts], indent=1) + '\n')
    (OUT / 'CNAME').write_text('blog.angsumi.online\n')
    (OUT / '404.html').write_text((OUT / 'index.html').read_text().replace('<head>', '<head><meta name="robots" content="noindex">', 1))
    print(f'dist/: {len(posts)} posts, index, feed, sitemap, posts.json')


if __name__ == '__main__':
    build()
