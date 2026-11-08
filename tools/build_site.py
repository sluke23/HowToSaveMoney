#!/usr/bin/env python3
"""Build a self-contained reading page from the maintained Markdown sources."""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown

ROOT = Path(__file__).resolve().parents[1]


def build():
    manifest = json.loads((ROOT / 'docs/内容映射.json').read_text(encoding='utf-8'))
    docs = manifest['documents']
    ids = {d['path']: f'doc-{i:02d}' for i, d in enumerate(docs)}
    toc, articles, options = [], [], []
    for i, doc in enumerate(docs):
        path = doc['path']
        text = (ROOT / path).read_text(encoding='utf-8')
        title = doc['title']
        doc_id = ids[path]
        # Per-chapter TOCs precede the first rule. The final rule starts navigation.
        if '## 本章目录' in text:
            body = text.split('\n---\n', 1)[1]
        else:
            body = re.sub(r'^# .+\n+', '', text, count=1)
        body = body.rsplit('\n---\n', 1)[0].strip()
        parts = re.split(r'<a id="(s\d+-\d+)"></a>\s*', body)

        def render(value):
            rendered = markdown.markdown(value, extensions=['tables', 'sane_lists'])

            def rewrite(match):
                href = html.unescape(match[1])
                parsed = urlsplit(href)
                if parsed.scheme or href.startswith('#'):
                    return match[0]
                target = (ROOT / path).parent / unquote(parsed.path)
                relative = target.resolve().relative_to(ROOT).as_posix()
                if relative in ids:
                    dest = '#' + (parsed.fragment or ids[relative])
                else:
                    dest = relative + ('#' + parsed.fragment if parsed.fragment else '')
                return 'href="' + html.escape(dest, quote=True) + '"'

            return re.sub(r'href="([^"]+)"', rewrite, rendered)

        entries = []
        if parts[0].strip():
            entries.append(f'<section class="entry intro" id="{doc_id}-intro">{render(parts[0])}</section>')
        for n in range(1, len(parts), 2):
            entries.append(f'<section class="entry" id="{parts[n]}">{render(parts[n+1])}</section>')
        city = next((c for c in ['北京', '上海', '广州', '深圳'] if re.match(r'第.+章 '+c+'：', title)), '通用')
        articles.append(f'<article id="{doc_id}" data-city="{city}" data-doc="{i}">'
                        f'<header class="chapter-head"><p class="part">{html.escape(doc["part"])}</p>'
                        f'<h2>{html.escape(title)}</h2>'
                        f'<a class="markdown" href="{html.escape(path)}">阅读 Markdown ↗</a></header>'
                        + ''.join(entries) + '</article>')
        toc.append(f'<a href="#{doc_id}">{html.escape(title)}</a>')
        options.append(f'<option value="{i}">{html.escape(title)}</option>')
    template = (ROOT / 'tools/site.html').read_text(encoding='utf-8')
    for key, value in {'TOC': ''.join(toc), 'ARTICLES': '\n'.join(articles),
                       'OPTIONS': ''.join(options)}.items():
        template = template.replace('{{' + key + '}}', value)
    return template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify index.html matches the Markdown sources')
    args = parser.parse_args()
    result = build()
    output = ROOT / 'index.html'
    if args.check:
        if not output.exists() or output.read_text(encoding='utf-8') != result:
            raise SystemExit('index.html 已过期，请运行 python3 tools/build_site.py')
        print('阅读页与 Markdown 一致。')
    else:
        output.write_text(result, encoding='utf-8')
        print('已生成 index.html（可离线打开，无运行时依赖）。')


if __name__ == '__main__':
    main()
