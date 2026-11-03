import re
from core.config import MATH_FUNCS, GREEK_CHARS
from core.typography import _split_text_by_spectrum

ITALICIZE_MATH_FUNCTIONS = False


def split_math_text_runs(text):
    pattern = re.compile(r'([A-Za-z]+|[' + GREEK_CHARS + r'])')
    tokens = []
    last_idx = 0
    for m in pattern.finditer(text):
        start, end = m.span()
        if start > last_idx:
            tokens.append((text[last_idx:start], False))
        val = m.group(0)
        if val.lower() in MATH_FUNCS:
            tokens.append((val, ITALICIZE_MATH_FUNCTIONS))
        else:
            tokens.append((val, True))
        last_idx = end
    if last_idx < len(text):
        tokens.append((text[last_idx:], False))
    return tokens

def parse_math_to_list(s):
    s = re.sub(r'\\(?:text|mathbf|mathrm|mathit)\{([^}]+)\}', r'\1', s)

    s = re.sub(r'(?<!\\)\{([,.;+\-=])\}', r'\1', s)

    s = re.sub(r'(?:\\?\s*)\^\{?\\circ\}?(?:\\?\s*)(?:\\(?:text|mathrm|mathbf)\{([CСcс])\}|\{([CСcс])\}|([CСcс]))(?![a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ])',
               lambda m: f" °{m.group(1) or m.group(2) or m.group(3)}", s)
    s = re.sub(r'(?:\\?\s*)\\(?:degree|celsius)(?:\\?\s*)(?:\\(?:text|mathrm|mathbf)\{([CСcс])\}|\{([CСcс])\}|([CСcс]))?(?![a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ])',
               lambda m: f" °{m.group(1) or m.group(2) or m.group(3)}" if (m.group(1) or m.group(2) or m.group(3)) else "°", s)
    s = re.sub(r'(?:\\?\s*)\\circ(?:\\?\s*)(?:\\(?:text|mathrm|mathbf)\{([CСcс])\}|\{([CСcс])\}|([CСcс]))(?![a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ])',
               lambda m: f" °{m.group(1) or m.group(2) or m.group(3)}", s)
    s = re.sub(r'(?:\\?\s*)\^\{?\\circ\}?', '°', s)

    replacements = {
        r'\{': '{', r'\}': '}',
        r'\dots': '…', r'\cdot': '·',
        r'\rightarrow': '→', r'\leftarrow': '←', 
        r'\infty': '∞',
        r'\left': '', r'\right': '',
        r'\approx': '≈', r'\le': '≤', r'\ge': '≥', r'\to': '→', r'\neq': '≠', r'\pm': '±',
        r'\quad': '    ', r'\ ': ' ',
        r'\times': '×', r'\%': '%',
        r'\ln': 'ln ', r'\min': 'min', r'\max': 'max',
        r'\sum': '∑', r'\prod': '∏', r'\int': '∫', r'\in': '∈', r'\notin': '∉', r'\cup': '∪', r'\cap': '∩',
        r'\partial': '∂', r'\nabla': '∇',
        r'\rho': 'ρ', r'\delta': 'δ', r'\alpha': 'α', r'\beta': 'β',
        r'\gamma': 'γ', r'\lambda': 'λ', r'\mu': 'μ', r'\pi': 'π',
        r'\sigma': 'σ', r'\omega': 'ω', r'\theta': 'θ', r'\vartheta': 'ϑ',
        r'\tau': 'τ', r'\epsilon': 'ε', r'\varepsilon': 'ε', r'\eta': 'η',
        r'\nu': 'ν', r'\xi': 'ξ', r'\phi': 'φ', r'\varphi': 'ϕ', r'\chi': 'χ',
        r'\psi': 'ψ', r'\zeta': 'ζ', r'\kappa': 'κ',
        r'\Delta': 'Δ', r'\Gamma': 'Γ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
        r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Upsilon': 'Υ',
        r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
        r'\circ': '∘', r'\degree': '°'
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    B0 = r"[^{}]*"
    B1 = r"(?:[^{}]|\{" + B0 + r"\})*"
    B2 = r"(?:[^{}]|\{" + B1 + r"\})*"
    B3 = r"(?:[^{}]|\{" + B2 + r"\})*"
    B4 = r"(?:[^{}]|\{" + B3 + r"\})*"
    FRAC_ARG = r"\{" + B4 + r"\}"
    ACC_EXPR = r"(?:\\(?:bar|vec)(?:" + FRAC_ARG + r"|\s*\\[a-zA-Z]+|\s*[^\W_]))"
    VAL = r"(?:[^\W_]+|\{" + B4 + r"\})"
    BASE = r"(?:" + ACC_EXPR + r"|[^\W_\']+|∑|∏|∫|\||\)|\]|\{" + B4 + r"\}|\\[a-zA-Z]+)"

    pattern = re.compile(
        r'(?P<frac>\\frac(?P<frac_num>' + FRAC_ARG + r')(?P<frac_den>' + FRAC_ARG + r'))|'
        r'(?P<subsup>(?P<ss_base>' + BASE + r')_(?P<ss_sub>' + VAL + r')\^(?P<ss_sup>' + VAL + r'))|'
        r'(?P<supsub>(?P<sus_base>' + BASE + r')\^(?P<sus_sup>' + VAL + r')_(?P<sus_sub>' + VAL + r'))|'
        r'(?P<sub>(?P<sub_base>' + BASE + r')_(?P<sub_val>' + VAL + r'))|'
        r'(?P<sup>(?P<sup_base>' + BASE + r')\^(?P<sup_val>' + VAL + r'))|'
        r'(?P<bar_b>\\bar(?P<bar_b_val>' + FRAC_ARG + r'))|'
        r'(?P<bar_s>\\bar\s*(?P<bar_s_val>(?:\\[a-zA-Z]+|[^\W_])))|'
        r'(?P<vec_b>\\vec(?P<vec_b_val>' + FRAC_ARG + r'))|'
        r'(?P<vec_s>\\vec\s*(?P<vec_s_val>(?:\\[a-zA-Z]+|[^\W_])))'
    )

    def parse_math_group(val):
        if val and val.startswith('{') and val.endswith('}'):
            val = val[1:-1]
        return parse_math_to_list(val)

    last_idx = 0
    items = []
    for m in pattern.finditer(s):
        start, end = m.span()
        if start > last_idx:
            items.append(s[last_idx:start])

        gd = m.groupdict()
        if gd['frac']:
            items.append(("frac", parse_math_group(gd['frac_num']), parse_math_group(gd['frac_den'])))
        elif gd['subsup']:
            items.append(("subsup", parse_math_group(gd['ss_base']), parse_math_group(gd['ss_sub']), parse_math_group(gd['ss_sup'])))
        elif gd['supsub']:
            items.append(("subsup", parse_math_group(gd['sus_base']), parse_math_group(gd['sus_sub']), parse_math_group(gd['sus_sup'])))
        elif gd['sub']:
            items.append(("sub", parse_math_group(gd['sub_base']), parse_math_group(gd['sub_val'])))
        elif gd['sup']:
            items.append(("sup", parse_math_group(gd['sup_base']), parse_math_group(gd['sup_val'])))
        elif gd['bar_b']:
            items.append(("bar", parse_math_group(gd['bar_b_val'])))
        elif gd['bar_s']:
            items.append(("bar", parse_math_group(gd['bar_s_val'])))
        elif gd['vec_b']:
            items.append(("vec", parse_math_group(gd['vec_b_val'])))
        elif gd['vec_s']:
            items.append(("vec", parse_math_group(gd['vec_s_val'])))

        last_idx = end

    if last_idx < len(s):
        items.append(s[last_idx:])

    cleaned = []
    for item in items:
        if isinstance(item, str):
            if item == '':
                continue
            if cleaned and isinstance(cleaned[-1], str):
                cleaned[-1] += item
            else:
                cleaned.append(item)
        else:
            cleaned.append(item)
    return cleaned

def parse_inline(text, is_bold=False, is_italic=False, spectrum_regex=None, current_hl=None):
    pattern = re.compile(
        r'(?P<math>\$(?P<math_val>[^$]+)\$)|'
        r'(?P<mark><mark\s+data-hl="(?P<hl_type>[^"]+)">(?P<hl_content>.*?)</mark>)|'
        r'(?P<bold>\*\*(?P<bold_val>.*?)\*\*)|'
        r'(?P<italic>\*(?P<italic_val>.*?)\*)'
    )

    last_idx = 0
    elements = []
    for m in pattern.finditer(text):
        start, end = m.span()
        if start > last_idx:
            raw_chunk = text[last_idx:start]
            elements.extend(_split_text_by_spectrum(raw_chunk, is_bold, is_italic, spectrum_regex, current_hl))

        gd = m.groupdict()
        if gd['math'] is not None:
            math_elements = parse_math_to_list(gd['math_val'])
            elements.append(("math", math_elements))
        elif gd['mark'] is not None:
            elements.extend(parse_inline(
                gd['hl_content'], 
                is_bold=is_bold, 
                is_italic=is_italic, 
                spectrum_regex=spectrum_regex, 
                current_hl=gd['hl_type']
            ))
        elif gd['bold'] is not None:
            elements.extend(parse_inline(
                gd['bold_val'], 
                is_bold=True, 
                is_italic=is_italic, 
                spectrum_regex=spectrum_regex, 
                current_hl=current_hl
            ))
        elif gd['italic'] is not None:
            elements.extend(parse_inline(
                gd['italic_val'], 
                is_bold=is_bold, 
                is_italic=True, 
                spectrum_regex=spectrum_regex, 
                current_hl=current_hl
            ))

        last_idx = end

    if last_idx < len(text):
        raw_chunk = text[last_idx:]
        elements.extend(_split_text_by_spectrum(raw_chunk, is_bold, is_italic, spectrum_regex, current_hl))

    return elements
