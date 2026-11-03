let pyodideInstance = null;
let pyodideInitPromise = (async () => {
    try {
        pyodideInstance = await loadPyodide({
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/"
        });
        await pyodideInstance.loadPackage("micropip");
        await pyodideInstance.runPythonAsync(`
import micropip
await micropip.install(['python-docx'])
import os, sys
os.makedirs('/home/pyodide/core', exist_ok=True)
if '/home/pyodide' not in sys.path:
    sys.path.insert(0, '/home/pyodide')
        `);
        
        const files = ['__init__.py', 'config.py', 'converter.py', 'docx_builder.py', 'math_parser.py', 'typography.py'];
        for (const f of files) {
            const res = await fetch(`/core/${f}?_ts=${Date.now()}`, { cache: 'no-store' });
            if (res.ok) {
                const text = await res.text();
                pyodideInstance.FS.writeFile(`/home/pyodide/core/${f}`, text);
            } else {
                throw new Error(`Failed to load /core/${f}: status ${res.status}`);
            }
        }
        
        await pyodideInstance.runPythonAsync(`
import io
import re
from docx import Document
from core.converter import convert_text_to_docx
from core.docx_builder import init_document_styles
from core import math_parser
import pyodide.ffi

def generate_docx_bytes(raw_text, options_js):
    options = options_js.to_py()
    doc = Document()
    init_document_styles(doc)
    math_parser.ITALICIZE_MATH_FUNCTIONS = bool(
        options.get("italicize_math_functions", False)
    )
    
    convert_text_to_docx(
        raw_text,
        doc,
        smart_quotes=options.get("smart_quotes", False),
        italicize_spectrum=options.get("italicize_spectrum", False),
        italic_pattern=options.get("italic_pattern", "[A-Za-z]"),
        replace_dash=options.get("replace_dash", False),
        replace_apostrophe=options.get("replace_apostrophe", False),
        lowercase_colon=options.get("lowercase_after_colon", False),
        remove_emojis=options.get("remove_emojis", False),
        custom_replacements=list(options.get("custom_replacements", [])),
        highlight_word=options.get("highlight_word", False),
        math_tnr=options.get("math_tnr", False)
    )
    
    f = io.BytesIO()
    doc.save(f)
    f.seek(0)
    return pyodide.ffi.to_js(f.read())
        `);
    } catch (e) {
        console.error("Pyodide Init Error:", e);
        const overlayMsg = document.getElementById('initStatusMsg');
        if (overlayMsg) overlayMsg.innerText = "Failed to load Python Engine.";
        const overlayIcon = document.getElementById('initStatusIcon');
        if (overlayIcon) overlayIcon.className = "fa-solid fa-triangle-exclamation text-rose-600";
        const overlayBar = document.querySelector('#init-overlay .bg-indigo-600');
        if (overlayBar) overlayBar.className = "bg-rose-500 h-full w-full";
    } finally {
        const overlay = document.getElementById('init-overlay');
        if (overlay) {
            setTimeout(() => {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.remove(), 500);
            }, 200);
        }
    }
})();

const sampleText = String.raw`# Markdown to DOCX — Feature Demo

Тестування **жирного тексту**, *курсиву* та автоматичного виділення латинських назв Pyodide і OMML. Лапки: "Документ із "вкладеною цитатою"". Об'єкт — параметр 🚀.

Примітка: Результат має зберігати зміст і структуру. Назва рушія: Python.

Inline math: $E = mc^2$, $Q_{in}$, $\sum_{i=1}^{n} x_i$, $\ln(x)$, $35 ^\circ C$.

## Mathematical Expressions

$$
\min_{\theta \in \Theta} \sum_{i=1}^{n} \sum_{j=1}^{m} \left( \frac{w_{ij} \cdot \left( y_{ij} - \bar{y}_i \right)^2}{\sigma_{ij}^2 + \lambda \cdot \prod_{k=1}^{p} \left( 1 - \rho_k \right)} \right) + \ln \left( \sum_{s=1}^{K} \alpha_s \cdot e^{-\frac{\Delta_s^2}{2 \sigma_0^2}} \right) \le \epsilon_{доп}
$$

## Structured Data

| Показник | Значення | Одиниця |
| :--- | :---: | ---: |
| Витрата | $1{,}66$ | л/хв |
| Температура | $35 ^\circ C$ | °C |
| Ефективність | $\eta = 0{,}98$ | % |

## Conversion Workflow

- **Live Preview:** відображення Markdown, формул і підсвічування змін.
- **Native DOCX:** редаговані формули OMML, таблиці та списки Word.

1. Перевірити результат автоматичної обробки.
2. Експортувати готовий документ у форматі DOCX.

Користувацька заміна: CUSTOM_TAG.

---
`;

let customRules = window.APP_CONFIG.custom_replacements || [];
const properNounsSet = new Set(['Україна', 'Украина', 'Київ', 'Киев', 'Харків', 'Харьков', 'Львів', 'Львов', 'Одеса', 'Одесса', 'Дніпро', 'Днепр', 'Європа', 'Европа', 'США', 'НАТО', 'Microsoft', 'Google', 'Apple', 'Linux', 'Windows', 'Python', 'Шевченко', 'Франко', 'Леся', 'Ньютон', 'Ейнштейн', 'Гаусс']);

const EMOJI_REGEX_JS = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2702}-\u{27B0}\u{24C2}-\u{1F251}\u{2300}-\u{23FF}\u{2600}-\u{26FF}\u{FE0E}\u{FE0F}\u{200D}]+/gu;

const editor = document.getElementById('editor');
const preview = document.getElementById('preview');
const smartQuotesToggle = document.getElementById('smartQuotesToggle');
const italicToggle = document.getElementById('italicToggle');
const italicPattern = document.getElementById('italicPattern');
const replaceDashToggle = document.getElementById('replaceDashToggle');
const replaceApostropheToggle = document.getElementById('replaceApostropheToggle');
const lowercaseColonToggle = document.getElementById('lowercaseColonToggle');
const removeEmojisToggle = document.getElementById('removeEmojisToggle');
const mathTnrToggle = document.getElementById('mathTnrToggle');
const italicizeMathFunctionsToggle = document.getElementById('italicizeMathFunctionsToggle');
const highlightPreviewToggle = document.getElementById('highlightPreviewToggle');
const highlightWordToggle = document.getElementById('highlightWordToggle');
const previewMarkerBadge = document.getElementById('previewMarkerBadge');
const convertForm = document.getElementById('convertForm');

const SETTINGS_STORAGE_KEY = 'markdown-to-docx.settings.v1';
const ZOOM_STORAGE_KEY = 'markdown-to-docx.zoom.v1';

