import unittest
import sys
from unittest.mock import MagicMock, patch
import os
import tempfile
import csv

# Ensure pdfplumber is mockable in test runner even if not installed locally
if "pdfplumber" not in sys.modules:
    sys.modules["pdfplumber"] = MagicMock()

import pdfplumber
from plumber import process, main


class TestPlumberParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_csv = os.path.join(self.temp_dir.name, "test_out.csv")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch.object(pdfplumber, "open")
    def test_domestic_transactions_total_calculation(self, mock_pdf_open):
        """Verify that multiple domestic rows do not sum quadratically and calculate correct dues."""
        mock_pdf = MagicMock()
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Page with 3 domestic transactions: 2 debits (1000.0, 500.0) and 1 credit (200.0)
        page1 = MagicMock()
        page1.extract_text.return_value = "Domestic Transactions Page"
        page1.extract_table.return_value = [
            ["Date", "Transaction Description", "Amount", "Reward Points"],
            ["01/09/2021", "AMAZON RETAIL", "1,000.00", "20"],
            ["02/09/2021", "SWIGGY BANGALORE", "500.00", "10"],
            ["03/09/2021", "CASHBACK REFUND", "200.00 Cr", "0"],
        ]
        mock_pdf.pages = [page1]

        res = process("dummy.pdf", self.output_csv, None)

        # Expected total = 1000.0 + 500.0 + 0 (Cr ignored in domestic dues) = 1500.0
        # Under the old quadratic bug, total was 1000 + (1000+500) + (1000+500+0) = 4000.0!
        self.assertAlmostEqual(res["total_amount"], 1500.0)
        self.assertEqual(len(res["indian"]), 3)
        self.assertEqual(res["indian"][0]["amount"], "1000.00")
        self.assertEqual(res["indian"][0]["type"], "Dr")
        self.assertEqual(res["indian"][2]["type"], "Cr")

        # Verify CSV is written
        self.assertTrue(os.path.exists(self.output_csv))
        with open(self.output_csv, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 3)
            self.assertEqual(reader[0]["description"], "AMAZON RETAIL")

    @patch.object(pdfplumber, "open")
    def test_foreign_transactions_forex_calculation(self, mock_pdf_open):
        """Verify international transactions parse forex amount and calculate exchange rate safely."""
        mock_pdf = MagicMock()
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        page1 = MagicMock()
        page1.extract_text.return_value = "International Transactions Details"
        page1.extract_table.return_value = [
            ["Date", "Description", "Currency & Forex Amt", "INR Amount", "Points"],
            ["15/09/2021", "GITHUB SPONSOR", "USD 10.00", "830.00", "16"],
            ["16/09/2021", "REFUND GITHUB", "USD 5.00", "415.00 Cr", "0"],
        ]
        mock_pdf.pages = [page1]

        res = process("dummy.pdf", self.output_csv, None)

        self.assertEqual(len(res["foreign"]), 2)
        # 830.00 / 10.00 = 83.00
        self.assertEqual(res["foreign"][0]["forex_rate"], "83.00")
        self.assertEqual(res["foreign"][0]["currency"], "USD")
        self.assertEqual(res["foreign"][0]["forex_amount"], "10.00")
        # In foreign, credits deduct from total: 830.00 - 415.00 = 415.0
        self.assertAlmostEqual(res["total_amount"], 415.0)

    @patch.object(pdfplumber, "open")
    def test_resilience_to_none_text_and_empty_tables(self, mock_pdf_open):
        """Ensure None return values from extract_text() and extract_table() do not crash parser."""
        mock_pdf = MagicMock()
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        page_empty = MagicMock()
        page_empty.extract_text.return_value = None
        page_empty.extract_table.return_value = None

        page_domestic_no_table = MagicMock()
        page_domestic_no_table.extract_text.return_value = "Domestic Transactions without table"
        page_domestic_no_table.extract_table.return_value = None

        mock_pdf.pages = [page_empty, page_domestic_no_table]

        res = process("dummy.pdf", self.output_csv, None)
        self.assertEqual(res["total_amount"], 0.0)
        self.assertEqual(len(res["combined"]), 0)

    def test_main_creates_output_directory(self):
        """Verify main() creates output directory when it does not exist."""
        in_dir = os.path.join(self.temp_dir.name, "inputs")
        out_dir = os.path.join(self.temp_dir.name, "nested", "outputs")
        os.makedirs(in_dir)

        args = MagicMock()
        args.in_dir = in_dir
        args.out_dir = out_dir
        args.password = None

        # Call main with empty input dir
        main(args)
        self.assertTrue(os.path.isdir(out_dir))


if __name__ == "__main__":
    unittest.main()
