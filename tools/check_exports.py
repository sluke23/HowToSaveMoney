#!/usr/bin/env python3
"""Validate exported artifacts: packaging, internal links, source coverage and PDF geometry."""
import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from reading.book import ROOT, load_book, plain, source_hashes


class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.text = [], [], []
        self.suppressed = 0
        self.external_assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.suppressed += 1
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag in ('script', 'img', 'iframe') and attrs.get('src'):
            self.external_assets.append(attrs['src'])
        if tag == 'link' and attrs.get('href'):
            self.external_assets.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.suppressed -= 1

    def handle_data(self, data):
        if not self.suppressed:
            self.text.append(data)


def norm(text):
    return ''.join(c for c in text if c.isalnum())


def check_links(trees):
    for name, tree in trees.items():
        ids = [e.get('id') for e in tree.iter() if e.get('id')]
        assert len(ids) == len(set(ids)), f'{name}: 重复锚点'
        for a in tree.iter():
            href = a.get('href')
            if not href:
                continue
            parts = urlsplit(href)
            if parts.scheme or parts.netloc:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parts.path))) if parts.path else name
            assert target in trees, f'{name}: 缺少目标 {href}'
            if parts.fragment:
                assert unquote(parts.fragment) in {e.get('id') for e in trees[target].iter()}, f'{name}: 缺少锚点 {href}'


def expected(pages):
    for page in pages:
        for el in page['tree'].iter():
            if el.tag in ('h1', 'h2', 'h3', 'p', 'li', 'td', 'th'):
                text = norm(plain(el))
                if len(text) >= 8:
                    yield page['path'], text


def coverage(actual, pages, label):
    normalized = norm(actual)
    missing = [(path, text[:70]) for path, text in expected(pages) if text not in normalized]
    assert not missing, f'{label}: 内容缺失或顺序中断 {missing[:10]}'


def check_epub(path, manifest, pages):
    with zipfile.ZipFile(path) as z:
        files = z.infolist()
        assert files[0].filename == 'mimetype' and files[0].compress_type == zipfile.ZIP_STORED
        assert z.read('mimetype') == b'application/epub+zip'
        assert z.testzip() is None
        container = ET.fromstring(z.read('META-INF/container.xml'))
        rootfile = next(e for e in container.iter() if e.tag.endswith('rootfile')).get('full-path')
        opf = ET.fromstring(z.read(rootfile))
        ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
        assert opf.get('version') == '3.0'
        assert opf.find('opf:metadata/dc:creator', ns).text == manifest['author']
        assert opf.find('opf:metadata/dc:language', ns).text == 'zh-CN'
        items = {e.get('id'): e for e in opf.findall('opf:manifest/opf:item', ns)}
        nav = [e for e in items.values() if e.get('properties') == 'nav']
        assert len(nav) == 1
        for item in items.values():
            assert 'EPUB/' + item.get('href') in z.namelist()
        spine = opf.findall('opf:spine/opf:itemref', ns)
        assert len(spine) == len(pages)
        assert all(e.get('idref') in items for e in spine)
        # Strip the XHTML namespace to share link validation with local documents.
        trees = {}
        for name in z.namelist():
            if name.endswith('.xhtml'):
                tree = ET.fromstring(z.read(name))
                for el in tree.iter():
                    el.tag = el.tag.rsplit('}', 1)[-1]
                trees[name] = tree
        # Stylesheets are valid package targets but do not have fragment identifiers.
        trees['EPUB/style.css'] = ET.Element('style')
        check_links(trees)
        text = '\n'.join(plain(trees['EPUB/' + page['file']]) for page in pages)
        coverage(text, pages, 'EPUB')
        print(f'EPUB：容器、XML、元数据、{len(spine)} 篇正文、导航与书内链接通过。')


def check_html(path, pages):
    parser = HTML()
    parser.feed(path.read_text(encoding='utf-8'))
    assert not parser.external_assets, '离线 HTML 不应依赖外部脚本、样式或图片'
    assert len(parser.ids) == len(set(parser.ids))
    for href in parser.links:
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            continue
        assert not parts.path and unquote(parts.fragment) in parser.ids, f'离线 HTML 存在本地文件依赖：{href}'
    coverage(''.join(parser.text), pages, 'HTML')
    print('离线 HTML：内置资料、内部链接与无外部资源依赖检查通过。')


def check_pdf(path, manifest, pages):
    import fitz
    doc = fitz.open(path)
    assert not doc.is_encrypted
    assert doc.metadata.get('author') == manifest['author']
    assert len(doc.get_toc()) == len(pages)
    text = []
    for i, page in enumerate(doc):
        # Exclude repeated header/footer before checking paragraph continuity.
        text.append(page.get_text(clip=fitz.Rect(40, 45, page.rect.width - 40, page.rect.height - 38)))
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                rect = fitz.Rect(line['bbox'])
                assert rect.x0 >= 25 and rect.x1 <= page.rect.width - 25 and rect.y0 >= 15 and rect.y1 <= page.rect.height - 12, f'PDF 第 {i+1} 页文字超出安全边距：{rect}'
        for link in page.get_links():
            if link.get('kind') == fitz.LINK_GOTO:
                assert 0 <= link['page'] < len(doc)
    coverage(''.join(text), pages, 'PDF')
    embedded = [doc.extract_font(font[0])[3] for page in doc for font in page.get_fonts() if font[2] == 'TrueType']
    assert embedded and all(embedded), 'PDF 中文字体应嵌入文档'
    print(f'PDF：{len(doc)} 页、作者、书签、内部跳转、文字边距、内容完整性与字体嵌入检查通过。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    folder = args.output_dir.resolve()
    info = json.loads((folder / 'build-info.json').read_text(encoding='utf-8'))
    manifest, pages, sources = load_book()
    assert info['sources'] == source_hashes(sources), '导出版已过期，请重新构建'
    assert info['author'] == manifest['author']
    assert info['outputs'] and set(info['outputs']) <= {'epub', 'pdf', 'html', 'txt'}, '构建清单中没有受支持的产物'
    for fmt, output in info['outputs'].items():
        path = folder / output['file']
        assert path.is_file() and path.stat().st_size == output['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == output['sha256'], f'{fmt} 文件内容与构建清单不一致'
        if fmt == 'epub':
            check_epub(path, manifest, pages)
        elif fmt == 'pdf':
            check_pdf(path, manifest, pages)
        elif fmt == 'html':
            check_html(path, pages)
        elif fmt == 'txt':
            text = path.read_text(encoding='utf-8')
            coverage(text, pages, 'TXT')
            urls = {a.get('href') for p in pages for a in p['tree'].iter('a') if a.get('href', '').startswith(('https:', 'http:'))}
            assert all(url in text for url in urls), 'TXT 丢失外部网址'
            print('TXT：UTF-8、全文与外部网址检查通过。')
    print('所有已构建格式通过检查；此检查不验证政策有效性，也不等同于 EPUBCheck 或各阅读器实测。')


if __name__ == '__main__':
    main()