const ZOOM_MIN = 0.6;
const ZOOM_MAX = 2.0;
const ZOOM_DEFAULT = 1.0;
let zoomState = { editor: 1.0, preview: 1.0 };

function applyZoom(target, zoomValue, save = true) {
    zoomValue = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(zoomValue * 100) / 100));
    zoomState[target] = zoomValue;

    const element = target === 'editor' ? document.getElementById('editor') : document.getElementById('preview');
    const label = document.getElementById(target + 'ZoomLabel');

    if (element) {
        element.style.zoom = zoomValue;
    }
    if (label) {
        label.textContent = Math.round(zoomValue * 100) + '%';
        label.classList.toggle('text-indigo-600', zoomValue !== 1.0);
        label.classList.toggle('text-slate-400', zoomValue === 1.0);
        label.classList.toggle('font-bold', zoomValue !== 1.0);
    }

    if (save) {
        try {
            localStorage.setItem(ZOOM_STORAGE_KEY, JSON.stringify(zoomState));
        } catch (e) {
            console.warn('Unable to persist zoom state:', e);
        }
    }
    
    if (typeof updateSelectionHighlight === 'function') {
        updateSelectionHighlight();
    }
}

function resetZoom(target) {
    applyZoom(target, ZOOM_DEFAULT);
}
window.resetZoom = resetZoom;

function initZoomHandlers() {
    try {
        const saved = JSON.parse(localStorage.getItem(ZOOM_STORAGE_KEY) || '{}');
        if (typeof saved.editor === 'number') zoomState.editor = saved.editor;
        if (typeof saved.preview === 'number') zoomState.preview = saved.preview;
    } catch (e) {
        console.warn('Unable to restore zoom state:', e);
    }

    applyZoom('editor', zoomState.editor, false);
    applyZoom('preview', zoomState.preview, false);

    // Intercept Ctrl + Wheel at window level to unconditionally suppress native browser tab zoom
    window.addEventListener('wheel', (e) => {
        if (!e.ctrlKey) return;

        const editorEl = document.getElementById('editor');
        const previewContainer = document.getElementById('preview-container');

        const isOverEditor = editorEl && (e.target === editorEl || editorEl.contains(e.target));
        const isOverPreview = previewContainer && (e.target === previewContainer || previewContainer.contains(e.target));

        if (isOverEditor || isOverPreview) {
            e.preventDefault();
            e.stopPropagation();

            const target = isOverEditor ? 'editor' : 'preview';
            const delta = -Math.sign(e.deltaY) * 0.05;
            applyZoom(target, zoomState[target] + delta);
        }
    }, { passive: false });
}

function getPersistedSettingControls() {
    return Array.from(document.querySelectorAll('input[id], select[id], textarea[id]'))
        .filter(control =>
            control.id !== 'editor' &&
            !control.closest('#customRulesContainer') &&
            !['button', 'submit', 'reset', 'file'].includes(control.type)
        );
}

function saveSettingsToStorage() {
    try {
        const controls = {};
        getPersistedSettingControls().forEach(control => {
            controls[control.id] = control.type === 'checkbox' || control.type === 'radio'
                ? control.checked
                : control.value;
        });

        const savedRules = customRules.map(rule => ({
            find: typeof rule.find === 'string' ? rule.find : '',
            replace: typeof rule.replace === 'string' ? rule.replace : ''
        }));

        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify({
            controls,
            customRules: savedRules
        }));
    } catch (error) {
        console.warn('Unable to save settings to browser storage:', error);
    }
}

function loadSettingsFromStorage() {
    try {
        const rawSettings = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (!rawSettings) return;

        const savedSettings = JSON.parse(rawSettings);
        if (!savedSettings || typeof savedSettings !== 'object') return;

        const controls = new Map(getPersistedSettingControls().map(control => [control.id, control]));
        if (savedSettings.controls && typeof savedSettings.controls === 'object') {
            Object.entries(savedSettings.controls).forEach(([id, value]) => {
                const control = controls.get(id);
                if (!control) return;

                if (control.type === 'checkbox' || control.type === 'radio') {
                    if (typeof value === 'boolean') control.checked = value;
                } else if (typeof value === 'string' || typeof value === 'number') {
                    control.value = String(value);
                }
            });
        }

        if (Array.isArray(savedSettings.customRules)) {
            customRules = savedSettings.customRules
                .filter(rule => rule && typeof rule === 'object' && !Array.isArray(rule))
                .map(rule => ({
                    find: typeof rule.find === 'string' ? rule.find : '',
                    replace: typeof rule.replace === 'string' ? rule.replace : ''
                }));
        }
    } catch (error) {
        console.warn('Unable to restore settings from browser storage:', error);
    }
}

function resetCustomRules() {
    if (customRules.length === 0) return;
    if (!window.confirm('Remove all custom replacement rules?')) return;

    customRules = [];
    renderCustomRules();
    onSettingChange();
}

function toggleReplacementsDrawer() {
    const drawer = document.getElementById('replacementsDrawer');
    const chevron = document.getElementById('drawerChevron');
    drawer.classList.toggle('hidden');
    chevron.classList.toggle('rotate-180');
}

function renderCustomRules() {
    const container = document.getElementById('customRulesContainer');
    container.replaceChildren();

    customRules.forEach((rule, idx) => {
        const row = document.createElement('div');
        row.className = 'flex items-center gap-2';

        const findInput = document.createElement('input');
        findInput.type = 'text';
        findInput.value = typeof rule.find === 'string' ? rule.find : '';
        findInput.placeholder = 'Find';
        findInput.className = 'flex-1 px-2 py-1 text-xs border border-slate-300 focus:ring-1 focus:ring-indigo-500 focus:outline-none';
        findInput.addEventListener('input', () => updateCustomRule(idx, 'find', findInput.value));

        const separator = document.createElement('span');
        separator.className = 'text-slate-400 text-xs';
        separator.textContent = '→';

        const replaceInput = document.createElement('input');
        replaceInput.type = 'text';
        replaceInput.value = typeof rule.replace === 'string' ? rule.replace : '';
        replaceInput.placeholder = 'Replace with';
        replaceInput.className = 'flex-1 px-2 py-1 text-xs border border-slate-300 focus:ring-1 focus:ring-indigo-500 focus:outline-none';
        replaceInput.addEventListener('input', () => updateCustomRule(idx, 'replace', replaceInput.value));

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'text-rose-500 hover:text-rose-700 p-1 text-xs';
        removeButton.title = 'Remove rule';
        removeButton.setAttribute('aria-label', 'Remove rule');
        removeButton.addEventListener('click', () => removeCustomRule(idx));

        const removeIcon = document.createElement('i');
        removeIcon.className = 'fa-solid fa-xmark';
        removeButton.appendChild(removeIcon);

        row.append(findInput, separator, replaceInput, removeButton);
        container.appendChild(row);
    });
}

