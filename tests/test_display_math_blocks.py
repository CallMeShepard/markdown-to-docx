import unittest

from docx import Document

from core.converter import convert_text_to_docx
from core.docx_builder import init_document_styles


class DisplayMathBlockTests(unittest.TestCase):

    def test_inline_math_at_start_of_line_does_not_swallow_document(self):
        raw_text = (
            "Some text.\n"
            "$X(t) = X(t - \\Delta t)$ (2.9)\n"
            "Following text.\n"
        )
        doc = Document()
        init_document_styles(doc)
        convert_text_to_docx(raw_text, doc)
        
        paragraph_texts = [p.text for p in doc.paragraphs]
        self.assertIn("Some text.", paragraph_texts)
        self.assertTrue(any("(2.9)" in p.text for p in doc.paragraphs))
        self.assertIn("Following text.", paragraph_texts)

    def test_inline_math_at_start_of_line_does_not_swallow_document(self):
        raw_text = (
            "Some text.\n"
            "$X(t) = X(t - \\Delta t)$ (2.9)\n"
            "Following text.\n"
        )
        doc = Document()
        init_document_styles(doc)
        convert_text_to_docx(raw_text, doc)
        
        paragraph_texts = [paragraph.text for paragraph in doc.paragraphs]
        self.assertIn("Some text.", paragraph_texts)
        self.assertTrue(any("(2.9)" in p for p in paragraph_texts))
        self.assertIn("Following text.", paragraph_texts)

    def test_display_math_formats_preserve_following_content(self):
        formula = r"J = \min_{\theta \in \Theta} \frac{\bar{Q}_{out} + \alpha \cdot \vec{u}^{2}}{1 + \frac{\mu_1}{\mu_2}} \le \epsilon"

        test_cases = {
            "multiline": f"$$\n{formula}\n$$",
            "single_line": f"$${formula}$$"
        }

        for math_format, math_block in test_cases.items():
            with self.subTest(math_format=math_format):
                raw_text = (
                    "## Mathematical Expressions\n\n"
                    f"{math_block}\n\n"
                    "## Following Section\n"
                    "This paragraph must remain in the document.\n"
                )

                doc = Document()
                init_document_styles(doc)
                convert_text_to_docx(raw_text, doc)

                paragraph_texts = [paragraph.text for paragraph in doc.paragraphs]

                self.assertIn("Mathematical Expressions", paragraph_texts)
                self.assertIn("Following Section", paragraph_texts)
                self.assertIn(
                    "This paragraph must remain in the document.",
                    paragraph_texts
                )
                self.assertTrue(
                    any("m:oMath" in paragraph._p.xml for paragraph in doc.paragraphs)
                )


if __name__ == "__main__":
    unittest.main()
