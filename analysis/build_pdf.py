#!/usr/bin/env python3
"""Typeset the Markdown manuscript with ReportLab and rendered math equations."""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import mathtext
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                               Spacer, Image, Table, TableStyle, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/pdf/when_should_a_learner_split.pdf'
TMP = ROOT/'tmp/pdf_math'
TMP.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

FONTDIR = Path(matplotlib.get_data_path())/'fonts/ttf'
for name, file in [('Body','DejaVuSerif.ttf'), ('Body-Bold','DejaVuSerif-Bold.ttf'),
                   ('Body-Italic','DejaVuSerif-Italic.ttf'),
                   ('Body-BoldItalic','DejaVuSerif-BoldItalic.ttf'),
                   ('Sans','DejaVuSans.ttf'), ('Sans-Bold','DejaVuSans-Bold.ttf'),
                   ('Code','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTDIR/file)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Body-Bold', italic='Body-Italic', boldItalic='Body-BoldItalic')
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='Sans-Bold', italic='Sans', boldItalic='Sans-Bold')

INK = colors.HexColor('#202d34')
BLUE = colors.HexColor('#1b5c73')
GRAY = colors.HexColor('#596970')
WIDTH = A4[0]-106

STYLES = {
    'title': ParagraphStyle('title',fontName='Body-Bold',fontSize=24,leading=29,textColor=INK,spaceAfter=12),
    'subtitle': ParagraphStyle('subtitle',fontName='Body-Italic',fontSize=12.3,leading=18,textColor=GRAY,spaceAfter=14),
    'author': ParagraphStyle('author',fontName='Sans',fontSize=9.5,leading=14,textColor=GRAY,spaceAfter=3),
    'h2': ParagraphStyle('h2',fontName='Sans-Bold',fontSize=12.1,leading=16,textColor=BLUE,spaceBefore=17,spaceAfter=8,keepWithNext=True),
    'h3': ParagraphStyle('h3',fontName='Sans-Bold',fontSize=10.2,leading=14,textColor=INK,spaceBefore=11,spaceAfter=6,keepWithNext=True),
    'body': ParagraphStyle('body',fontName='Body',fontSize=10.05,leading=14.65,textColor=INK,alignment=TA_JUSTIFY,spaceAfter=8,allowWidows=0,allowOrphans=0),
    'abstract': ParagraphStyle('abstract',fontName='Body',fontSize=9.55,leading=13.65,textColor=INK,alignment=TA_JUSTIFY,spaceAfter=9),
    'caption': ParagraphStyle('caption',fontName='Body',fontSize=8.45,leading=11.9,textColor=GRAY,spaceBefore=4,spaceAfter=10,alignment=TA_LEFT),
    'cell': ParagraphStyle('cell',fontName='Sans',fontSize=8.0,leading=11.3,textColor=INK),
    'headcell': ParagraphStyle('headcell',fontName='Sans-Bold',fontSize=8.0,leading=11.3,textColor=colors.white),
    'ref': ParagraphStyle('ref',fontName='Body',fontSize=8.6,leading=12.15,textColor=INK,spaceAfter=8,alignment=TA_LEFT),
}


