import re
import time
import sys
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from core.typography import apply_text_transformations, get_spectrum_regex
from core.math_parser import parse_math_to_list, parse_inline
from core.docx_builder import add_block_equation, add_header, build_bullet, build_numbered, build_paragraph, build_table, get_new_num_id

def log_progress(current, total, start_time, message=""):
    elapsed = time.time() - start_time
    pct = int((current / total) * 100) if total > 0 else 0
    pct = min(100, max(0, pct))
    eta = ((elapsed / current) * (total - current)) if current > 0 else 0.0
    bar_len = 20
    filled = int(bar_len * pct // 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    clean_msg = message[:35]
    sys.stdout.write(f"\r[WordMath] |{bar}| {pct:3d}% ({current}/{total}) | Elapsed: {elapsed:4.1f}s | ETA: ~{eta:4.1f}s | {clean_msg:<35}")
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write(f"\n[WordMath] ✔ Completed in {elapsed:.2f}s!\n")
        sys.stdout.flush()

def convert_text_to_docx(raw_text, doc, on_progress=None, smart_quotes=False, italicize_spectrum=False, 
                        italic_pattern="[A-Za-z]", replace_dash=False, replace_apostrophe=False, lowercase_colon=False, 
                        remove_emojis=False, custom_replacements=None, highlight_word=False, math_tnr=False):
    raw_text = apply_text_transformations(
        raw_text,
        smart_quotes=smart_quotes,
        replace_dash=replace_dash,
        replace_apostrophe=replace_apostrophe,
        lowercase_colon=lowercase_colon,
        remove_emojis=remove_emojis,
        custom_replacements=custom_replacements,
        highlight=highlight_word
    )

    spectrum_regex = get_spectrum_regex(italic_pattern) if italicize_spectrum else None

    text = raw_text.replace('\r\n', '\n')
    lines = text.split('\n')

    blocks = []
    in_math_block = False
    math_block_content = []
    table_lines = []

    for line in lines:
        line_str = line.strip()

        if in_math_block:
            if line_str.endswith('$$'):
                rest = line_str[:-2].strip()
                if rest:
                    math_block_content.append(rest)
                blocks.append(('equation', " ".join(math_block_content)))
                in_math_block = False
            elif line_str:
                math_block_content.append(line_str)
            continue

        if not line_str:
            if table_lines:
                blocks.append(('table', table_lines))
                table_lines = []
            continue

        if line_str.startswith('$$') and line_str.endswith('$$') and len(line_str) > 3:
            if table_lines:
                blocks.append(('table', table_lines))
                table_lines = []
            blocks.append(('equation', line_str[2:-2].strip()))
            continue
        elif line_str.startswith('$$'):
            if table_lines:
                blocks.append(('table', table_lines))
                table_lines = []
            in_math_block = True
            math_block_content = []
            rest = line_str[2:].strip()
            if rest:
                math_block_content.append(rest)
            continue
        elif line_str.startswith('|') and line_str.endswith('|'):
            table_lines.append(line_str)
            continue
        else:
            if table_lines:
                blocks.append(('table', table_lines))
                table_lines = []
            blocks.append(('line', line))

    if table_lines:
        blocks.append(('table', table_lines))

    total = len(blocks)
    if total == 0:
        total = 1

    active_num_id = None
    last_block_type = None

    for idx, (b_type, b_content) in enumerate(blocks, start=1):
        if on_progress:
            on_progress(idx, total, f"Processing block {idx}/{total}")

        if b_type == 'table':
            build_table(doc, b_content, spectrum_regex=spectrum_regex, highlight_word=highlight_word, math_tnr=math_tnr)
            last_block_type = 'table'
            continue

        if b_type == 'equation':
            add_block_equation(doc, parse_math_to_list(b_content), highlight_word=highlight_word, math_tnr=math_tnr)
            last_block_type = 'equation'
            continue

        line_str = b_content.strip()
        if line_str in ('---', '***'):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run('—' * 30)
            r.font.color.rgb = RGBColor(150, 150, 150)
            last_block_type = 'hr'
            continue

        header_match = re.match(r'^(#{1,6})\s+(.*)$', line_str)
        if header_match:
            level = len(header_match.group(1))
            header_text = header_match.group(2)
            add_header(doc, header_text, level, spectrum_regex=spectrum_regex, highlight_word=highlight_word, math_tnr=math_tnr)
            last_block_type = 'header'
            continue

        original_line = b_content.rstrip('\r\n')

        bullet_match = re.match(r'^(\s*)[\*\-\+]\s+(.*)$', original_line)
        if bullet_match:
            spaces = len(bullet_match.group(1))
            level = spaces // 4
            content = bullet_match.group(2)
            build_bullet(doc, parse_inline(content, spectrum_regex=spectrum_regex), 
                         level=level, highlight_word=highlight_word, math_tnr=math_tnr)
            last_block_type = 'bullet'
            continue

        numbered_match = re.match(r'^(\s*)(\d+)\.\s+(.*)$', original_line)
        if numbered_match:
            spaces = len(numbered_match.group(1))
            level = spaces // 4
            num = int(numbered_match.group(2))
            content = numbered_match.group(3)

            if last_block_type != 'numbered' or num == 1:
                active_num_id = get_new_num_id(doc, 'List Number', start_val=num)

            build_numbered(doc, num, parse_inline(content, spectrum_regex=spectrum_regex), 
                           level=level, highlight_word=highlight_word, math_tnr=math_tnr, num_id=active_num_id)
            last_block_type = 'numbered'
            continue

        build_paragraph(doc, parse_inline(line_str, spectrum_regex=spectrum_regex), 
                        highlight_word=highlight_word, math_tnr=math_tnr)
        last_block_type = 'paragraph'
