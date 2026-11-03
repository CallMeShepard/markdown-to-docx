import re
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from core.config import HL_COLOR_MAP
from core.math_parser import split_math_text_runs, parse_inline

def get_new_num_id(doc, style_name='List Number', start_val=1):
    try:
        num_id_base = -1
        for s in doc.styles:
            if s.name == style_name:
                if s._element.pPr is not None and s._element.pPr.numPr is not None:
                    num_id_base = s._element.pPr.numPr.numId.val
                    break
        if num_id_base == -1:
            num_id_base = 1
        ct_numbering = doc.part.numbering_part.numbering_definitions._numbering
        ct_num = ct_numbering.num_having_numId(num_id_base)
        if ct_num is not None:
            abstractNumId = ct_num.abstractNumId.val
            new_num = ct_numbering.add_num(abstractNumId)
            if start_val is not None:
                new_num.add_lvlOverride(0)._add_startOverride().val = start_val
            return new_num.numId
    except Exception:
        pass
    return None

def set_paragraph_numbering(p, num_id, ilvl=0):
    if num_id is not None:
        try:
            pPr = p._p.get_or_add_pPr()
            numPr = pPr.get_or_add_numPr()
            numPr.get_or_add_numId().val = num_id
            numPr.get_or_add_ilvl().val = ilvl
        except Exception:
            pass

def _build_ctrl_pr(highlight_val=None, math_tnr=False):
    ctrlPr = OxmlElement("m:ctrlPr")
    rPr = OxmlElement("w:rPr")
    if math_tnr:
        rFonts = OxmlElement("w:rFonts")
        rFonts.set(qn("w:ascii"), "Times New Roman")
        rFonts.set(qn("w:hAnsi"), "Times New Roman")
        rFonts.set(qn("w:cs"), "Times New Roman")
        rPr.append(rFonts)
    if highlight_val:
        hl = OxmlElement("w:highlight")
        hl.set(qn("w:val"), highlight_val)
        rPr.append(hl)
    if len(rPr) > 0:
        ctrlPr.append(rPr)
    return ctrlPr