def inline(text):
    text = html.escape(text, quote=False)
    # URL parentheses need a balanced match for DOI paths such as S0893-6080(98).
    pattern = r'\[([^\]]+)\]\((https?://(?:[^\s()]|\([^()]*\))+)\)'
    text = re.sub(pattern, lambda m: '<link href="'+m.group(2)+'" color="#1b5c73">'+m.group(1)+'</link>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Code" size="8.15">\1</font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
    return text


class Manuscript(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ('h2','h3'):
            title = flowable.getPlainText()
            key = hashlib.sha256(title.encode()).hexdigest()[:18]
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,level=0 if flowable.style.name=='h2' else 1,closed=False)


def page_frame(canvas, doc):
    canvas.saveState()
    if doc.page>1:
        canvas.setFont('Sans',7.2)
        canvas.setFillColor(GRAY)
        canvas.drawString(53,A4[1]-34,'WHEN SHOULD A LEARNER SPLIT?')
        canvas.drawRightString(A4[0]-53,A4[1]-34,'LUODE  |  RESEARCH NOTE 0.1')
        canvas.setStrokeColor(colors.HexColor('#d6dfe2'))
        canvas.line(53,A4[1]-42,A4[0]-53,A4[1]-42)
    canvas.setFont('Sans',7.4)
    canvas.setFillColor(GRAY)
    canvas.drawString(53,29,'7 September 2026  |  AI-assisted draft, not peer reviewed')
    canvas.drawRightString(A4[0]-53,29,str(doc.page))
    canvas.restoreState()


def equation(expr):
    dest = TMP/(hashlib.sha256(expr.encode()).hexdigest()[:20]+'.png')
    mathtext.math_to_image('$'+expr+'$', dest, dpi=240, format='png',
                           prop=matplotlib.font_manager.FontProperties(size=12), color='#202d34')
    with PILImage.open(dest) as im:
        w,h=im.size
    scale=min(72/240,(WIDTH-16)/w)
    image=Image(str(dest),width=w*scale,height=h*scale)
    image.hAlign='CENTER'
    return KeepTogether([Spacer(1,5),image,Spacer(1,12)])


def table(lines):
    rows=[[c.strip() for c in s.strip().strip('|').split('|')] for s in lines]
    rows=[rows[0]]+rows[2:]
    n=len(rows[0])
    widths=([WIDTH*.39,WIDTH*.305,WIDTH*.305] if n==3 else [WIDTH/n]*n)
    cells=[[Paragraph(inline(c),STYLES['headcell' if r==0 else 'cell']) for c in row] for r,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),
                          ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                          ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
                          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f4f5'),colors.white]),
                          ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#bcccd1'))]))
    return t


def build():
    lines=(ROOT/'paper/paper.md').read_text().splitlines()
    story=[]
    i=0
    before_abstract=True
    section=''
    while i<len(lines):
        line=lines[i].strip()
        if not line:
            i+=1
            continue
        if line.startswith('# '):
            story.append(Paragraph(inline(line[2:]),STYLES['title']))
            i+=1
            continue
        if line.startswith('## '):
            section=line[3:]
            before_abstract=False
            story.append(Paragraph(inline(section),STYLES['h2']))
            i+=1
            continue
        if line.startswith('### '):
            story.append(Paragraph(inline(line[4:]),STYLES['h3']))
            i+=1
            continue
        if line=='$$':
            eq=[]
            i+=1
            while lines[i].strip()!='$$':
                eq.append(lines[i].strip())
                i+=1
            story.append(equation(' '.join(eq)))
            i+=1
            continue
        if line.startswith('|'):
            group=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                group.append(lines[i]);i+=1
            t=table(group)
            # Keep each small scientific table with its caption if present.
            j=i
            while j<len(lines) and not lines[j].strip():j+=1
            if j<len(lines) and lines[j].startswith('**Table '):
                story.append(KeepTogether([Spacer(1,5),t,Paragraph(inline(lines[j]),STYLES['caption'])]))
                i=j+1
            else:
                lead=Spacer(1,5)
                lead.keepWithNext=True
                story.extend([lead,t,Spacer(1,10)])
            continue
        if line.startswith('!['):
            match=re.match(r'!\[([^]]*)\]\(([^)]+)\)',line)
            imagepath=(ROOT/'paper'/match.group(2)).resolve()
            with PILImage.open(imagepath) as im:w,h=im.size
            im=Image(str(imagepath),width=WIDTH,height=WIDTH*h/w)
            group=[Spacer(1,8),im]
            j=i+1
            while j<len(lines) and not lines[j].strip():j+=1
            if j<len(lines) and lines[j].startswith('**Figure '):
                group.append(Paragraph(inline(lines[j]),STYLES['caption']))
                i=j+1
            else:i+=1
            story.append(KeepTogether(group))
            continue
        if before_abstract:
            style='subtitle' if line.startswith('*') and not line.startswith('**') else 'author'
            story.append(Paragraph(inline(line),STYLES[style]))
            i+=1
            continue
        paragraph=[line]
        i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','$$','|','![')):
            paragraph.append(lines[i].strip());i+=1
        content=' '.join(paragraph)
        style=('ref' if section=='References' else 'abstract' if section=='Abstract' else
               'caption' if content.startswith(('**Table ','**Figure ')) else 'body')
        para=Paragraph(inline(content),STYLES[style])
        j=i
        while j<len(lines) and not lines[j].strip():j+=1
        if j<len(lines) and lines[j].strip().startswith('|'):
            para.keepWithNext=True
        story.append(para)
    doc=Manuscript(str(OUT),pagesize=A4,leftMargin=53,rightMargin=53,topMargin=55,bottomMargin=48,
                   title='When Should a Learner Split?',author='Antti Luode',
                   subject='Responsibility, interference, and evidence for structural specialization')
    frame=Frame(53,48,WIDTH,A4[1]-103,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='all',frames=[frame],onPage=page_frame))
    doc.build(story)
    print(OUT)


if __name__=='__main__':build()
