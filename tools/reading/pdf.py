"""Chinese PDF with embedded TrueType font, bookmarks, page TOC and linked sources."""
import os
import re
from pathlib import Path

from .book import TITLE, plain, xml


def find_font(requested=None):
    explicit = requested or os.environ.get('SAVE_MONEY_PDF_FONT')
    if explicit:
        if not Path(explicit).is_file():
            raise RuntimeError('指定的 PDF 字体不存在：' + explicit)
        return str(Path(explicit).resolve())
    candidates = [
                  '/Library/Fonts/Arial Unicode.ttf',
                  '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                  '/usr/share/fonts/truetype/arphic/uming.ttc']
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError('PDF 需要包含简体中文的 TrueType 字体。Linux 可安装 fonts-wqy-zenhei；或用 --font fonts/chinese-font.ttf 指定。')


def build(output, manifest, pages, font=None):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle
    from reportlab.platypus.tableofcontents import TableOfContents

    font_path = find_font(font)
    pdfmetrics.registerFont(TTFont('GuideCJK', font_path, subfontIndex=0))
    glyphs = pdfmetrics.getFont('GuideCJK').face.charToGlyph
    missing = sorted({c for page in pages for c in plain(page['tree']) if '\u3400' <= c <= '\u9fff' and ord(c) not in glyphs})
    if missing:
        raise RuntimeError('PDF 字体缺少中文字形：' + ''.join(missing[:20]))
    pdfmetrics.registerFontFamily('GuideCJK', normal='GuideCJK', bold='GuideCJK', italic='GuideCJK', boldItalic='GuideCJK')
    ink = colors.HexColor('#24382e')
    muted = colors.HexColor('#667268')
    accent = colors.HexColor('#285c42')
    styles = {
        'body': ParagraphStyle('Body', fontName='GuideCJK', fontSize=10, leading=16, wordWrap='CJK', spaceAfter=7, textColor=ink),
        'h1': ParagraphStyle('Chapter', fontName='GuideCJK', fontSize=21, leading=30, wordWrap='CJK', spaceAfter=20, textColor=ink, keepWithNext=True),
        'h2': ParagraphStyle('Section', fontName='GuideCJK', fontSize=13, leading=21, wordWrap='CJK', spaceBefore=16, spaceAfter=10, textColor=accent, keepWithNext=True),
        'h3': ParagraphStyle('Subsection', fontName='GuideCJK', fontSize=11, leading=18, wordWrap='CJK', spaceBefore=12, spaceAfter=8, textColor=accent, keepWithNext=True),
        'quote': ParagraphStyle('Quote', fontName='GuideCJK', fontSize=8, leading=13, wordWrap='CJK', spaceAfter=10, textColor=muted, leftIndent=10),
        'list': ParagraphStyle('List', fontName='GuideCJK', fontSize=9.5, leading=15, wordWrap='CJK', spaceAfter=3, textColor=ink),
        'cell': ParagraphStyle('Cell', fontName='GuideCJK', fontSize=7.8, leading=12, wordWrap='CJK', spaceAfter=0, textColor=ink),
        'cover': ParagraphStyle('Cover', fontName='GuideCJK', fontSize=32, leading=44, alignment=TA_CENTER, wordWrap='CJK', textColor=ink, spaceAfter=30),
        'center': ParagraphStyle('Center', fontName='GuideCJK', fontSize=12, leading=22, alignment=TA_CENTER, wordWrap='CJK', spaceAfter=18, textColor=muted),
    }

    def inline(el):
        text = xml(el.text or '')
        for child in el:
            value = inline(child)
            if child.tag == 'a':
                if child.get('id'):
                    value = f'<a name="{xml(child.get("id"))}"/>' + value
                if child.get('href'):
                    href = child.get('href')
                    if '.xhtml#' in href:
                        href = '#' + href.split('#', 1)[1]
                    value = f'<a href="{xml(href)}" color="#285c42">{value}</a>'
            elif child.tag in ('strong', 'b'):
                value = '<b>' + value + '</b>'
            elif child.tag in ('em', 'i'):
                value = '<i>' + value + '</i>'
            elif child.tag == 'br':
                value = '<br/>'
            text += value + xml(child.tail or '')
        return text

    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('TOC', fontName='GuideCJK', fontSize=9, leading=16, wordWrap='CJK', spaceBefore=0, leftIndent=0, rightIndent=22)]
    toc.tableStyle = TableStyle([('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)])
    width, height = A4
    margin = 48
    available = width - 2 * margin

    class Document(BaseDocTemplate):
        def afterFlowable(self, flowable):
            key = getattr(flowable, 'bookmark', None)
            if key:
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0, closed=False)
                self.notify('TOCEntry', (0, flowable.getPlainText(), self.page, key))

    def decorate(canvas, document):
        canvas.setTitle(TITLE)
        canvas.setAuthor(manifest['author'])
        canvas.setSubject('由 Markdown 生成的阅读导出版；政策口径见正文与待核实清单')
        canvas.setFont('GuideCJK', 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(margin, height - 29, TITLE + ' | 阅读导出版')
        canvas.drawRightString(width - margin, 25, str(document.page))

    doc = Document(str(output), pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=52, bottomMargin=44,
                   title=TITLE, author=manifest['author'], allowSplitting=True)
    doc.addPageTemplates(PageTemplate(id='book', frames=[Frame(margin, 44, available, height - 96, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=decorate))
    story = [Spacer(1, 140), Paragraph(TITLE, styles['cover']), Paragraph('一份给普通打工人的成本结构说明书', styles['center']),
             Paragraph('作者：' + xml(manifest['author']), styles['center']), Paragraph('北京 · 上海 · 广州 · 深圳', styles['center']),
             Spacer(1, 55), Paragraph('原文版本：' + xml(manifest['source_version']), styles['center']),
             Paragraph('阅读导出版 · 正文与工具内容的许可范围见书末说明', styles['center']), PageBreak(), Paragraph('阅读目录', styles['h1']), toc]

    def flow(el):
        if el.tag == 'a':
            return [Paragraph(inline(el) if not el.get('id') else f'<a name="{xml(el.get("id"))}"/>' + inline(el), styles['body'])] if el.get('id') else []
        if re.fullmatch(r'h[1-6]', el.tag):
            style = styles[el.tag] if el.tag in styles else styles['h3']
            value = inline(el)
            if el.get('id'):
                value = f'<a name="{xml(el.get("id"))}"/>' + value
            p = Paragraph(value, style)
            if el.tag == 'h1':
                p.bookmark = el.get('id')
            return [p]
        if el.tag == 'blockquote':
            return [Paragraph(inline(child), styles['quote']) for child in el if plain(child).strip()]
        if el.tag in ('ul', 'ol'):
            return [Paragraph((str(i+1) + '. ' if el.tag == 'ol' else '• ') + inline(child), styles['list']) for i, child in enumerate(el)]
        if el.tag == 'table':
            rows = [[Paragraph(inline(cell), styles['cell']) for cell in row] for row in el.iter('tr')]
            ncols = len(rows[0])
            # Weighted widths keep narrow number columns from consuming prose columns.
            weights = []
            for col in range(ncols):
                samples = [min(len(plain(list(row)[col])), 50) for row in el.iter('tr')]
                weights.append(max(4, min(22, sum(samples) / len(samples))))
            widths = [available * w / sum(weights) for w in weights]
            table = LongTable(rows, colWidths=widths, repeatRows=1, hAlign='LEFT', splitByRow=1, splitInRow=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eddf')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f8f3')]),
                ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#cdd3c6')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            return [table, Spacer(1, 12)]
        if el.tag == 'hr':
            return [Spacer(1, 10)]
        if plain(el).strip() or list(el):
            return [Paragraph(inline(el), styles['body'])]
        return []

    for page in pages:
        story.append(PageBreak())
        for element in page['tree']:
            story.extend(flow(element))
    doc.multiBuild(story)
    return font_path