def _create_single_math_run(text, is_var, highlight_val=None, math_tnr=False):
    r = OxmlElement("m:r")
    
    if math_tnr or not text.strip():
        mRPr = OxmlElement("m:rPr")
        mRPr.append(OxmlElement("m:nor"))
        r.append(mRPr)

    rPr = OxmlElement("w:rPr")
    if math_tnr:
        rFonts = OxmlElement("w:rFonts")
        rFonts.set(qn("w:ascii"), "Times New Roman")
        rFonts.set(qn("w:hAnsi"), "Times New Roman")
        rFonts.set(qn("w:cs"), "Times New Roman")
        rPr.append(rFonts)

    if is_var:
        rPr.append(OxmlElement("w:i"))

    if highlight_val:
        hl = OxmlElement("w:highlight")
        hl.set(qn("w:val"), highlight_val)
        rPr.append(hl)

    if len(rPr) > 0:
        r.append(rPr)

    t = OxmlElement("m:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r

def _add_math_text(parent, text, highlight_val=None, math_tnr=False):
    runs = split_math_text_runs(text)
    for chunk_text, is_var in runs:
        if not chunk_text:
            continue
        r = _create_single_math_run(chunk_text, is_var, highlight_val, math_tnr)
        parent.append(r)

def _add_math_sub(parent, base_items, sub_items, highlight_val=None, math_tnr=False):
    ssub = OxmlElement("m:sSub")
    pr = OxmlElement("m:sSubPr")
    pr.append(_build_ctrl_pr(highlight_val, math_tnr))
    ssub.append(pr)
    e = OxmlElement("m:e"); _populate_math(e, base_items, highlight_val, math_tnr)
    sub_el = OxmlElement("m:sub"); _populate_math(sub_el, sub_items, highlight_val, math_tnr)
    ssub.append(e); ssub.append(sub_el)
    parent.append(ssub)

def _add_math_sup(parent, base_items, sup_items, highlight_val=None, math_tnr=False):
    ssup = OxmlElement("m:sSup")
    pr = OxmlElement("m:sSupPr")
    pr.append(_build_ctrl_pr(highlight_val, math_tnr))
    ssup.append(pr)
    e = OxmlElement("m:e"); _populate_math(e, base_items, highlight_val, math_tnr)
    sup_el = OxmlElement("m:sup"); _populate_math(sup_el, sup_items, highlight_val, math_tnr)
    ssup.append(e); ssup.append(sup_el)
    parent.append(ssup)

def _add_math_subsup(parent, base_items, sub_items, sup_items, highlight_val=None, math_tnr=False):
    sSubSup = OxmlElement("m:sSubSup")
    pr = OxmlElement("m:sSubSupPr")
    pr.append(_build_ctrl_pr(highlight_val, math_tnr))
    sSubSup.append(pr)
    e = OxmlElement("m:e"); _populate_math(e, base_items, highlight_val, math_tnr)
    sub_el = OxmlElement("m:sub"); _populate_math(sub_el, sub_items, highlight_val, math_tnr)
    sup_el = OxmlElement("m:sup"); _populate_math(sup_el, sup_items, highlight_val, math_tnr)
    sSubSup.append(e); sSubSup.append(sub_el); sSubSup.append(sup_el)
    parent.append(sSubSup)

def _add_math_frac(parent, num_items, den_items, highlight_val=None, math_tnr=False):
    f = OxmlElement("m:f")
    fPr = OxmlElement("m:fPr")
    fPr.append(_build_ctrl_pr(highlight_val, math_tnr))
    f.append(fPr)

    num_el = OxmlElement("m:num")
    _populate_math(num_el, num_items, highlight_val, math_tnr)
    f.append(num_el)

    den_el = OxmlElement("m:den")
    _populate_math(den_el, den_items, highlight_val, math_tnr)
    f.append(den_el)
    parent.append(f)

def _add_math_bar(parent, base_items, highlight_val=None, math_tnr=False):
    acc = OxmlElement("m:acc")
    accPr = OxmlElement("m:accPr")
    accPr.append(_build_ctrl_pr(highlight_val, math_tnr))
    chr_el = OxmlElement("m:chr")
    chr_el.set(qn("m:val"), "\u0304")
    accPr.append(chr_el)
    acc.append(accPr)
    e = OxmlElement("m:e"); _populate_math(e, base_items, highlight_val, math_tnr)
    acc.append(e)
    parent.append(acc)

def _add_math_vec(parent, base_items, highlight_val=None, math_tnr=False):
    acc = OxmlElement("m:acc")
    accPr = OxmlElement("m:accPr")
    accPr.append(_build_ctrl_pr(highlight_val, math_tnr))
    chr_el = OxmlElement("m:chr")
    chr_el.set(qn("m:val"), "\u20D7")
    accPr.append(chr_el)
    acc.append(accPr)
    e = OxmlElement("m:e"); _populate_math(e, base_items, highlight_val, math_tnr)
    acc.append(e)
    parent.append(acc)

def _populate_math(oMath, items, highlight_val=None, math_tnr=False):
    for item in items:
        if isinstance(item, str):
            _add_math_text(oMath, item, highlight_val, math_tnr)
        elif isinstance(item, tuple):
            kind = item[0]
            if kind == "sub": _add_math_sub(oMath, item[1], item[2], highlight_val, math_tnr)
            elif kind == "sup": _add_math_sup(oMath, item[1], item[2], highlight_val, math_tnr)
            elif kind == "subsup": _add_math_subsup(oMath, item[1], item[2], item[3], highlight_val, math_tnr)
            elif kind == "frac": _add_math_frac(oMath, item[1], item[2], highlight_val, math_tnr)
            elif kind == "bar": _add_math_bar(oMath, item[1], highlight_val, math_tnr)
            elif kind == "vec": _add_math_vec(oMath, item[1], highlight_val, math_tnr)

def add_block_equation(doc, items, space_after=12, highlight_word=False, math_tnr=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    oMathPara = OxmlElement("m:oMathPara")
    oMath = OxmlElement("m:oMath")
    oMathPara.append(oMath)
    p._p.append(oMathPara)
    math_hl = "cyan" if highlight_word else None
    _populate_math(oMath, items, math_hl, math_tnr)

def _fill_paragraph(p, elements, highlight_word=False, math_tnr=False):
    for el in elements:
        if el[0] == "text":
            text = el[1]
            bold = el[2] if len(el) > 2 else False
            italic = el[3] if len(el) > 3 else False
            hl_type = el[4] if len(el) > 4 else None

            r = p.add_run(text)
            r.bold = bold
            r.italic = italic
            if highlight_word and hl_type and hl_type in HL_COLOR_MAP:
                r.font.highlight_color = HL_COLOR_MAP[hl_type]
        elif el[0] == "math":
            oMath = OxmlElement("m:oMath")
            math_hl = "cyan" if highlight_word else None
            _populate_math(oMath, el[1], math_hl, math_tnr)
            p._p.append(oMath)

def build_paragraph(doc, elements, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, 
                    hanging_indent=None, left_indent=None, highlight_word=False, math_tnr=False, style=None):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)

    if left_indent is not None:
        p.paragraph_format.left_indent = Pt(left_indent)
    elif hanging_indent:
        p.paragraph_format.left_indent = Pt(hanging_indent)

    if hanging_indent:
        p.paragraph_format.first_line_indent = Pt(-hanging_indent)

    _fill_paragraph(p, elements, highlight_word, math_tnr)
    return p

def _split_table_row(line):
    cells = []
    current = []
    in_math = False
    for char in line:
        if char == "$":
            in_math = not in_math
            current.append(char)
        elif char == "|" and not in_math:
            cells.append("".join(current))
            current = []
        else:
            current.append(char)
    cells.append("".join(current))
    return cells

def build_table(doc, table_lines, spectrum_regex=None, highlight_word=False, math_tnr=False):
    if not table_lines: return
    
    parsed_rows = []
    alignments = []
    
    for i, line in enumerate(table_lines):
        line = line.strip()
        if line.startswith('|'): line = line[1:]
        if line.endswith('|'): line = line[:-1]
        
        cells = _split_table_row(line)
        
        if i == 1:
            is_separator = True
            row_aligns = []
            for cell in cells:
                c = cell.strip()
                if not re.match(r'^:?-+:?$', c):
                    is_separator = False
                    break
                if c.startswith(':') and c.endswith(':'):
                    row_aligns.append(WD_ALIGN_PARAGRAPH.CENTER)
                elif c.endswith(':'):
                    row_aligns.append(WD_ALIGN_PARAGRAPH.RIGHT)
                else:
                    row_aligns.append(WD_ALIGN_PARAGRAPH.LEFT)
            if is_separator:
                alignments = row_aligns
                continue
        
        parsed_rows.append(cells)
        
    if not parsed_rows: return
    
    cols = max(len(row) for row in parsed_rows)
    table = doc.add_table(rows=len(parsed_rows), cols=cols)
    table.style = 'Table Grid'
    
    for r_idx, row_data in enumerate(parsed_rows):
        row_cells = table.rows[r_idx].cells
        for c_idx, cell_text in enumerate(row_data):
            if c_idx < cols:
                p = row_cells[c_idx].paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                
                if alignments and c_idx < len(alignments):
                    p.alignment = alignments[c_idx]
                
                is_header = (r_idx == 0 and len(alignments) > 0)
                elements = parse_inline(cell_text.strip(), is_bold=is_header, spectrum_regex=spectrum_regex)
                _fill_paragraph(p, elements, highlight_word, math_tnr)

def build_bullet(doc, elements, level=0, highlight_word=False, math_tnr=False):
    bullet_styles = {0: 'List Bullet', 1: 'List Bullet 2', 2: 'List Bullet 3'}
    style_name = bullet_styles.get(level, 'List Bullet 3')
    return build_paragraph(doc, elements, style=style_name, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                           space_after=3, highlight_word=highlight_word, math_tnr=math_tnr)

def build_numbered(doc, number, elements, level=0, highlight_word=False, math_tnr=False, num_id=None):
    num_styles = {0: 'List Number', 1: 'List Number 2', 2: 'List Number 3'}
    style_name = num_styles.get(level, 'List Number 3')
    p = build_paragraph(doc, elements, style=style_name, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                        space_after=3, highlight_word=highlight_word, math_tnr=math_tnr)
    if num_id is not None:
        set_paragraph_numbering(p, num_id, ilvl=level)
    return p

def add_header(doc, text, level=1, spectrum_regex=None, highlight_word=False, math_tnr=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(max(2, 12 - level * 2))
    p.paragraph_format.space_before = Pt(12)
    sizes = {1: 18, 2: 16, 3: 15, 4: 14, 5: 14, 6: 14}
    sz = Pt(sizes.get(level, 14))
    elements = parse_inline(text, is_bold=True, spectrum_regex=spectrum_regex)
    for el in elements:
        if el[0] == "text":
            r = p.add_run(el[1])
            r.bold = True
            r.italic = el[3] if len(el) > 3 else False
            r.font.size = sz
            hl_type = el[4] if len(el) > 4 else None
            if highlight_word and hl_type and hl_type in HL_COLOR_MAP:
                r.font.highlight_color = HL_COLOR_MAP[hl_type]
        elif el[0] == "math":
            oMath = OxmlElement("m:oMath")
            math_hl = "cyan" if highlight_word else None
            _populate_math(oMath, el[1], math_hl, math_tnr)
            p._p.append(oMath)

def init_document_styles(doc):
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal_style.font.size = Pt(14)

    list_styles = [
        'List Bullet', 'List Bullet 2', 'List Bullet 3',
        'List Number', 'List Number 2', 'List Number 3',
        'List Paragraph'
    ]
    for s_name in list_styles:
        if s_name in doc.styles:
            st = doc.styles[s_name]
            st.font.name = "Times New Roman"
            if st._element.rPr is not None and st._element.rPr.rFonts is not None:
                st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
            st.font.size = Pt(14)
