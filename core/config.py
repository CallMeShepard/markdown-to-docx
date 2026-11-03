import os
import sys
import re
from docx.enum.text import WD_COLOR_INDEX

# --- CONFIG_START ---
APP_CONFIG = {
    'smart_quotes': True,
    'italicize_spectrum': True,
    'italic_pattern': '[A-Za-z]',
    'replace_dash': True,
    'replace_apostrophe': True,
    'lowercase_after_colon': True,
    'remove_emojis': True,
    'highlight_preview': True,
    'highlight_word': False,
    'math_tnr': True,
    'custom_replacements': [],
}
# --- CONFIG_END ---

PROPER_NOUNS = {
    'Україна', 'Украина', 'Київ', 'Киев', 'Харків', 'Харьков', 'Львів', 'Львов',
    'Одеса', 'Одесса', 'Дніпро', 'Днепр', 'Європа', 'Европа', 'США', 'НАТО',
    'ЄС', 'ЕС', 'ООН', 'Microsoft', 'Google', 'Apple', 'Linux', 'Windows',
    'Ubuntu', 'Word', 'Excel', 'Python', 'Java', 'JavaScript', 'OpenAI',
    'Шевченко', 'Франко', 'Леся', 'Ньютон', 'Ейнштейн', 'Эйнштейн', 'Гаусс',
    'Ейлер', 'Эйлер', 'Паскаль', 'ДСТУ', 'ГОСТ', 'ISO', 'IEEE'
}

HL_COLOR_MAP = {
    'quote': WD_COLOR_INDEX.PINK,
    'dash': WD_COLOR_INDEX.TEAL,
    'colon': WD_COLOR_INDEX.YELLOW,
    'custom': WD_COLOR_INDEX.VIOLET,
    'emoji': WD_COLOR_INDEX.GRAY_25,
    'italic': WD_COLOR_INDEX.BRIGHT_GREEN,
    'math': WD_COLOR_INDEX.TURQUOISE,
}

MATH_FUNCS = {'min', 'max', 'ln', 'lg', 'log', 'exp', 'sin', 'cos', 'tan', 'ctg', 'tg', 'det', 'dim', 'lim'}

GREEK_CHARS = (
    'αβγδεζηθϑικλμνξπϖρϱσςτυφϕχψω'
    'ΓΔΘΛΞΠΣΥΦΨΩ'
)

def update_config_in_memory(new_settings):
    global APP_CONFIG
    APP_CONFIG.update(new_settings)