function addCustomRule() {
    customRules.push({ find: '', replace: '' });
    renderCustomRules();
    onSettingChange();
}

function removeCustomRule(idx) {
    customRules.splice(idx, 1);
    renderCustomRules();
    onSettingChange();
}

function updateCustomRule(idx, field, value) {
    customRules[idx][field] = value;
    onSettingChange();
}

function removeEmojisSmartJs(text, highlight) {
    let s = text.replace(EMOJI_REGEX_JS, highlight ? ' \x01EMOJI_SHIFT\x01 ' : ' ');

    s = s.replace(/[ \t]+([.,!?:;»\)])/g, '$1');
    s = s.replace(/^(#{1,6})[ \t]+/gm, '$1 ');
    s = s.replace(/^[ \t]+(?!\*|\-|\+|\d+\.)/gm, '');
    s = s.replace(/[ \t]+$/gm, '');
    s = s.replace(/[ \t]{2,}/g, ' ');

    if (highlight && s.includes('\x01EMOJI_SHIFT\x01')) {
        s = s.replace(/\x01EMOJI_SHIFT\x01\s*([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9]+)/g, (match, word) => {
            return `\x02HL:emoji\x02${word}\x03`;
        });
        s = s.replace(/([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9]+)\s*\x01EMOJI_SHIFT\x01\s*([.,!?:;»\)])/g, (match, word, punct) => {
            return `\x02HL:emoji\x02${word}\x03${punct}`;
        });
        s = s.replaceAll('\x01EMOJI_SHIFT\x01', '');
        s = s.replace(/[ \t]{2,}/g, ' ');
    }
    return s;
}

function replaceSmartQuotesJs(text, highlight) {
    const chars = text.split('');
    const n = chars.length;
    let i = 0;
    let nestingLevel = 0;

    const openingPreceders = new Set([' ', '\t', '\n', '\r', '(', '[', '{', '\'', '"', '-', '—', '–', '«', '„', '\x02', '\x03']);
    const closingFollowers = new Set([' ', '\t', '\n', '\r', '.', ',', ';', ':', '!', '?', ')', ']', '}', '\'', '"', '-', '—', '–', '»', '”', '\0', '\x02', '\x03']);

    while (i < n) {
        const ch = chars[i];
        if (ch === '"') {
            const prevCh = i > 0 ? chars[i - 1] : ' ';
            const nextCh = i + 1 < n ? chars[i + 1] : ' ';

            if (/\d/.test(prevCh) && (closingFollowers.has(nextCh) || nextCh === '')) {
                i++;
                continue;
            }

            const isOpening = openingPreceders.has(prevCh) && !closingFollowers.has(nextCh);
            const isClosing = !openingPreceders.has(prevCh) && (closingFollowers.has(nextCh) || openingPreceders.has(nextCh));

            let target = '«';
            if (isOpening) {
                target = (nestingLevel === 0) ? '«' : '„';
                nestingLevel = (nestingLevel === 0) ? 1 : 2;
            } else if (isClosing) {
                target = (nestingLevel >= 2) ? '“' : '»';
                nestingLevel = (nestingLevel >= 2) ? 1 : 0;
            } else {
                target = (nestingLevel === 0) ? '«' : '»';
                nestingLevel = (nestingLevel === 0) ? 1 : 0;
            }

            chars[i] = highlight ? `\x02HL:quote\x02${target}\x03` : target;
        } else if (ch === '\n' || ch === '\r') {
            nestingLevel = 0;
        }
        i++;
    }
    return chars.join('');
}

function smartLowercaseAfterColonJs(text, highlight) {
    return text.replace(/(:\*{0,2})\s+([А-ЯЁІЇЄҐA-Z])([а-яёіїєґa-z]+)/g, (match, prefix, firstLetter, restWord) => {
        const fullWord = firstLetter + restWord;
        if (properNounsSet.has(fullWord)) {
            return match;
        }
        const lowered = firstLetter.toLowerCase();
        if (highlight) {
            return `${prefix} \x02HL:colon\x02${lowered}\x03${restWord}`;
        }
        return `${prefix} ${lowered}${restWord}`;
    });
}

function preprocessMathForPreview(s) {
    if (!s) return s;
    s = s.replace(/(?:\\?\s*)\^\{?\\circ\}?(?:\\?\s*)(?:\\(?:text|mathrm|mathbf)\{([CСcс])\}|\{([CСcс])\}|([CСcс]))(?![a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ])/g, (m, c1, c2, c3) => ` ^{\\circ}\\text{${c1 || c2 || c3}}`);
    s = s.replace(/(?:\\?\s*)\\(?:degree|celsius)(?:\\?\s*)(?:\\(?:text|mathrm|mathbf)\{([CСcс])\}|\{([CСcс])\}|([CСcс]))?(?![a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ])/g, (m, c1, c2, c3) => {
        const c = c1 || c2 || c3;
        return c ? ` ^{\\circ}\\text{${c}}` : ' ^{\\circ}';
    });
    s = s.replace(/(?:\\?\s*)\\circ(?:\\?\s*)(?:\\(?:text|mathrm|mathbf)\{([CСcс])\}|\{([CСcс])\}|([CСcс]))(?![a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ])/g, (m, c1, c2, c3) => ` ^{\\circ}\\text{${c1 || c2 || c3}}`);
    s = s.replace(/(?:\\?\s*)\^\{?\\circ\}?/g, ' ^{\\circ}');
    return s;
}

