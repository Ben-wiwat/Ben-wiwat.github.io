import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import update_scholar


ANSWERS = ["2,000", "25", "50", "2016", "9, 0, 0, 0, 0, 0, 0, 80, 170, 200"]
METRICS = {"citations": 2000, "h-index": 25, "i10-index": 50}
YEARS = list(range(2016, 2026))
COUNTS = [9, 0, 0, 0, 0, 0, 0, 80, 170, 200]


class ScholarTests(unittest.TestCase):
    def test_reads_all_time_metrics_and_ten_annual_counts(self):
        with patch("builtins.input", side_effect=ANSWERS):
            self.assertEqual(update_scholar.read_stats(), (METRICS, YEARS, COUNTS))

    def test_rejects_invalid_input(self):
        invalid = (
            ["-1", *ANSWERS[1:]],
            [*ANSWERS[:3], "1899", ANSWERS[4]],
            [*ANSWERS[:4], "1, 2"],
            [*ANSWERS[:4], "1, 2, 3, 4, 5, 6, 7, 8, 9, -1"],
            ["1", *ANSWERS[1:]],
        )
        for answers in invalid:
            with self.subTest(answers=answers), patch("builtins.input", side_effect=answers):
                with self.assertRaises(ValueError):
                    update_scholar.read_stats()

    def test_update_changes_only_citation_metrics_and_chart(self):
        original = (
            '<td>Books</td><td>3</td>\r\n'
            '<td data-scholar="citations">1666</td>\r\n'
            '<td data-scholar="h-index">21</td>\r\n'
            '<td data-scholar="i10-index">41</td>\r\n'
            "labels: [\"2025\"], datasets: [{ label: 'Citations per year', "
            "backgroundColor: [], data: [104], }]\r\n"
        )
        expected = (
            '<td>Books</td><td>3</td>\r\n'
            '<td data-scholar="citations">2000</td>\r\n'
            '<td data-scholar="h-index">25</td>\r\n'
            '<td data-scholar="i10-index">50</td>\r\n'
            'labels: ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"], '
            "datasets: [{ label: 'Citations per year', backgroundColor: [], "
            "data: [9, 0, 0, 0, 0, 0, 0, 80, 170, 200], }]\r\n"
        )
        self.assertEqual(update_scholar.update_page(original, METRICS, YEARS, COUNTS), expected)
        self.assertEqual(update_scholar.update_page(expected, METRICS, YEARS, COUNTS), expected)

    def test_main_does_not_write_if_either_page_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "index.html"
            second = Path(directory) / "publications.html"
            source = update_scholar.PAGES[0].read_bytes().decode("utf-8")
            original = update_scholar.update_page(
                source, {"citations": 1, "h-index": 1, "i10-index": 1}, [2020], [1]
            ).encode("utf-8")
            first.write_bytes(original)
            second.write_text("invalid page", encoding="utf-8")
            with patch.object(update_scholar, "PAGES", (first, second)), \
                 patch("builtins.input", side_effect=ANSWERS):
                with self.assertRaises(ValueError):
                    update_scholar.main()
            self.assertEqual(first.read_bytes(), original)
            self.assertEqual(second.read_text(encoding="utf-8"), "invalid page")

    def test_main_rejects_invalid_input_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            pages = tuple(Path(directory) / page.name for page in update_scholar.PAGES)
            originals = [page.read_bytes() for page in update_scholar.PAGES]
            for page, content in zip(pages, originals):
                page.write_bytes(content)
            with patch.object(update_scholar, "PAGES", pages), \
                 patch("builtins.input", side_effect=[*ANSWERS[:4], "1, 2"]):
                with self.assertRaises(ValueError):
                    update_scholar.main()
            self.assertEqual([page.read_bytes() for page in pages], originals)

    def test_main_updates_both_pages_preserving_line_endings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            originals = [page.read_bytes() for page in update_scholar.PAGES]
            pages = tuple(Path(directory) / page.name for page in update_scholar.PAGES)
            for page, content in zip(pages, originals):
                page.write_bytes(content)
            with patch.object(update_scholar, "PAGES", pages), \
                 patch("builtins.input", side_effect=ANSWERS * 2):
                update_scholar.main()
                contents = [page.read_bytes() for page in pages]
                for original, content in zip(originals, contents):
                    self.assertIn(b'data-scholar="citations">2000', content)
                    self.assertIn(b"suggestedMax: 160", content)
                    if b"\r\n" in original:
                        self.assertNotIn(b"\n", content.replace(b"\r\n", b""))
                original_open = Path.open

                def read_only(path, *args, **kwargs):
                    if args and args[0] == "w":
                        raise AssertionError("Unexpected write for unchanged page")
                    return original_open(path, *args, **kwargs)

                with patch.object(Path, "open", read_only):
                    update_scholar.main()
                self.assertEqual(contents, [page.read_bytes() for page in pages])


if __name__ == "__main__":
    unittest.main()
