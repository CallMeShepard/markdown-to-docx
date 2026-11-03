import re
from core.config import PROPER_NOUNS

EMOJI_REGEX = re.compile(
    r'['
    r'\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
    r'\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF'
    r'\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF'
    r'\U00002702-\U000027B0\U000024C2-\U0001F251\U00002300-\U000023FF'
    r'\U00002600-\U000026FF\uFE0E\uFE0F\u200D'
    r']+',
    flags=re.UNICODE
)

def remove_emojis_smart(text, highlight=False):
    def repl(m):
        return ' \x01EMOJI_SHIFT\x01 ' if highlight else ' '

    s = EMOJI_REGEX.sub(repl, text)

    s = re.sub(r'[ \t]+([.,!?:;»\)])', r'\1', s)
    s = re.sub(r'^(#{1,6})[ \t]+', r'\1 ', s, flags=re.MULTILINE)
    s = re.sub(r'^[ \t]+(?!\*|\-|\+|\d+\.)', '', s, flags=re.MULTILINE)
    s = re.sub(r'[ \t]+$', '', s, flags=re.MULTILINE)
    s = re.sub(r'[ \t]{2,}', ' ', s)

    if highlight and '\x01EMOJI_SHIFT\x01' in s:
        def mark_next_word(m):
            word = m.group(1)
            return f"\x02HL:emoji\x02{word}\x03"

        s = re.sub(r'\x01EMOJI_SHIFT\x01\s*([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9]+)', mark_next_word, s)

        def mark_prev_word(m):
            word = m.group(1)
            punct = m.group(2)
            return f"\x02HL:emoji\x02{word}\x03{punct}"

        s = re.sub(r'([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9]+)\s*\x01EMOJI_SHIFT\x01\s*([.,!?:;»\)])', mark_prev_word, s)

        s = s.replace('\x01EMOJI_SHIFT\x01', '')
        s = re.sub(r'[ \t]{2,}', ' ', s)

    return s

def replace_smart_quotes(text, highlight=False):
    math_placeholders = []
    def stash_math(m):
        idx = len(math_placeholders)
        math_placeholders.append(m.group(0))
        return f"\x00MATH_{idx}\x00"

    s = re.sub(r'\$\$[\s\S]*?\$\$', stash_math, text)
    s = re.sub(r'\$[^\$\n]+?\$', stash_math, s)

    chars = list(s)
    n = len(chars)
    i = 0
    nesting_level = 0

    opening_preceders = set(' \t\n\r([{\'"-—–«„\x02\x03')
    closing_followers = set(' \t\n\r.,;:!?)]}\'"-—–»”\x00\x02\x03')

    while i < n:
        ch = chars[i]
        if ch == '"':
            prev_ch = chars[i - 1] if i > 0 else ' '
            next_ch = chars[i + 1] if i + 1 < n else ' '

            if prev_ch.isdigit() and (next_ch in closing_followers or next_ch == ''):
                i += 1
                continue

            is_opening = (prev_ch in opening_preceders and next_ch not in closing_followers)
            is_closing = (prev_ch not in opening_preceders and (next_ch in closing_followers or next_ch in opening_preceders))

            target = '«'
            if is_opening:
                target = '«' if nesting_level == 0 else '„'
                nesting_level = 1 if nesting_level == 0 else 2
            elif is_closing:
                target = '“' if nesting_level >= 2 else '»'
                nesting_level = 1 if nesting_level >= 2 else 0
            else:
                target = '«' if nesting_level == 0 else '»'
                nesting_level = 1 if nesting_level == 0 else 0

            chars[i] = f'\x02HL:quote\x02{target}\x03' if highlight else target
        elif ch in ('\n', '\r'):
            nesting_level = 0
        i += 1

    res = "".join(chars)
    for idx, math_chunk in enumerate(math_placeholders):
        res = res.replace(f"\x00MATH_{idx}\x00", math_chunk)

    return res

def smart_lowercase_after_colon(text, highlight=False):
    def fix_match(m):
        prefix = m.group(1)
        first_letter = m.group(2)
        rest_word = m.group(3)
        full_word = first_letter + rest_word

        if full_word in PROPER_NOUNS:
            return m.group(0)

        lowered = first_letter.lower()
        if highlight:
            return f'{prefix} \x02HL:colon\x02{lowered}\x03{rest_word}'
        return f'{prefix} {lowered}{rest_word}'

    pattern = re.compile(r'(:\*{0,2})\s+([А-ЯЁІЇЄҐA-Z])([а-яёіїєґa-z]+)')
    return pattern.sub(fix_match, text)

def apply_text_transformations(text, smart_quotes=False, replace_dash=False, replace_apostrophe=False, lowercase_colon=False, 
                              remove_emojis=False, custom_replacements=None, highlight=False):
    math_placeholders = []
    def stash_math(m):
        idx = len(math_placeholders)
        math_placeholders.append(m.group(0))
        return f"\x00MATH_{idx}\x00"

    s = re.sub(r'\$\$[\s\S]*?\$\$', stash_math, text)
    s = re.sub(r'\$[^\$\n]+?\$', stash_math, s)

    if remove_emojis:
        s = remove_emojis_smart(s, highlight=highlight)

    if smart_quotes:
        s = replace_smart_quotes(s, highlight=highlight)

    if replace_dash:
        rep = '\x02HL:dash\x02–\x03' if highlight else '–'
        s = s.replace('—', rep)

    if replace_apostrophe:
        rep = '\x02HL:dash\x02’\x03' if highlight else '’'
        s = s.replace("'", rep)

    if lowercase_colon:
        s = smart_lowercase_after_colon(s, highlight=highlight)

    s = s.replace('`', '')

    if custom_replacements:
        for item in custom_replacements:
            find_str = item.get('find', '')
            replace_str = item.get('replace', '')
            if find_str:
                rep = f'\x02HL:custom\x02{replace_str}\x03' if highlight else replace_str
                s = s.replace(find_str, rep)

    if highlight:
        s = re.sub(r'\x02HL:([a-z]+)\x02([\s\S]*?)\x03', r'<mark data-hl="\1">\2</mark>', s)
    else:
        s = re.sub(r'\x02HL:[a-z]+\x02([\s\S]*?)\x03', r'\1', s)

    for idx, math_chunk in enumerate(math_placeholders):
        s = s.replace(f"\x00MATH_{idx}\x00", math_chunk)

    return s

def get_spectrum_regex(pattern_str):
    if not pattern_str:
        return None
    s = pattern_str.strip()
    if not s:
        return None
    try:
        if s.startswith('[') and s.endswith(']'):
            inner = s[1:-1]
            return re.compile(f'([{inner}]+)')
        else:
            return re.compile(f'([{s}]+)')
    except re.error:
        return None

def _split_text_by_spectrum(text, is_bold, is_italic, spectrum_regex, current_hl=None):
    if not text:
        return []
    if is_italic or not spectrum_regex:
        return [("text", text, is_bold, is_italic, current_hl)]

    parts = spectrum_regex.split(text)
    out = []
    for part in parts:
        if not part:
            continue
        is_match = bool(spectrum_regex.fullmatch(part))
        hl = current_hl or ('italic' if is_match else None)
        out.append(("text", part, is_bold, is_match or is_italic, hl))
    return out