function italicizeDomTextNodes(rootElement, spectrumStr, doHighlight) {
    if (!spectrumStr) return;
    let inner = spectrumStr.trim();
    if (inner.startsWith('[') && inner.endsWith(']')) {
        inner = inner.slice(1, -1);
    }
    if (!inner) return;

    let regex, testRegex;
    try {
        regex = new RegExp(`([${inner}]+)`, 'g');
        testRegex = new RegExp(`^[${inner}]+$`);
    } catch (e) {
        return;
    }

    const walker = document.createTreeWalker(
        rootElement,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode(node) {
                let p = node.parentElement;
                while (p && p !== rootElement) {
                    const tag = p.tagName ? p.tagName.toUpperCase() : '';
                    if (
                        tag === 'EM' || tag === 'I' || tag === 'CODE' || tag === 'PRE' ||
                        tag === 'MJX-CONTAINER' || tag === 'MATH' || tag.startsWith('MJX-') ||
                        (p.classList && (p.classList.contains('MathJax') || p.classList.contains('tex2jax_ignore'))) ||
                        p.hasAttribute('data-mjx-texclass')
                    ) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    p = p.parentElement;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );

    const textNodes = [];
    while (walker.nextNode()) {
        if (regex.test(walker.currentNode.nodeValue)) {
            textNodes.push(walker.currentNode);
        }
    }

    textNodes.forEach(node => {
        const parent = node.parentNode;
        if (!parent) return;
        const text = node.nodeValue;
        const parts = text.split(regex);
        const frag = document.createDocumentFragment();
        parts.forEach(part => {
            if (!part) return;
            if (testRegex.test(part)) {
                const em = document.createElement('em');
                em.className = 'italic font-serif';
                em.textContent = part;
                if (doHighlight) {
                    const mark = document.createElement('mark');
                    mark.setAttribute('data-hl', 'italic');
                    mark.appendChild(em);
                    frag.appendChild(mark);
                } else {
                    frag.appendChild(em);
                }
            } else {
                frag.appendChild(document.createTextNode(part));
            }
        });
        parent.replaceChild(frag, node);
    });
}

const previewHighlightStyles = {
    quote: { label: 'Quotation marks', background: '#fce7f3', line: '#f472b6' },
    dash: { label: 'Dash replacement', background: '#ccfbf1', line: '#5eead4' },
    colon: { label: 'Lowercase after colon', background: '#fef3c7', line: '#fcd34d' },
    custom: { label: 'Custom replacement', background: '#f3e8ff', line: '#d8b4fe' },
    emoji: { label: 'Emoji adjustment', background: '#e2e8f0', line: '#94a3b8' },
    italic: { label: 'Italicization', background: '#dcfce7', line: '#86efac' }
};

function parseHighlightCharacters(text) {
    const markerRegex = /\x02HL:([a-z]+)\x02|\x03/g;
    const characters = [];
    const activeTypes = [];
    let lastIndex = 0;
    let match;

    const appendText = value => {
        for (let index = 0; index < value.length; index++) {
            characters.push({ value: value[index], types: activeTypes.slice() });
        }
    };

    while ((match = markerRegex.exec(text)) !== null) {
        appendText(text.slice(lastIndex, match.index));
        if (match[1]) {
            activeTypes.push(match[1]);
        } else if (activeTypes.length > 0) {
            activeTypes.pop();
        }
        lastIndex = markerRegex.lastIndex;
    }

    appendText(text.slice(lastIndex));
    return characters;
}

function encodeHighlightCharacters(characters) {
    const knownOrder = Object.keys(previewHighlightStyles);
    let activeTypes = [];
    let result = '';

    characters.forEach(character => {
        const nextTypes = Array.from(new Set(character.types)).sort((a, b) => {
            const aIndex = knownOrder.indexOf(a);
            const bIndex = knownOrder.indexOf(b);
            return (aIndex < 0 ? knownOrder.length : aIndex) - (bIndex < 0 ? knownOrder.length : bIndex);
        });

        let commonLength = 0;
        while (
            commonLength < activeTypes.length &&
            commonLength < nextTypes.length &&
            activeTypes[commonLength] === nextTypes[commonLength]
        ) {
            commonLength++;
        }

        result += '\x03'.repeat(activeTypes.length - commonLength);
        for (let index = commonLength; index < nextTypes.length; index++) {
            result += `\x02HL:${nextTypes[index]}\x02`;
        }
        result += character.value;
        activeTypes = nextTypes;
    });

    result += '\x03'.repeat(activeTypes.length);
    return result;
}

function applyCustomRulesWithHighlights(text, rules, enabled) {
    if (!Array.isArray(rules) || rules.length === 0) return text;

    if (!enabled) {
        rules.forEach(rule => {
            const find = String(rule.find || '');
            if (find) text = text.split(find).join(String(rule.replace || ''));
        });
        return text;
    }

    let characters = parseHighlightCharacters(text);

    rules.forEach(rule => {
        const find = String(rule.find || '');
        if (!find) return;

        const replacement = String(rule.replace || '');
        const visibleText = characters.map(character => character.value).join('');
        const nextCharacters = [];
        let cursor = 0;
        let matchIndex;

        while ((matchIndex = visibleText.indexOf(find, cursor)) !== -1) {
            nextCharacters.push(...characters.slice(cursor, matchIndex));
            const matchedCharacters = characters.slice(matchIndex, matchIndex + find.length);

            const replacementTypes = Array.from(
                { length: replacement.length },
                () => new Set()
            );
            for (let index = 0; index < replacement.length; index++) {
                const sourceIndex = Math.min(
                    matchedCharacters.length - 1,
                    Math.floor(index * matchedCharacters.length / replacement.length)
                );
                matchedCharacters[sourceIndex].types.forEach(type => replacementTypes[index].add(type));
            }
            matchedCharacters.forEach((character, sourceIndex) => {
                const targetIndex = Math.min(
                    replacement.length - 1,
                    Math.floor(sourceIndex * replacement.length / matchedCharacters.length)
                );
                if (targetIndex >= 0) {
                    character.types.forEach(type => replacementTypes[targetIndex].add(type));
                }
            });
            for (let index = 0; index < replacement.length; index++) {
                replacementTypes[index].add('custom');
                nextCharacters.push({ value: replacement[index], types: Array.from(replacementTypes[index]) });
            }

            cursor = matchIndex + find.length;
        }

        nextCharacters.push(...characters.slice(cursor));
        characters = nextCharacters;
    });

    return encodeHighlightCharacters(characters);
}

function renderHighlightMarkers(text, enabled) {
    const markerRegex = /\x02HL:([a-z]+)\x02|\x03/g;
    let html = '';
    let lastIndex = 0;
    let openMarkers = 0;
    let match;

    while ((match = markerRegex.exec(text)) !== null) {
        html += text.slice(lastIndex, match.index);

        if (match[1]) {
            if (enabled) html += `<mark data-hl="${match[1]}">`;
            openMarkers++;
        } else if (openMarkers > 0) {
            if (enabled) html += '</mark>';
            openMarkers--;
        }

        lastIndex = markerRegex.lastIndex;
    }

    html += text.slice(lastIndex);
    if (enabled && openMarkers > 0) {
        html += '</mark>'.repeat(openMarkers);
    }
    return html;
}

function combineOverlappingHighlights(rootElement) {
    const walker = document.createTreeWalker(rootElement, NodeFilter.SHOW_TEXT);
    const highlightedNodes = [];
    const ruleOrder = Object.keys(previewHighlightStyles);

    while (walker.nextNode()) {
        const activeTypes = new Set();
        let parent = walker.currentNode.parentElement;
        let insideMath = false;

        while (parent && parent !== rootElement) {
            if (parent.tagName === 'MARK' && parent.hasAttribute('data-hl')) {
                const types = parent.getAttribute('data-hl').split(/\s+/).filter(Boolean);
                if (types.includes('math')) {
                    insideMath = true;
                    break;
                }
                types.forEach(type => {
                    if (Object.prototype.hasOwnProperty.call(previewHighlightStyles, type)) {
                        activeTypes.add(type);
                    }
                });
            }
            parent = parent.parentElement;
        }

        if (!insideMath && activeTypes.size > 0) {
            highlightedNodes.push({ node: walker.currentNode, activeTypes });
        }
    }

    highlightedNodes.forEach(({ node, activeTypes }) => {
        if (!node.parentNode) return;

        const types = ruleOrder.filter(type => activeTypes.has(type));
        if (types.length === 0) return;

        const mark = document.createElement('mark');
        mark.setAttribute('data-hl', types.join(' '));
        mark.className = 'hl-final';
        mark.title = types.map(type => previewHighlightStyles[type].label).join(' + ');

        if (types.length > 1) {
            const stripeStops = types.map((type, index) => {
                const start = index * 6;
                const end = (index + 1) * 6;
                return `${previewHighlightStyles[type].background} ${start}px ${end}px`;
            }).join(', ');
            const lineStops = types.map((type, index) => {
                const start = index * 100 / types.length;
                const end = (index + 1) * 100 / types.length;
                return `${previewHighlightStyles[type].line} ${start}% ${end}%`;
            }).join(', ');

            mark.classList.add('hl-overlap');
            mark.style.setProperty('--hl-stripes', `repeating-linear-gradient(135deg, ${stripeStops})`);
            mark.style.setProperty('--hl-line', `linear-gradient(90deg, ${lineStops})`);
        }

        mark.textContent = node.nodeValue;
        node.parentNode.replaceChild(mark, node);
    });

    const sourceMarks = Array.from(rootElement.querySelectorAll('mark[data-hl]')).filter(mark => {
        const types = mark.getAttribute('data-hl').split(/\s+/).filter(Boolean);
        return !mark.classList.contains('hl-final') && !types.includes('math');
    });

    sourceMarks.forEach(mark => {
        const parent = mark.parentNode;
        if (!parent) return;
        while (mark.firstChild) {
            parent.insertBefore(mark.firstChild, mark);
        }
        parent.removeChild(mark);
    });
}

function normalizeMarkdownParagraphs(text) {
    if (!text) return text;
    const lines = text.split('\n');
    const result = [];
    let inMath = false;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        if (trimmed.startsWith('$') && trimmed.endsWith('$') && trimmed.length > 2) {
            // single-line math block
        } else if (trimmed.startsWith('$')) {
            inMath = true;
        } else if (trimmed.endsWith('$') && inMath) {
            inMath = false;
        }

        result.push(line);

        if (i < lines.length - 1 && !inMath) {
            const nextLine = lines[i + 1];
            const nextTrimmed = nextLine.trim();

            if (!trimmed || !nextTrimmed) continue;

            const isTable = trimmed.startsWith('|') && trimmed.endsWith('|');
            const nextIsTable = nextTrimmed.startsWith('|') && nextTrimmed.endsWith('|');
            if (isTable && nextIsTable) continue;

            const isList = /^\s*([*+-]|\d+\.)\s+/.test(line);
            const nextIsList = /^\s*([*+-]|\d+\.)\s+/.test(nextLine);
            const nextIsIndent = /^\s{2,}/.test(nextLine);
            if (isList && (nextIsList || nextIsIndent)) continue;

            result.push('');
        }
    }
    return result.join('\n');
}

function escapeHtml(value) {
    return value.replace(/[&<>"']/g, function(char) {
        switch (char) {
            case '&': return '&amp;';
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '"': return '&quot;';
            case "'": return '&#39;';
            default: return char;
        }
    });
}

function renderMarkdownAndMath(text) {
    text = normalizeMarkdownParagraphs(text);
    const doHighlight = highlightPreviewToggle && highlightPreviewToggle.checked;

    const blocks = [];
    let safeText = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, math) => {
        const id = `%%BLOCK_MATH_${blocks.length}%%`;
        blocks.push({ id, math: preprocessMathForPreview(math) });
        return id;
    });

    const inlines = [];
    safeText = safeText.replace(/\$((?:\\\$|[^$\n])+?)\$/g, (match, math) => {
        const id = `%%INLINE_MATH_${inlines.length}%%`;
        inlines.push({ id, math: preprocessMathForPreview(math) });
        return id;
    });

    if (removeEmojisToggle && removeEmojisToggle.checked) {
        safeText = removeEmojisSmartJs(safeText, doHighlight);
    }

    if (smartQuotesToggle && smartQuotesToggle.checked) {
        safeText = replaceSmartQuotesJs(safeText, doHighlight);
    }

    if (replaceDashToggle && replaceDashToggle.checked) {
        const rep = doHighlight ? '\x02HL:dash\x02–\x03' : '–';
        safeText = safeText.replace(/—/g, rep);
    }

    if (replaceApostropheToggle && replaceApostropheToggle.checked) {
        const rep = doHighlight ? '\x02HL:dash\x02’\x03' : '’';
        safeText = safeText.replace(/'/g, rep);
    }

    if (lowercaseColonToggle && lowercaseColonToggle.checked) {
        safeText = smartLowercaseAfterColonJs(safeText, doHighlight);
    }

    safeText = applyCustomRulesWithHighlights(safeText, customRules, doHighlight);

    safeText = renderHighlightMarkers(safeText, doHighlight);

    let html = marked.parse(safeText);
    html = DOMPurify.sanitize(html);

    const S_DOL = '$';
    const S_DDOL = '$$';

    if (doHighlight) {
        blocks.forEach(item => {
            html = html.replace(item.id, () => '<mark data-hl="math" class="block">' + S_DDOL + '\\phantom{}' + escapeHtml(item.math) + S_DDOL + '</mark>');
        });
        inlines.forEach(item => {
            html = html.replace(item.id, () => '<mark data-hl="math">' + S_DOL + escapeHtml(item.math) + S_DOL + '</mark>');
        });
    } else {
        blocks.forEach(item => {
            html = html.replace(item.id, () => S_DDOL + '\\phantom{}' + escapeHtml(item.math) + S_DDOL);
        });
        inlines.forEach(item => {
            html = html.replace(item.id, () => S_DOL + escapeHtml(item.math) + S_DOL);
        });
    }
    return html;
}

