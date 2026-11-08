"""Shared Markdown source, anchors and link rewriting for reading exports."""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

import markdown

ROOT = Path(__file__).resolve().parents[2]
TITLE = '一线城市省钱指南'
LANGUAGE = 'zh-CN'


def xml(text):
    return html.escape(str(text), quote=True)


def plain(element):
    return ''.join(element.itertext())


def content(source):
    """Drop repository navigation and duplicate per-chapter TOCs, keep source notes."""
    text = source
    if '## 本章目录' in text:
        before, rest = text.split('## 本章目录', 1)
        text = before + rest.split('\n---\n', 1)[1]
    if '\n---\n' in text:
        text = text.rsplit('\n---\n', 1)[0]
    text = re.sub(r'\[查看原文\]\([^\n]*?\.pdf#page=\d+\)', '原始 PDF 页码见本段；此导出版不附原始 PDF', text)
    text = re.sub(r'^\[返回首页\].*$', '', text, flags=re.M)
    return text.strip()


def load_book():
    manifest = json.loads((ROOT / 'docs/内容映射.json').read_text(encoding='utf-8'))
    source_paths = [doc['path'] for doc in manifest['documents']]
    source_paths += ['docs/待核实清单.md', 'docs/版权与使用说明.md']
    pages = [{'path': 'README.md', 'id': 'front', 'title': '版本与阅读说明',
              'md': f'''# 版本与阅读说明

《{TITLE}》

一份给普通打工人的成本结构说明书

作者：{manifest['author']}

北京 · 上海 · 广州 · 深圳

原文版本：{manifest['source_version']}。

此阅读版从项目当前 Markdown 生成，包含使用说明、17 章、3 个附录、待核实清单和版权说明。原文政策基线不代表导出当天仍然有效。正文里的疑点请结合书末“待核实清单”阅读；官方入口不等于当前资格或金额已获核实。

许可：一般正文 CC BY-NC-SA 4.0；指定工具内容 CC BY 4.0。完整适用范围见本书“许可范围”。

这些文件是重新排版的阅读导出版，原始 PDF 已不随仓库提供，历史来源信息保留在内容映射中。版权说明中对原排版字体的描述仅指原始 PDF；本导出版的字体随格式而定，PDF 实际使用的嵌入字体见构建清单。'''}]
    for i, path in enumerate(source_paths):
        text = content((ROOT / path).read_text(encoding='utf-8'))
        title = re.search(r'^# (.+)$', text, re.M).group(1)
        pages.append({'path': path, 'id': f'doc-{i:02d}', 'title': title, 'md': text})
    license_text = (ROOT / 'LICENSE').read_text(encoding='utf-8')
    pages.append({'path': 'LICENSE', 'id': 'license', 'title': '许可范围',
                  'md': '# 许可范围\n\n' + '\n\n'.join(license_text.splitlines())})
    path_map = {page['path']: page for page in pages}
    for page in pages:
        fragment = markdown.markdown(page['md'], extensions=['tables', 'sane_lists'], output_format='xhtml')
        # XML knows the five built-in entities, so turn other HTML entities into numeric references.
        fragment = re.sub(r'&([a-zA-Z][a-zA-Z0-9]+);', lambda m: m[0] if m[1] in ['amp', 'lt', 'gt', 'quot', 'apos'] else ''.join(f'&#{ord(c)};' for c in html.unescape(m[0])), fragment)
        tree = ET.fromstring('<div>' + fragment + '</div>')
        heading_count = 0
        for element in tree.iter():
            if re.fullmatch(r'h[1-6]', element.tag):
                heading_count += 1
                element.set('id', page['id'] if heading_count == 1 else f'{page["id"]}-h{heading_count}')
        # Put section anchors on visible headings so PDF destinations survive layout.
        pending = None
        for element in list(tree):
            anchor = element if element.tag == 'a' else element.find('a') if element.tag == 'p' else None
            if anchor is not None and anchor.get('id') and not plain(element).strip():
                pending = anchor.get('id')
                tree.remove(element)
            elif pending and re.fullmatch(r'h[1-6]', element.tag):
                element.set('id', pending)
                pending = None
        page['tree'] = tree
        page['file'] = page['id'] + '.xhtml'
    # Resolve all local links to an explicit book target or remove navigation to files not included.
    for page in pages:
        for a in page['tree'].iter('a'):
            href = a.get('href')
            if href is None:
                continue
            parts = urlsplit(href)
            if parts.scheme or parts.netloc:
                continue
            target_path = ((ROOT / page['path']).parent / unquote(parts.path)).resolve().relative_to(ROOT).as_posix() if parts.path else page['path']
            target = path_map.get(target_path)
            if not target:
                a.attrib.pop('href', None)
                continue
            anchor = unquote(parts.fragment) if parts.fragment else target['id']
            ids = {el.get('id') for el in target['tree'].iter()}
            if anchor not in ids:
                anchor = target['id']
            a.set('href', target['file'] + '#' + anchor)
    build_inputs = ['tools/export_book.py', 'tools/requirements-export.txt', 'tools/requirements.txt']
    build_inputs += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'tools/reading').glob('*.py'))]
    build_inputs += ['tools/reading/style.css']
    return manifest, pages, source_paths + ['LICENSE', 'docs/内容映射.json'] + build_inputs


def html_body(page, single=False):
    text = ''.join(ET.tostring(el, encoding='unicode', method='xml') for el in page['tree'])
    if single:
        text = re.sub(r'href="[^"#]+\.xhtml#([^"]+)"', r'href="#\1"', text)
    return text


def source_hashes(paths):
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
