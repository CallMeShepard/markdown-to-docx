import unittest

from core import math_parser


class MathFunctionItalicsTests(unittest.TestCase):

    def tearDown(self):
        math_parser.ITALICIZE_MATH_FUNCTIONS = False

    def test_math_functions_are_upright_by_default(self):
        math_parser.ITALICIZE_MATH_FUNCTIONS = False

        tokens = math_parser.split_math_text_runs("min max ln sin x")

        function_tokens = [
            token for token in tokens
            if token[0].strip() in {"min", "max", "ln", "sin"}
        ]

        self.assertEqual(
            function_tokens,
            [
                ("min", False),
                ("max", False),
                ("ln", False),
                ("sin", False)
            ]
        )

    def test_math_functions_can_be_italicized(self):
        math_parser.ITALICIZE_MATH_FUNCTIONS = True

        tokens = math_parser.split_math_text_runs("min max ln sin x")

        function_tokens = [
            token for token in tokens
            if token[0].strip() in {"min", "max", "ln", "sin"}
        ]

        self.assertEqual(
            function_tokens,
            [
                ("min", True),
                ("max", True),
                ("ln", True),
                ("sin", True)
            ]
        )

    def test_variables_remain_italicized(self):
        math_parser.ITALICIZE_MATH_FUNCTIONS = True

        tokens = math_parser.split_math_text_runs("min x")

        variable_token = next(token for token in tokens if token[0] == "x")

        self.assertEqual(variable_token, ("x", True))


if __name__ == "__main__":
    unittest.main()