let renderSeq = 0;
let updateTimeout = null;

function updatePreview() {
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(() => {
        const currentSeq = ++renderSeq;
        const container = document.getElementById('preview-container');
        const preview = document.getElementById('preview');
        const doHighlight = highlightPreviewToggle && highlightPreviewToggle.checked;

        if (previewMarkerBadge) {
            previewMarkerBadge.classList.toggle('hidden', !doHighlight);
        }

        const staging = document.createElement('div');
        staging.className = preview.className;
        const containerWidth = preview.offsetWidth || 500;
        staging.style.cssText = `visibility:hidden; position:absolute; top:0; left:0; width:${containerWidth}px; pointer-events:none; z-index:-1000;`;
        staging.innerHTML = renderMarkdownAndMath(editor.value);
        container.appendChild(staging);

        if (window.MathJax) {
            MathJax.typesetPromise([staging]).then(() => {
                if (currentSeq !== renderSeq) {
                    staging.remove();
                    return;
                }
                if (italicToggle && italicToggle.checked) {
                    italicizeDomTextNodes(staging, italicPattern.value || '[A-Za-z]', doHighlight);
                }
                if (doHighlight) {
                    combineOverlappingHighlights(staging);
                }
                preview.innerHTML = staging.innerHTML;
                staging.remove();
                updateSelectionHighlight();
            }).catch((err) => {
                console.error('MathJax error:', err);
                if (currentSeq === renderSeq) {
                    if (doHighlight) {
                        combineOverlappingHighlights(staging);
                    }
                    preview.innerHTML = staging.innerHTML;
                    staging.remove();
                    updateSelectionHighlight();
                }
            });
        } else {
            if (italicToggle && italicToggle.checked) {
                italicizeDomTextNodes(staging, italicPattern.value || '[A-Za-z]', doHighlight);
            }
            if (doHighlight) {
                combineOverlappingHighlights(staging);
            }
            preview.innerHTML = staging.innerHTML;
            staging.remove();
            updateSelectionHighlight();
        }
    }, 60);
}

