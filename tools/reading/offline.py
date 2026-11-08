"""Standalone HTML and UTF-8 plain text; no links to local repository files."""
import re
from pathlib import Path

from .book import TITLE, plain, xml, html_body


def build_html(output, manifest, pages):
    style = Path(__file__).with_name('style.css').read_text(encoding='utf-8')
    nav = ''.join(f'<li><a href="#{p["id"]}">{xml(p["title"])}</a></li>' for p in pages)
    articles = ''.join(f'<article>{html_body(p, single=True)}</article>' for p in pages)
    text = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="author" content="{xml(manifest['author'])}"><title>{TITLE}</title><style>{style}
body{{max-width:1000px;margin:auto;padding:20px;background:#faf8f2}}html{{scroll-padding-top:90px}}.search{{position:sticky;top:0;background:#faf8f2;padding:12px 0;border-bottom:1px solid #cdd3c6}}input,button{{font:inherit;padding:8px;max-width:100%}}input{{width:65%}}[hidden]{{display:none!important}}article{{margin:35px 0;border-top:2px solid #285c42}}table{{display:block;overflow-x:auto}}@media print{{.search{{display:none}}article{{break-before:page}}}} 
</style></head><body><div class="search"><label for="q">全文搜索 </label><input id="q" type="search" placeholder="租房、医保、公积金……"><button id="reset">重置</button><p id="count" role="status" aria-live="polite"></p></div><nav aria-label="目录"><h1>阅读目录</h1><ol>{nav}</ol></nav><main>{articles}</main><p id="empty" hidden>没有找到匹配内容，请换个关键词。</p><script>
const q=document.querySelector('#q'),articles=[...document.querySelectorAll('article')];
function filter(){{const terms=q.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);let count=0;for(const a of articles){{a.hidden=!terms.every(t=>a.textContent.toLowerCase().includes(t));if(!a.hidden)count++;}}document.querySelector('#count').textContent='显示 '+count+' 篇';document.querySelector('#empty').hidden=count>0;}}
function reset(){{q.value='';filter();}}q.addEventListener('input',filter);document.querySelector('#reset').addEventListener('click',reset);
function reveal(){{const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(target?.closest('article')?.hidden){{reset();target.scrollIntoView();}}}}window.addEventListener('hashchange',reveal);document.addEventListener('click',e=>{{if(e.target.closest('a[href^="#"]'))reset();}});filter();reveal();
</script></body></html>'''
    output.write_text(text, encoding='utf-8')


def build_txt(output, manifest, pages):
    lines = [TITLE, '作者：' + manifest['author'], '原文版本：' + manifest['source_version'], '']

    def with_urls(el):
        text = plain(el)
        urls = list(dict.fromkeys(a.get('href') for a in el.iter('a') if a.get('href', '').startswith(('http:', 'https:'))))
        return text + ''.join(' <' + url + '>' for url in urls if url not in text)

    def emit(el, depth=0):
        if re.fullmatch(r'h[1-6]', el.tag):
            return ['\n' + plain(el), '']
        if el.tag == 'table':
            return ['\t'.join(with_urls(cell) for cell in row if cell.tag in ('th', 'td')) for row in el.iter('tr')] + ['']
        if el.tag in ('ul', 'ol'):
            return [f'{i+1}. ' + with_urls(li) if el.tag == 'ol' else '- ' + with_urls(li) for i, li in enumerate(el)] + ['']
        if el.tag in ('p', 'blockquote'):
            text = plain(el)
            urls = list(dict.fromkeys(a.get('href') for a in el.iter('a') if a.get('href', '').startswith(('http:', 'https:'))))
            return [text] + ['  ' + url for url in urls if url not in text] + ['']
        return [plain(el)] if plain(el).strip() else []

    for page in pages:
        lines += ['\n' + '=' * 48, '']
        for el in page['tree']:
            lines += emit(el)
    output.write_text('\n'.join(lines).strip() + '\n', encoding='utf-8')
