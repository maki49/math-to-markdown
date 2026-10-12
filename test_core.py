import unittest
from core import clean_latex, to_markdown

class MarkdownTests(unittest.TestCase):
    def test_math_delimiters_and_fences(self):
        for source in [r'\[x_1^2\]', r'\(x_1^2\)', '$x_1^2$', '$$x_1^2$$', '```latex\nx_1^2\n```']:
            self.assertEqual(to_markdown(source, '块公式'), '$$\nx_1^2\n$$')

    def test_multiline_structure_is_preserved(self):
        latex = r'\begin{aligned}a&=b\\c&=d\end{aligned}'
        self.assertEqual(to_markdown(latex, '块公式'), '$$\n' + latex + '\n$$')
        self.assertEqual(to_markdown(latex, '纯 LaTeX'), latex)

    def test_inline_and_empty(self):
        self.assertEqual(to_markdown('$$\nx+y\n$$', '行内公式'), '$x+y$')
        self.assertEqual(to_markdown('  ', '块公式'), '')

    def test_does_not_strip_latex_backslashes(self):
        self.assertEqual(clean_latex(r'\frac{1}{2}'), r'\frac{1}{2}')

if __name__ == '__main__':
    unittest.main()