function loadSample() {
    editor.value = sampleText;
    updatePreview();
}

function clearText() { 
    editor.value = ''; 
    preview.innerHTML = ''; 
}

function onSettingChange() {
    saveSettingsToStorage();
    updatePreview();
}

let pollTimer = null;
let clientStart = 0;
let clientStopwatch = null;

function openProgressModal() {
    const modal = document.getElementById('progressModal');
    modal.classList.remove('hidden', 'fade-out');
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressBar').className = "bg-indigo-600 h-full transition-all duration-150 ease-out";
    document.getElementById('pctLabel').innerText = '0%';
    document.getElementById('pctLabel').className = "text-xl font-extrabold text-indigo-600 font-mono";
    document.getElementById('statusMsg').innerText = 'Processing document...';
    document.getElementById('statusIcon').className = "fa-solid fa-gear fa-spin text-indigo-600";
    document.getElementById('modalTitle').innerText = "Generating Word Document";
    document.getElementById('modalActions').classList.add('hidden');

    clientStart = performance.now();
    clientStopwatch = setInterval(() => {
        const el = (performance.now() - clientStart) / 1000;
        document.getElementById('elapsedVal').innerText = `${el.toFixed(1)} с`;
    }, 100);
}

function closeProgressModal() {
    clearInterval(clientStopwatch);
    clearInterval(pollTimer);
    const modal = document.getElementById('progressModal');
    if (modal) {
        modal.classList.add('fade-out');
        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('fade-out');
        }, 400);
    }
}

convertForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (editor.value.length > 50000) {
        alert("Input text exceeds the maximum allowed length of 50,000 characters.");
        return;
    }
    const textVal = editor.value.trim() || "### Document is empty\nPlease enter text.";
    
    const payload = {
        text: textVal,
        smart_quotes: smartQuotesToggle.checked,
        italicize_spectrum: italicToggle.checked,
        italic_pattern: italicPattern.value,
        replace_dash: replaceDashToggle.checked,
        replace_apostrophe: replaceApostropheToggle.checked,
        lowercase_colon: lowercaseColonToggle.checked,
        remove_emojis: removeEmojisToggle.checked,
        math_tnr: mathTnrToggle.checked,
        italicize_math_functions: italicizeMathFunctionsToggle.checked,
        highlight_preview: highlightPreviewToggle.checked,
        highlight_word: highlightWordToggle.checked,
        custom_replacements: customRules.filter(r => r.find && r.find.trim())
    };

    openProgressModal();
    document.getElementById('progressBar').style.width = '30%';
    document.getElementById('progressBar').classList.add('animate-pulse');
    document.getElementById('pctLabel').innerText = '...';

    try {
        await pyodideInitPromise;
        if (!pyodideInstance) throw new Error("Failed to load Python engine.");
        
        document.getElementById('progressBar').style.width = '70%';
        document.getElementById('statusMsg').innerText = 'Formatting and generating Word document...';
        
        // Yield execution to allow UI update
        await new Promise(resolve => setTimeout(resolve, 50));

        const generateDocxBytes = pyodideInstance.globals.get('generate_docx_bytes');
        if (typeof generateDocxBytes !== 'function') {
            throw new Error("Python function generate_docx_bytes is not defined.");
        }
        const uint8Array = generateDocxBytes(payload.text, payload);
        
        let filename = 'Converted_Document.docx';
        const firstLine = payload.text.trim().split('\n')[0];
        if (firstLine.startsWith('#')) {
            const cleanName = firstLine.replace(/[\\/*?:"<>|#]/g, "").trim();
            if (cleanName) filename = `${cleanName.substring(0, 50)}.docx`;
        }

        const blob = new Blob([uint8Array], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);

        clearInterval(clientStopwatch);
        document.getElementById('progressBar').classList.remove('animate-pulse');
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressBar').className = "bg-emerald-500 h-full transition-all duration-150 ease-out";
        document.getElementById('pctLabel').innerText = '100%';
        document.getElementById('pctLabel').className = "text-xl font-extrabold text-emerald-600 font-mono";
        document.getElementById('statusIcon').className = "fa-solid fa-circle-check text-emerald-500";
        document.getElementById('modalTitle').innerText = "Done!";
        document.getElementById('statusMsg').innerText = "Document generated locally!";

        setTimeout(() => { closeProgressModal(); }, 1500);

    } catch (startErr) {
        clearInterval(clientStopwatch);
        document.getElementById('progressBar').classList.remove('animate-pulse');
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressBar').className = "bg-rose-500 h-full";
        document.getElementById('statusIcon').className = "fa-solid fa-triangle-exclamation text-rose-500";
        document.getElementById('modalTitle').innerText = "Generation error";
        document.getElementById('statusMsg').innerText = startErr.message;
        document.getElementById('modalActions').classList.remove('hidden');
    }
});

function updateSelectionHighlight() {
    const overlay = document.getElementById('sync-highlight-overlay');
    const caret = document.getElementById('virtual-caret');
    if (!overlay || !caret || !editor || !preview) return;

    if (document.activeElement !== editor || editor.value.length === 0) {
        overlay.style.opacity = '0';
        caret.style.opacity = '0';
        caret.classList.remove('blinking');
        return;
    }

    const children = Array.from(preview.children);
    if (children.length === 0) {
        overlay.style.opacity = '0';
        caret.style.opacity = '0';
        return;
    }

    const text = editor.value;
    const selStart = editor.selectionStart;
    const selEnd = editor.selectionEnd;
    const isSelection = selStart !== selEnd;

    const previewContainer = document.getElementById('preview-container');
    const containerRect = previewContainer.getBoundingClientRect();

    function getRelativeRect(el) {
        const rect = el.getBoundingClientRect();
        return {
            top: rect.top - containerRect.top + previewContainer.scrollTop,
            left: rect.left - containerRect.left + previewContainer.scrollLeft,
            width: rect.width,
            height: rect.height,
            bottom: rect.bottom - containerRect.top + previewContainer.scrollTop,
            right: rect.right - containerRect.left + previewContainer.scrollLeft
        };
    }

    const lines = text.split('\n');
    const blocks = [];
    let offset = 0;
    let inMath = false;
    let inTable = false;
    let currentBlock = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        const lineStart = offset;
        const lineEnd = offset + line.length;
        offset = lineEnd + 1;

        if (inMath) {
            if (currentBlock) {
                currentBlock.end = lineEnd;
                currentBlock.raw += '\n' + line;
            }
            if (trimmed.endsWith('$$')) {
                inMath = false;
                currentBlock = null;
            }
            continue;
        }

        if (!trimmed) {
            inTable = false;
            currentBlock = null;
            continue;
        }

        if (trimmed.startsWith('$$') && trimmed.endsWith('$$') && trimmed.length > 2) {
            blocks.push({ start: lineStart, end: lineEnd, raw: line, type: 'math' });
            currentBlock = null;
            continue;
        } else if (trimmed.startsWith('$$')) {
            inMath = true;
            currentBlock = { start: lineStart, end: lineEnd, raw: line, type: 'math' };
            blocks.push(currentBlock);
            continue;
        }

        const isTableRow = trimmed.startsWith('|') && trimmed.endsWith('|');
        if (isTableRow) {
            if (inTable && currentBlock && currentBlock.type === 'table') {
                currentBlock.end = lineEnd;
                currentBlock.raw += '\n' + line;
            } else {
                inTable = true;
                currentBlock = { start: lineStart, end: lineEnd, raw: line, type: 'table' };
                blocks.push(currentBlock);
            }
            continue;
        } else {
            inTable = false;
        }

        const isList = /^\s*([*+-]|\d+\.)\s+/.test(line);
        if (isList) {
            if (currentBlock && currentBlock.type === 'list') {
                currentBlock.end = lineEnd;
                currentBlock.raw += '\n' + line;
            } else {
                currentBlock = { start: lineStart, end: lineEnd, raw: line, type: 'list' };
                blocks.push(currentBlock);
            }
            continue;
        }

        blocks.push({ start: lineStart, end: lineEnd, raw: line, type: trimmed.startsWith('#') ? 'heading' : 'paragraph' });
        currentBlock = null;
    }

    let startBlockIdx = -1;
    let endBlockIdx = -1;
    for (let i = 0; i < blocks.length; i++) {
        const b = blocks[i];
        if (startBlockIdx === -1 && selStart <= b.end) startBlockIdx = i;
        if (selEnd >= b.start) endBlockIdx = i;
    }

    if (startBlockIdx === -1) startBlockIdx = 0;
    if (endBlockIdx === -1) endBlockIdx = blocks.length - 1;
    startBlockIdx = Math.min(startBlockIdx, children.length - 1);
    endBlockIdx = Math.min(endBlockIdx, children.length - 1);

    const startEl = children[startBlockIdx];
    const endEl = children[endBlockIdx];
    if (!startEl || !endEl) return;

    if (isSelection) {
        caret.style.opacity = '0';
        caret.classList.remove('blinking');
        
        const startRect = getRelativeRect(startEl);
        const endRect = getRelativeRect(endEl);

        overlay.className = 'selection-mode';
        overlay.style.top = `${startRect.top - 6}px`;
        overlay.style.left = '8px';
        overlay.style.width = `calc(100% - 16px)`;
        overlay.style.height = `${endRect.bottom - startRect.top + 12}px`;
        overlay.style.opacity = '1';
        return;
    }

    const block = blocks[startBlockIdx];
    const cursorOffsetInBlock = selStart - block.start;

    const combinedMathRegex = /\$\$[\s\S]*?\$\$|\$((?:\\\$|[^$\n])+?)\$/g;
    let match;
    let mathIndex = -1;
    let mathCount = 0;

    while ((match = combinedMathRegex.exec(block.raw)) !== null) {
        if (cursorOffsetInBlock >= match.index && cursorOffsetInBlock <= match.index + match[0].length) {
            mathIndex = mathCount;
            break;
        }
        mathCount++;
    }

    if (mathIndex !== -1) {
        let targetMath = startEl.querySelectorAll('mjx-container')[mathIndex];
        if (targetMath) {
            if (targetMath.parentElement && targetMath.parentElement.tagName === 'MARK') {
                targetMath = targetMath.parentElement;
            }
            caret.style.opacity = '0';
            caret.classList.remove('blinking');
            const rect = getRelativeRect(targetMath);
            overlay.className = 'math-mode';
            overlay.style.top = `${rect.top - 4}px`;
            overlay.style.left = `${rect.left - 4}px`;
            overlay.style.width = `${rect.width + 8}px`;
            overlay.style.height = `${rect.height + 8}px`;
            overlay.style.opacity = '1';
            return;
        }
    }

    if (block.type === 'table') {
        const lines = block.raw.split('\n');
        let charCount = 0;
        let inAlignRow = false;
        for (let i = 0; i < lines.length; i++) {
            const lineLen = lines[i].length + 1;
            if (cursorOffsetInBlock >= charCount && cursorOffsetInBlock < charCount + lineLen) {
                if (i === 1 && lines[i].match(/^\|?[\s:-]+\|/)) {
                    inAlignRow = true;
                }
                break;
            }
            charCount += lineLen;
        }
        if (inAlignRow) {
            caret.style.opacity = '0';
            caret.classList.remove('blinking');
            const rect = getRelativeRect(startEl);
            overlay.className = 'cursor-mode';
            overlay.style.top = `${rect.top - 4}px`;
            overlay.style.left = `${rect.left - 4}px`;
            overlay.style.width = `${rect.width + 8}px`;
            overlay.style.height = `${rect.height + 8}px`;
            overlay.style.opacity = '1';
            return;
        }
    }

    overlay.style.opacity = '0';
    
    const marker = '\x01';
    let rawWithMarker = block.raw.slice(0, cursorOffsetInBlock) + marker + block.raw.slice(cursorOffsetInBlock);
    
    rawWithMarker = rawWithMarker.replace(/\$\$[\s\S]*?\$\$|\$((?:\\\$|[^$\n])+?)\$/g, '');
    
    const tempHtml = renderMarkdownAndMath(rawWithMarker);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = tempHtml;
    
    tempDiv.querySelectorAll('mark[data-hl="math"]').forEach(n => n.remove());
    
    const targetTextOffset = tempDiv.textContent.indexOf(marker);
    if (targetTextOffset === -1) {
        caret.style.opacity = '0';
        return;
    }

    let currentLen = 0;
    let targetNode = null;
    let targetOffset = 0;

    const walker = document.createTreeWalker(startEl, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
            let p = node.parentElement;
            while(p && p !== startEl) {
                if (p.tagName === 'MARK' && p.getAttribute('data-hl') === 'math') return NodeFilter.FILTER_REJECT;
                if (p.tagName === 'MJX-CONTAINER') return NodeFilter.FILTER_REJECT;
                if (p.classList && p.classList.contains('MathJax_Display')) return NodeFilter.FILTER_REJECT;
                p = p.parentElement;
            }
            return NodeFilter.FILTER_ACCEPT;
        }
    });

    let n;
    while ((n = walker.nextNode())) {
        const len = n.nodeValue.length;
        if (currentLen + len >= targetTextOffset) {
            targetNode = n;
            targetOffset = targetTextOffset - currentLen;
            break;
        }
        currentLen += len;
    }

    if (targetNode) {
        const range = document.createRange();
        try {
            range.setStart(targetNode, targetOffset);
            range.setEnd(targetNode, targetOffset);
        } catch (e) {
            range.selectNodeContents(targetNode);
            range.collapse(false);
        }

        const rects = range.getClientRects();
        let rect = rects.length > 0 ? rects[0] : null;

        if (!rect && targetNode.parentElement) {
            rect = targetNode.parentElement.getBoundingClientRect();
        }

        if (rect) {
            const top = rect.top - containerRect.top + previewContainer.scrollTop;
            const left = rect.left - containerRect.left + previewContainer.scrollLeft;

            caret.style.top = `${top}px`;
            caret.style.left = `${left}px`;
            caret.style.height = `${rect.height || 18}px`;
            caret.style.opacity = '1';
            
            caret.classList.remove('blinking');
            void caret.offsetWidth;
            caret.classList.add('blinking');
        }
    } else {
        caret.style.opacity = '0';
    }
}

document.addEventListener('selectionchange', () => {
    if (document.activeElement === editor) {
        updateSelectionHighlight();
    } else {
        const overlay = document.getElementById('sync-highlight-overlay');
        if (overlay) overlay.style.opacity = '0';
    }
});

editor.addEventListener('blur', () => {
    const overlay = document.getElementById('sync-highlight-overlay');
    const caret = document.getElementById('virtual-caret');
    if (overlay) overlay.style.opacity = '0';
    if (caret) {
        caret.style.opacity = '0';
        caret.classList.remove('blinking');
    }
});

editor.addEventListener('focus', updateSelectionHighlight);

document.addEventListener('pointerdown', (e) => {
    if (e.target !== editor) {
        const overlay = document.getElementById('sync-highlight-overlay');
        const caret = document.getElementById('virtual-caret');
        if (overlay) overlay.style.opacity = '0';
        if (caret) {
            caret.style.opacity = '0';
            caret.classList.remove('blinking');
        }
    }
});

function initEventListeners() {
    const settingToggles = [
        smartQuotesToggle, italicToggle, replaceDashToggle,
        replaceApostropheToggle, lowercaseColonToggle, removeEmojisToggle,
        mathTnrToggle, italicizeMathFunctionsToggle, highlightPreviewToggle,
        highlightWordToggle
    ];
    settingToggles.forEach(toggle => {
        if (toggle) toggle.addEventListener('change', onSettingChange);
    });

    if (italicPattern) {
        italicPattern.addEventListener('input', onSettingChange);
    }

    const toggleReplacementsBtn = document.getElementById('toggleReplacementsBtn');
    if (toggleReplacementsBtn) toggleReplacementsBtn.addEventListener('click', toggleReplacementsDrawer);

    const addCustomRuleBtn = document.getElementById('addCustomRuleBtn');
    if (addCustomRuleBtn) addCustomRuleBtn.addEventListener('click', addCustomRule);

    const resetCustomRulesBtn = document.getElementById('resetCustomRulesBtn');
    if (resetCustomRulesBtn) resetCustomRulesBtn.addEventListener('click', resetCustomRules);

    const closeProgressModalBtn = document.getElementById('closeProgressModalBtn');
    if (closeProgressModalBtn) closeProgressModalBtn.addEventListener('click', closeProgressModal);

    const loadSampleBtn = document.getElementById('loadSampleBtn');
    if (loadSampleBtn) loadSampleBtn.addEventListener('click', loadSample);

    const clearTextBtn = document.getElementById('clearTextBtn');
    if (clearTextBtn) clearTextBtn.addEventListener('click', clearText);

    const resetEditorZoomBtn = document.getElementById('resetEditorZoomBtn');
    if (resetEditorZoomBtn) resetEditorZoomBtn.addEventListener('click', () => resetZoom('editor'));

    const resetPreviewZoomBtn = document.getElementById('resetPreviewZoomBtn');
    if (resetPreviewZoomBtn) resetPreviewZoomBtn.addEventListener('click', () => resetZoom('preview'));
}

editor.addEventListener('input', updatePreview);
window.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadSettingsFromStorage();
    renderCustomRules();
    loadSample();
    initZoomHandlers();
});
