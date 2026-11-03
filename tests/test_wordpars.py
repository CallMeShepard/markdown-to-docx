import unittest
import time
from docx import Document
from docx.enum.text import WD_COLOR_INDEX, WD_ALIGN_PARAGRAPH
from core.math_parser import parse_math_to_list, parse_inline
from core.typography import replace_smart_quotes, smart_lowercase_after_colon, remove_emojis_smart, apply_text_transformations, get_spectrum_regex
from core.converter import convert_text_to_docx
from core.config import update_config_in_memory, APP_CONFIG
from core.docx_builder import init_document_styles

class WordParsTestSuite(unittest.TestCase):

    def test_celsius_and_degree_parsing(self):
        res1 = parse_math_to_list(r"t = 35 - 40 ^\circC")
        self.assertEqual(res1, ["t = 35 - 40 °C"])

        res2 = parse_math_to_list(r"t = 35 - 40 ^\circ C")
        self.assertEqual(res2, ["t = 35 - 40 °C"])

        res3 = parse_math_to_list(r"t = 35 - 40^{\circ}\text{C}")
        self.assertEqual(res3, ["t = 35 - 40 °C"])

        res4 = parse_math_to_list("t = 35 - 40 ^\\circС")
        self.assertEqual(res4, ["t = 35 - 40 °С"])

        res5 = parse_math_to_list(r"40 ^\circ")
        self.assertEqual(res5, ["40°"])

        res6 = parse_math_to_list(r"f \circ g")
        self.assertEqual(res6, ["f ∘ g"])

    def test_decimal_comma_and_grouping(self):
        res1 = parse_math_to_list(r"1{,}66\ \text{л/хв}")
        self.assertEqual(res1, ["1,66 л/хв"])

        res2 = parse_math_to_list(r"Q = 1{,}66")
        self.assertEqual(res2, ["Q = 1,66"])

        res3 = parse_math_to_list(r"\frac{1{,}66}{2}")
        self.assertEqual(res3, [("frac", ["1,66"], ["2"])])

        res4 = parse_math_to_list(r"\{1, 2\}")
        self.assertEqual(res4, ["{1, 2}"])

    def test_greek_and_symbols_expansion(self):
        raw = r"\min_{\theta \in \Theta} \le \epsilon_{доп} + \Phi + \omega + \tau"
        res = parse_math_to_list(raw)
        flat = str(res)
        self.assertIn("θ", flat)
        self.assertIn("Θ", flat)
        self.assertIn("ε", flat)
        self.assertIn("Φ", flat)
        self.assertIn("ω", flat)
        self.assertIn("τ", flat)

    def test_multi_level_nested_fractions(self):
        raw = r"\frac{a}{1 + \frac{\mu_{ст}}{\mu_ж} \cdot \left( \frac{\rho_1}{\rho_2} \right)}"
        res = parse_math_to_list(raw)
        self.assertEqual(res[0][0], "frac")

    def test_bar_with_subscripts(self):
        raw = r"\bar{L}_{крит} + \bar{T}_{ст} + \bar{q}_j"
        res = parse_math_to_list(raw)
        self.assertEqual(res[0][0], "sub")
        self.assertEqual(res[0][1], [("bar", ["L"])])
        self.assertEqual(res[2][0], "sub")
        self.assertEqual(res[2][1], [("bar", ["T"])])

    def test_vec_with_subscripts(self):
        raw = r"\vec{u}_{xy} + \vec g + \vec{u}^2"
        res = parse_math_to_list(raw)
        self.assertEqual(res[0][0], "sub")
        self.assertEqual(res[0][1], [("vec", ["u"])])
        self.assertEqual(res[1], " + ")
        self.assertEqual(res[2][0], "vec")
        self.assertEqual(res[2][1], ["g"])
        self.assertEqual(res[3], " + ")
        self.assertEqual(res[4][0], "sup")
        self.assertEqual(res[4][1], [("vec", ["u"])])

    def test_replace_apostrophe(self):
        t1 = "об'єкт та комп'ютер"
        res = apply_text_transformations(t1, replace_apostrophe=True)
        self.assertEqual(res, "об’єкт та комп’ютер")

        res_hl = apply_text_transformations(t1, replace_apostrophe=True, highlight=True)
        self.assertIn('<mark data-hl="dash">’</mark>', res_hl)

        math_text = "об'єкт $f'(x) = 1$ сім'я"
        res_math = apply_text_transformations(math_text, replace_apostrophe=True)
        self.assertEqual(res_math, "об’єкт $f'(x) = 1$ сім’я")

    def test_smart_quotes_replacement(self):
        text1 = 'Він сказав: "Це чудово".'
        self.assertEqual(replace_smart_quotes(text1), 'Він сказав: «Це чудово».')

        text2 = '"Система "Оберіг" у дії"'
        self.assertEqual(replace_smart_quotes(text2), '«Система „Оберіг“ у дії»')

        text3 = 'Текст "приклад" та формула $x = "test"$ плюс "кінець".'
        expected = 'Текст «приклад» та формула $x = "test"$ плюс «кінець».'
        self.assertEqual(replace_smart_quotes(text3), expected)

        text4 = 'Діагональ 27" та диск 3.5".'
        self.assertEqual(replace_smart_quotes(text4), 'Діагональ 27" та диск 3.5".')

    def test_smart_lowercase_after_colon(self):
        t1 = "**Спосіб #1:** Полягає у мінімізації витрат."
        self.assertEqual(smart_lowercase_after_colon(t1), "**Спосіб #1:** полягає у мінімізації витрат.")

        t2 = "Причина: Заключается в том, что..."
        self.assertEqual(smart_lowercase_after_colon(t2), "Причина: заключается в том, что...")

        t3 = "**Автор:** Шевченко написав твір."
        self.assertEqual(smart_lowercase_after_colon(t3), "**Автор:** Шевченко написав твір.")

        t4 = "Місце: Київ є столицею."
        self.assertEqual(smart_lowercase_after_colon(t4), "Місце: Київ є столицею.")

        t5 = "Сказав: «Сьогодні вихідний»."
        self.assertEqual(smart_lowercase_after_colon(t5), "Сказав: «Сьогодні вихідний».")

    def test_remove_emojis_smart(self):
        h1 = "### 🧮 БЛОК 1: ТЕСТ"
        self.assertEqual(remove_emojis_smart(h1), "### БЛОК 1: ТЕСТ")

        t1 = "Параметр 🚀 далі працює."
        self.assertEqual(remove_emojis_smart(t1), "Параметр далі працює.")

        t2 = "Успішне завершення 📊."
        self.assertEqual(remove_emojis_smart(t2), "Успішне завершення.")

        t3 = "Заголовок 🌟\nТекст"
        self.assertEqual(remove_emojis_smart(t3), "Заголовок\nТекст")

    def test_apply_text_transformations_and_highlights(self):
        raw = "### 🧮 Блок\n**Спосіб:** Полягає в $x = \"test\"$ — тут 🚀."
        
        hl_res = apply_text_transformations(
            raw,
            smart_quotes=True,
            replace_dash=True,
            lowercase_colon=True,
            remove_emojis=True,
            highlight=True
        )
        self.assertIn('<mark data-hl="dash">–</mark>', hl_res)
        self.assertIn('<mark data-hl="colon">п</mark>олягає', hl_res)
        self.assertIn('<mark data-hl="emoji">Блок</mark>', hl_res)
        self.assertNotIn('data-hl=«', hl_res)
        self.assertIn('$x = "test"$', hl_res)

        clean_res = apply_text_transformations(
            raw,
            smart_quotes=True,
            replace_dash=True,
            lowercase_colon=True,
            remove_emojis=True,
            highlight=False
        )
        self.assertNotIn('<mark', clean_res)
        self.assertIn('– тут.', clean_res)
        self.assertIn('### Блок', clean_res)

    def test_word_highlight_export(self):
        raw = "### 🧮 Блок 1\n**Спосіб:** Полягає в цьому — факт $E = mc^2$."
        doc = Document()
        init_document_styles(doc)
        convert_text_to_docx(
            raw,
            doc,
            replace_dash=True,
            lowercase_colon=True,
            remove_emojis=True,
            italicize_spectrum=True,
            italic_pattern="[A-Za-z]",
            highlight_word=True
        )
        runs_with_hl = [r for p in doc.paragraphs for r in p.runs if r.font.highlight_color is not None]
        self.assertTrue(len(runs_with_hl) > 0)

        dash_runs = [r for r in runs_with_hl if '–' in r.text]
        if dash_runs:
            self.assertEqual(dash_runs[0].font.highlight_color, WD_COLOR_INDEX.TEAL)

        fact_runs = [r for r in runs_with_hl if 'fact' in r.text]
        if fact_runs:
            self.assertEqual(fact_runs[0].font.highlight_color, WD_COLOR_INDEX.BRIGHT_GREEN)

    def test_math_tnr_mode_and_golden_standard_italics(self):
        raw = "Параметр $Q = 100\\ \\text{л/год}$, або $\\theta \\in \\Theta$, $\\min(x) + 35\\ ^\\circC$."
        doc = Document()
        init_document_styles(doc)
        convert_text_to_docx(raw, doc, math_tnr=True)
        
        xml = doc.paragraphs[0]._p.xml
        self.assertIn('w:ascii="Times New Roman"', xml)
        self.assertIn('m:nor', xml)
        
        # Q, θ, Θ, x must have italic <w:i/>
        self.assertIn('w:i', xml)
        self.assertIn('θ', xml)
        self.assertIn('Θ', xml)

    def test_native_word_lists(self):
        sample = (
            "* Пункт маркованого списку 1\n"
            "* Пункт маркованого списку 2\n"
            "1. Перший номер 1\n"
            "2. Другий номер 2\n"
        )
        doc = Document()
        init_document_styles(doc)
        convert_text_to_docx(sample, doc)
        
        # Bullet list uses native List Bullet style
        p_bullet = doc.paragraphs[0]
        self.assertIn('List Bullet', p_bullet.style.name)
        self.assertNotIn('•', p_bullet.text)
        
        # Numbered list uses native List Number style and OpenXML numPr
        p_num = doc.paragraphs[2]
        self.assertIn('List Number', p_num.style.name)
        self.assertNotIn('1.', p_num.text)
        self.assertIn('w:numPr', p_num._p.xml)

    def test_in_memory_config(self):
        update_config_in_memory({
            "remove_emojis": True,
            "highlight_preview": True,
            "highlight_word": True,
            "math_tnr": True
        })
        self.assertTrue(APP_CONFIG['remove_emojis'])
        self.assertTrue(APP_CONFIG['highlight_preview'])
        self.assertTrue(APP_CONFIG['highlight_word'])
        self.assertTrue(APP_CONFIG['math_tnr'])

        update_config_in_memory({
            "remove_emojis": False,
            "highlight_preview": True,
            "highlight_word": False,
            "math_tnr": False
        })

    def test_markdown_tables(self):
        raw = (
            "| Col 1 | Col 2 |\n"
            "| :--- | ---: |\n"
            "| **Bold** | $x = 1$ |\n"
        )
        doc = Document()
        init_document_styles(doc)
        convert_text_to_docx(raw, doc)
        
        self.assertEqual(len(doc.tables), 1)
        table = doc.tables[0]
        self.assertEqual(len(table.rows), 2)
        
        p_left = table.rows[0].cells[0].paragraphs[0]
        p_right = table.rows[0].cells[1].paragraphs[0]
        self.assertEqual(p_left.alignment, WD_ALIGN_PARAGRAPH.LEFT)
        self.assertEqual(p_right.alignment, WD_ALIGN_PARAGRAPH.RIGHT)
        
        p_math = table.rows[1].cells[1].paragraphs[0]
        self.assertIn('m:oMath', p_math._p.xml)

    # API tests removed due to pure serverless client-side architecture

if __name__ == '__main__':
    unittest.main()
