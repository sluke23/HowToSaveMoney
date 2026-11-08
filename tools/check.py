#!/usr/bin/env python3
"""Check local document links, table shape, source integrity and generated site."""
import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])


def anchors(path):
    text = path.read_text(encoding='utf-8')
    parser = HTMLLinks()
    parser.feed(text)
    found = set(parser.ids)
    if path.suffix == '.md':
        counts = {}
        for heading in re.findall(r'^#{1,6} (.+)$', text, re.M):
            slug = ''.join(c for c in heading.lower() if c in '-_' or not unicodedata.category(c).startswith(('P', 'S'))).replace(' ', '-')
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            found.add(slug + (f'-{count}' if count else ''))
    return found


def main():
    errors = []
    files = sorted(ROOT.glob('*.md')) + sorted(ROOT.glob('book/*.md')) + sorted(ROOT.glob('docs/*.md')) + sorted((ROOT / 'skills').rglob('*.md')) + sorted((ROOT / 'tools').rglob('*.md')) + [ROOT / 'index.html']
    link_count = 0
    table_count = 0
    for path in files:
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            parser = HTMLLinks()
            parser.feed(text)
            links = parser.links
            if len(parser.ids) != len(set(parser.ids)):
                errors.append('index.html：出现重复锚点')
        else:
            links = re.findall(r'\[[^\]\n]*\]\(([^\n]+?)\)', text)
            # This repository uses unescaped pipes only as cell separators.
            previous = None
            for line in text.splitlines():
                if line.startswith('| '):
                    cells = len(re.split(r'(?<!\\)\|', line)) - 2
                    if previous is not None and cells != previous:
                        errors.append(f'{path.name}：表格列数不一致：{line}')
                    previous = cells
                    if re.fullmatch(r'\|(?:\s*:?-+:?\s*\|)+', line):
                        table_count += 1
                else:
                    previous = None
        for link in links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            link_count += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.exists():
                errors.append(f'{path.name}：目标不存在：{link}')
            elif parts.fragment and target.suffix in ('.md', '.html') and unquote(parts.fragment) not in anchors(target):
                errors.append(f'{path.name}：锚点不存在：{link}')
    manifest = json.loads((ROOT / 'docs/内容映射.json').read_text(encoding='utf-8'))
    # The source PDF is historical provenance, not a checkout/build dependency.
    source_name = manifest.get('source_pdf_name', '')
    if not source_name or '/' in source_name or '\\' in source_name or not source_name.endswith('.pdf'):
        errors.append('source_pdf_name 必须是历史来源 PDF 的文件名，不是文件路径。')
    if not re.fullmatch(r'[0-9a-f]{64}', manifest.get('source_sha256', '')):
        errors.append('历史来源 SHA-256 格式不正确。')
    if not manifest.get('source_note'):
        errors.append('缺少历史来源说明 source_note。')
    for doc in manifest['documents']:
        text = (ROOT / doc['path']).read_text(encoding='utf-8')
        count = len(re.findall(r'^## \d+\.\d+ ', text, re.M))
        if count != doc['sections']:
            errors.append(f'{doc["path"]}：编号小节数量与内容映射不一致')
    from build_site import build
    if (ROOT / 'index.html').read_text(encoding='utf-8') != build():
        errors.append('阅读页已过期，请运行 python3 tools/build_site.py')
    from build_skill import bundle, SKILL
    expected = bundle()
    stale = [name for name, text in expected.items() if not (SKILL / name).is_file() or (SKILL / name).read_text(encoding='utf-8') != text]
    extra = [str(p.relative_to(SKILL)) for p in (SKILL / 'references').rglob('*') if p.is_file() and p.relative_to(SKILL).as_posix() not in expected]
    if stale or extra:
        errors.append('Skill 资料已过期，请运行 python3 tools/build_skill.py：' + ', '.join(stale + extra))
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'检查通过：{len(files)} 份文档、{link_count} 个本地链接、{table_count} 张表格；历史来源元数据格式正确，章节、阅读页与 Skill 一致。')
    print('此检查不验证外部网址可用性或政策有效性。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
