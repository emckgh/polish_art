#!/usr/bin/env python3
"""
Generate professional executive summary PDF with standard business formatting:
- Centered title page
- Table of contents with page numbers
- Page breaks between major sections
- Headers and footers
- Professional typography and spacing

Requires: pip install reportlab markdown
Run: python scripts/generate_executive_pdf.py
"""
from pathlib import Path
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, Frame, PageTemplate
)
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_MD = PROJECT_ROOT / "docs" / "Executive_Summary_Surveillance_System.md"
OUTPUT_PDF = PROJECT_ROOT / "docs" / "Executive_Summary_Surveillance_System.pdf"


class NumberedCanvas(canvas.Canvas):
    """Canvas with page numbers and headers."""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_elements(self, num_pages):
        self.saveState()
        self.setFont('Helvetica', 9)
        
        page_num = self._pageNumber
        
        # Skip header/footer on title page (page 1)
        if page_num > 1:
            # Header
            self.setFillColor(HexColor('#666666'))
            self.drawString(0.75*inch, letter[1] - 0.5*inch, 
                          "Polish Looted Art Surveillance System")
            
            # Footer with page number
            self.drawRightString(letter[0] - 0.75*inch, 0.5*inch,
                               f"Page {page_num - 1}")  # -1 to not count title page
        
        self.restoreState()


def create_styles():
    """Create custom paragraph styles for business document."""
    styles = getSampleStyleSheet()
    
    # Title page styles
    styles.add(ParagraphStyle(
        name='TitlePage',
        parent=styles['Title'],
        fontSize=28,
        leading=34,
        textColor=HexColor('#1a1a1a'),
        alignment=TA_CENTER,
        spaceAfter=0.3*inch,
        fontName='Helvetica-Bold',
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitle',
        fontSize=16,
        leading=20,
        textColor=HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=0.2*inch,
        fontName='Helvetica',
    ))
    
    styles.add(ParagraphStyle(
        name='TitleMeta',
        fontSize=11,
        leading=14,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        fontName='Helvetica',
    ))
    
    # Content styles
    styles['Heading1'].fontSize = 18
    styles['Heading1'].textColor = HexColor('#1a1a1a')
    styles['Heading1'].spaceAfter = 0.2*inch
    styles['Heading1'].spaceBefore = 0.3*inch
    styles['Heading1'].fontName = 'Helvetica-Bold'
    styles['Heading1'].borderWidth = 0
    styles['Heading1'].borderPadding = 0
    
    styles['Heading2'].fontSize = 14
    styles['Heading2'].textColor = HexColor('#2c3e50')
    styles['Heading2'].spaceAfter = 0.15*inch
    styles['Heading2'].spaceBefore = 0.25*inch
    styles['Heading2'].fontName = 'Helvetica-Bold'
    
    styles['Heading3'].fontSize = 12
    styles['Heading3'].textColor = HexColor('#34495e')
    styles['Heading3'].spaceAfter = 0.1*inch
    styles['Heading3'].spaceBefore = 0.2*inch
    styles['Heading3'].fontName='Helvetica-Bold'
    
    styles['Normal'].fontSize = 11
    styles['Normal'].leading = 15
    styles['Normal'].alignment = TA_JUSTIFY
    styles['Normal'].textColor = HexColor('#333333')
    styles['Normal'].fontName = 'Helvetica'
    
    styles.add(ParagraphStyle(
        name='TOCEntry',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        leftIndent=0,
        spaceAfter=0.08*inch,
    ))
    
    return styles


