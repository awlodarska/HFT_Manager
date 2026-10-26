"""Spreadsheet-safe downloads retain the original business records."""

from io import BytesIO
import unittest

import pandas as pd

from studio.orders_view import csv_export


class CsvExportTests(unittest.TestCase):
    def test_formula_prefixes_are_escaped_without_changing_source_or_unicode(self):
        names = ["=SUM(1,2)", "+cmd", "@foo", "-evil", "  \t=1+1", "Hafciarnia Żółć — Łódź"]
        source = pd.DataFrame({
            "client": names,
            "note": pd.Series(names, dtype="string"),
            "amount": [10.5, 20.0, 30.0, -99.0, 0.0, 123.45],
        })
        original = source.copy(deep=True)

        exported = csv_export(source)
        self.assertTrue(exported.startswith(b"\xef\xbb\xbf"))
        downloaded = pd.read_csv(BytesIO(exported), keep_default_na=False)
        expected = ["'" + name for name in names[:-1]] + [names[-1]]
        self.assertEqual(downloaded["client"].tolist(), expected)
        self.assertEqual(downloaded["note"].tolist(), expected)
        self.assertEqual(downloaded["amount"].tolist(), source["amount"].tolist())
        self.assertIn(names[-1], exported.decode("utf-8-sig"))
        pd.testing.assert_frame_equal(source, original)


if __name__ == "__main__":
    unittest.main()
