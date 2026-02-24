import unittest

import pdf_editor


class TestPageSelection(unittest.TestCase):
    def test_parse_mixed_selection(self):
        result = pdf_editor.parse_page_selection("1,3-4,6-", 8)
        self.assertEqual(result.indexes, [0, 2, 3, 5, 6, 7])

    def test_parse_open_start_range(self):
        result = pdf_editor.parse_page_selection("-3", 10)
        self.assertEqual(result.indexes, [0, 1, 2])

    def test_out_of_bounds_raises(self):
        with self.assertRaises(ValueError):
            pdf_editor.parse_page_selection("2,9", 5)


if __name__ == "__main__":
    unittest.main()