def parse_markdown_to_flowables(md_content, styles):
    """Parse markdown and create reportlab flowables."""
    flowables = []
    lines = md_content.split('\n')
    
    current_para = []
    in_list = False
    toc_entries = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # H1
        if line.startswith('# ') and not line.startswith('## '):
            if current_para:
                text = ' '.join(current_para)
                flowables.append(Paragraph(text, styles['Normal']))
                flowables.append(Spacer(1, 0.1*inch))
                current_para = []
            
            title = line[2:].strip()
            if 'Executive Summary' not in title:  # Don't add main title to TOC
                toc_entries.append((title, 1))
                flowables.append(PageBreak())
            flowables.append(Paragraph(title, styles['Heading1']))
            in_list = False
            
        # H2
        elif line.startswith('## '):
            if current_para:
                text = ' '.join(current_para)
                flowables.append(Paragraph(text, styles['Normal']))
                flowables.append(Spacer(1, 0.1*inch))
                current_para = []
            
            title = line[3:].strip()
            toc_entries.append((title, 2))
            flowables.append(Paragraph(title, styles['Heading2']))
            in_list = False
            
        # H3
        elif line.startswith('### '):
            if current_para:
                text = ' '.join(current_para)
                flowables.append(Paragraph(text, styles['Normal']))
                flowables.append(Spacer(1, 0.1*inch))
                current_para = []
            
            title = line[4:].strip()
            flowables.append(Paragraph(title, styles['Heading3']))
            in_list = False
            
        # Horizontal rule - use as section break
        elif line.startswith('---'):
            if current_para:
                text = ' '.join(current_para)
                flowables.append(Paragraph(text, styles['Normal']))
                current_para = []
            flowables.append(Spacer(1, 0.15*inch))
            in_list = False
            
        # Bullet list
        elif line.startswith('- '):
            if current_para:
                text = ' '.join(current_para)
                flowables.append(Paragraph(text, styles['Normal']))
                flowables.append(Spacer(1, 0.05*inch))
                current_para = []
            
            bullet_text = line[2:].strip()
            # Handle bold carefully
            bullet_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', bullet_text)
            # Handle italic
            bullet_text = re.sub(r'\*([^*]+?)\*', r'<i>\1</i>', bullet_text)
            # Clean up
            bullet_text = bullet_text.replace('**', '')
            flowables.append(Paragraph(f'• {bullet_text}', styles['Normal']))
            in_list = True
            
        # Empty line
        elif not line:
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    flowables.append(Paragraph(text, styles['Normal']))
                    flowables.append(Spacer(1, 0.1*inch))
                current_para = []
            if in_list:
                flowables.append(Spacer(1, 0.05*inch))
            in_list = False
            
        # Regular paragraph text
        else:
            # Handle bold - must be properly closed
            line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            # Handle italic
            line = re.sub(r'\*([^*]+?)\*', r'<i>\1</i>', line)
            # Escape any remaining asterisks
            line = line.replace('**', '')
            
            if current_para or line:
                current_para.append(line)
        
        i += 1
    
    # Flush remaining
    if current_para:
        text = ' '.join(current_para)
        if text.strip():
            flowables.append(Paragraph(text, styles['Normal']))
    
    return flowables, toc_entries


def create_title_page(styles):
    """Create centered title page."""
    return [
        Spacer(1, 2.5*inch),
        Paragraph("Polish Looted Art Surveillance System", styles['TitlePage']),
        Spacer(1, 0.2*inch),
        Paragraph("Executive Summary", styles['Subtitle']),
        Spacer(1, 0.5*inch),
        Paragraph("Technical Surveillance System for Cultural Heritage Recovery", styles['TitleMeta']),
        Spacer(1, 0.3*inch),
        Paragraph("February 2026", styles['TitleMeta']),
        Spacer(1, 0.2*inch),
        Paragraph("For Museum Directors and Ministry Officials", styles['TitleMeta']),
        PageBreak(),
    ]


def create_toc(toc_entries, styles):
    """Create table of contents."""
    toc_flowables = [
        Paragraph("Table of Contents", styles['Heading1']),
        Spacer(1, 0.2*inch),
    ]
    
    for title, level in toc_entries:
        if level == 1:
            toc_flowables.append(Paragraph(f'<b>{title}</b>', styles['TOCEntry']))
        else:
            indent = '    ' * (level - 1)
            toc_flowables.append(Paragraph(f'{indent}{title}', styles['TOCEntry']))
    
    toc_flowables.append(PageBreak())
    return toc_flowables


def main():
    if not INPUT_MD.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_MD}")
    
    with open(INPUT_MD, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create PDF with custom canvas for page numbers
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=inch,
        bottomMargin=0.75*inch,
    )
    
    styles = create_styles()
    
    # Build flowables
    story = []
    
    # Title page
    story.extend(create_title_page(styles))
    
    # Parse content and build TOC
    content_flowables, toc_entries = parse_markdown_to_flowables(md_content, styles)
    
    # Add TOC
    story.extend(create_toc(toc_entries, styles))
    
    # Add content
    story.extend(content_flowables)
    
    # Build PDF with numbered pages
    doc.build(story, canvasmaker=NumberedCanvas)
    
    print(f"Professional PDF generated: {OUTPUT_PDF}")
    print(f"Size: {OUTPUT_PDF.stat().st_size / 1024:.1f} KB")
    print(f"Pages: Title + TOC + ~{len(toc_entries)} sections")


if __name__ == "__main__":
    main()
