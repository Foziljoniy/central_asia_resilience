"""Build a clean Word manuscript from the approved Markdown manuscript."""

from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "full_manuscript_v2_clean.md"
OUTPUT = ROOT / "manuscript" / "final" / "Foziljon_Alisherov_Remittances_Shocks.docx"


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text.strip())
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(9)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, rows):
    widths = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=widths)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, row in enumerate(rows):
        for j in range(widths):
            value = row[j] if j < len(row) else ""
            set_cell_text(table.cell(i, j), value, bold=(i == 0))
            if i == 0:
                shade(table.cell(i, j), "D9EAF0")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_markdown_paragraph(doc, text):
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = text.replace("**", "")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.08
    for part in re.split(r"(`[^`]+`|\*[^*]+\*)", text):
        if not part:
            continue
        run = p.add_run(part.strip("`") if part.startswith("`") else part.strip("*"))
        run.font.name = "Aptos"
        run.font.size = Pt(10.5)
        if part.startswith("*") and not part.startswith("**"):
            run.italic = True
    return p


def build():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.8)
    sec.bottom_margin = Inches(0.8)
    sec.left_margin = Inches(0.9)
    sec.right_margin = Inches(0.9)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)

    i = 0
    first_title = True
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(10)
            run = p.add_run(line[2:].strip())
            run.bold = True
            run.font.name = "Aptos Display"
            run.font.size = Pt(20)
            run.font.color.rgb = RGBColor(0x0E, 0x4F, 0x5C)
            first_title = False
            i += 1
            continue
        if line.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(5)
            run = p.add_run(line[3:].strip())
            run.bold = True
            run.font.name = "Aptos Display"
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0x0E, 0x4F, 0x5C)
            i += 1
            continue
        if line.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(line[4:].strip())
            run.bold = True
            run.font.name = "Aptos Display"
            run.font.size = Pt(11.5)
            run.font.color.rgb = RGBColor(0x2A, 0x6F, 0x7B)
            i += 1
            continue
        if line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            p.add_run(line[2:].strip()).font.size = Pt(10.5)
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", x) for x in raw):
                    rows.append(raw)
                i += 1
            if rows:
                add_table(doc, rows)
            continue
        add_markdown_paragraph(doc, line)
        i += 1

    # Add explicit title-page metadata if the source front matter changes later.
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Foziljon Alisherov and Mukhayyo Djuraeva | Remittances and household shocks")
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
