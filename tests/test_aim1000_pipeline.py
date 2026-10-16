import unittest

from aim1000_pipeline import html_text


class PipelineTests(unittest.TestCase):
    def test_dashboard_text_escapes_html(self):
        self.assertEqual(html_text("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_dashboard_text_escapes_quotes(self):
        self.assertEqual(html_text('x" onmouseover="alert(1)'), "x&quot; onmouseover=&quot;alert(1)")


if __name__ == "__main__":
    unittest.main()
