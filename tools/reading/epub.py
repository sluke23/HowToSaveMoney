"""EPUB 3, with navigation, NCX fallback and reflowable chapter files."""
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .book import TITLE, LANGUAGE, xml, html_body


def wrap(title, body):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{LANGUAGE}" lang="{LANGUAGE}">
<head><title>{xml(title)}</title><link href="style.css" rel="stylesheet" type="text/css"/></head><body>{body}</body></html>'''


def build(output, manifest, pages):
    uid = 'urn:sha256:' + hashlib.sha256(''.join(p['md'] for p in pages).encode()).hexdigest()
    modified = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    nav_items = []
    for page in pages:
        subs = [el for el in page['tree'].iter('h2') if el.get('id')]
        subnav = '<ol>' + ''.join(f'<li><a href="{page["file"]}#{el.get("id")}">{xml("".join(el.itertext()))}</a></li>' for el in subs) + '</ol>' if subs else ''
        nav_items.append(f'<li><a href="{page["file"]}">{xml(page["title"])}</a>{subnav}</li>')
    nav = wrap('目录', '<nav epub:type="toc" id="toc"><h1>目录</h1><ol>' + ''.join(nav_items) + '</ol></nav>')
    ncx = f'''<?xml version="1.0" encoding="utf-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{uid}"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head><docTitle><text>{TITLE}</text></docTitle><navMap>''' + ''.join(f'<navPoint id="n{i}" playOrder="{i+1}"><navLabel><text>{xml(page["title"])}</text></navLabel><content src="{page["file"]}"/></navPoint>' for i, page in enumerate(pages)) + '</navMap></ncx>'
    items = '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/><item id="css" href="style.css" media-type="text/css"/>'
    items += ''.join(f'<item id="p{i}" href="{page["file"]}" media-type="application/xhtml+xml"/>' for i, page in enumerate(pages))
    spine = ''.join(f'<itemref idref="p{i}"/>' for i in range(len(pages)))
    opf = f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="{LANGUAGE}"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">{uid}</dc:identifier><dc:title>{TITLE}</dc:title><dc:creator>{xml(manifest['author'])}</dc:creator><dc:language>{LANGUAGE}</dc:language><dc:rights>一般正文 CC BY-NC-SA 4.0；指定工具内容 CC BY 4.0，具体见许可范围。</dc:rights><meta property="dcterms:modified">{modified}</meta></metadata><manifest>{items}</manifest><spine toc="ncx">{spine}</spine></package>'''
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        for name, text in [('package.opf', opf), ('nav.xhtml', nav), ('toc.ncx', ncx)]:
            z.writestr('EPUB/' + name, text)
        z.writestr('EPUB/style.css', Path(__file__).with_name('style.css').read_text(encoding='utf-8'))
        for page in pages:
            z.writestr('EPUB/' + page['file'], wrap(page['title'], html_body(page)))
