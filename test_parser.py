"""
Unit tests for the biodata parser in run_match.py.

Run with:
    python -m unittest test_agent.py -v
    # or, if pytest is installed:
    pytest test_agent.py -v
"""

import os
import tempfile
import unittest

import run_match as rm


# ---------------------------------------------------------------------------
# Date of Birth parsing
# ---------------------------------------------------------------------------
class TestParseDob(unittest.TestCase):
    def test_day_monthname_year(self):
        self.assertEqual(rm.parse_dob("12 November 1993"),
                         {"day": 12, "month": 11, "year": 1993})

    def test_ordinal_suffix(self):
        self.assertEqual(rm.parse_dob("Birthdate : 3rd May 1997"),
                         {"day": 3, "month": 5, "year": 1997})

    def test_abbreviated_month(self):
        self.assertEqual(rm.parse_dob("Born 5 Sep 2000"),
                         {"day": 5, "month": 9, "year": 2000})

    def test_numeric_slash(self):
        self.assertEqual(rm.parse_dob("DOB: 12/11/1993"),
                         {"day": 12, "month": 11, "year": 1993})

    def test_numeric_dash(self):
        self.assertEqual(rm.parse_dob("07-12-1995"),
                         {"day": 7, "month": 12, "year": 1995})

    def test_missing_returns_none(self):
        self.assertIsNone(rm.parse_dob("No date here at all"))


# ---------------------------------------------------------------------------
# Time of Birth parsing
# ---------------------------------------------------------------------------
class TestParseTime(unittest.TestCase):
    def test_24h(self):
        self.assertEqual(rm.parse_time("08:45"), {"hour": 8, "minute": 45})

    def test_pm(self):
        self.assertEqual(rm.parse_time("09:43 pm"), {"hour": 21, "minute": 43})

    def test_am(self):
        self.assertEqual(rm.parse_time("2:16 AM"), {"hour": 2, "minute": 16})

    def test_noon_pm(self):
        self.assertEqual(rm.parse_time("12:48 PM"), {"hour": 12, "minute": 48})

    def test_midnight_am(self):
        self.assertEqual(rm.parse_time("12:05 AM"), {"hour": 0, "minute": 5})

    def test_labeled(self):
        self.assertEqual(rm.parse_time("Time Of Birth : 12:48 PM"),
                         {"hour": 12, "minute": 48})

    def test_missing_returns_none(self):
        self.assertIsNone(rm.parse_time("no time present"))


# ---------------------------------------------------------------------------
# Place of Birth parsing
# ---------------------------------------------------------------------------
class TestParsePlace(unittest.TestCase):
    def test_simple_label(self):
        self.assertEqual(rm.parse_place("Place of Birth: Denver"), "Denver")

    def test_birthplace_label(self):
        self.assertEqual(rm.parse_place("Birthplace: Austin, Texas"),
                         "Austin, Texas")

    def test_parenthetical_note_stripped(self):
        text = "Place Of Birth : Seattle (Resided in Denver since birth)"
        self.assertEqual(rm.parse_place(text), "Seattle")

    def test_unclosed_parenthesis_wrapped(self):
        # Simulates PDF line-wrapping inside a parenthetical
        text = "Place Of Birth : Seattle (Resided in"
        self.assertEqual(rm.parse_place(text), "Seattle")

    def test_missing_returns_none(self):
        self.assertIsNone(rm.parse_place("nothing relevant here"))


class TestCleanPlace(unittest.TestCase):
    def test_removes_parenthetical(self):
        self.assertEqual(rm._clean_place("Seattle (note)"), "Seattle")

    def test_trims_punctuation(self):
        self.assertEqual(rm._clean_place("  Denver, "), "Denver")


# ---------------------------------------------------------------------------
# Name parsing
# ---------------------------------------------------------------------------
class TestParseName(unittest.TestCase):
    def test_labeled_name(self):
        text = "PERSONAL DETAILS\nName : Jane Smith\nDate Of Birth : 1 Jan 2000"
        self.assertEqual(rm.parse_name_from_text(text), "Jane Smith")

    def test_does_not_pick_fathers_name(self):
        text = "Father's Name : Mr. Bob Baker\nName : Jane Smith"
        self.assertEqual(rm.parse_name_from_text(text), "Jane Smith")

    def test_skips_invocation_line(self):
        text = "|| Welcome Header ||\nJohn Doe"
        self.assertEqual(rm.parse_name_from_text(text), "John Doe")

    def test_first_meaningful_line_fallback(self):
        text = "Bio Data\nJohn Doe\nBirthdate: 12 November 1993"
        self.assertEqual(rm.parse_name_from_text(text), "John Doe")

    def test_all_caps_name(self):
        text = "ALICE GREEN\nBirthdate : 3rd May 1997"
        self.assertEqual(rm.parse_name_from_text(text), "ALICE GREEN")


class TestFirstName(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(rm._first_name("John Doe"), "John")

    def test_all_caps_titlecased(self):
        self.assertEqual(rm._first_name("ALICE GREEN"), "Alice")

    def test_strips_punctuation(self):
        self.assertEqual(rm._first_name("Mr. Bob"), "Mr")

    def test_empty(self):
        self.assertEqual(rm._first_name(""), "Unknown")


# ---------------------------------------------------------------------------
# Multi-format text extraction
# ---------------------------------------------------------------------------
class TestExtractTextFromFile(unittest.TestCase):
    def test_txt(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as f:
            f.write("Name : Test User\nDOB: 12/11/1993")
            path = f.name
        try:
            text = rm.extract_text_from_file(path)
            self.assertIn("Test User", text)
        finally:
            os.unlink(path)

    def test_docx(self):
        import docx
        doc = docx.Document()
        doc.add_paragraph("Name : Docx Person")
        doc.add_paragraph("Date Of Birth : 15 August 1990")
        doc.add_paragraph("Time Of Birth : 06:30 AM")
        doc.add_paragraph("Place Of Birth : Boston")
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        doc.save(path)
        try:
            text = rm.extract_text_from_file(path)
            self.assertIn("Docx Person", text)
            self.assertIn("Boston", text)
        finally:
            os.unlink(path)

    def test_unsupported_extension(self):
        with tempfile.NamedTemporaryFile("w", suffix=".rtf", delete=False) as f:
            path = f.name
        try:
            with self.assertRaises(rm.BiodataParseError) as ctx:
                rm.extract_text_from_file(path)
            self.assertIn("Unsupported file type", str(ctx.exception))
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Full extract_person_info — success and clear-error behaviour
# ---------------------------------------------------------------------------
class TestExtractPersonInfo(unittest.TestCase):
    def _write_txt(self, content):
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                        encoding="utf-8")
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_success_txt(self):
        path = self._write_txt(
            "Name : Sample Person\n"
            "Date Of Birth : 12 November 1993\n"
            "Time Of Birth : 08:45\n"
            "Place Of Birth : Denver, Colorado\n"
        )
        info = rm.extract_person_info(path)
        self.assertEqual(info["name"], "Sample Person")
        self.assertEqual(info["day"], 12)
        self.assertEqual(info["month"], 11)
        self.assertEqual(info["year"], 1993)
        self.assertEqual(info["hour"], 8)
        self.assertEqual(info["minute"], 45)
        self.assertEqual(info["place"], "Denver, Colorado")

    def test_missing_dob_clear_error(self):
        path = self._write_txt(
            "Name : No Date\nTime Of Birth : 08:45\nPlace Of Birth : Chicago\n"
        )
        with self.assertRaises(rm.BiodataParseError) as ctx:
            rm.extract_person_info(path)
        msg = str(ctx.exception)
        self.assertIn("Date of Birth", msg)
        self.assertNotIn("Time of Birth", msg)
        self.assertNotIn("Place of Birth", msg)

    def test_missing_time_clear_error(self):
        path = self._write_txt(
            "Name : No Time\nDate Of Birth : 1 Jan 2000\nPlace Of Birth : Chicago\n"
        )
        with self.assertRaises(rm.BiodataParseError) as ctx:
            rm.extract_person_info(path)
        self.assertIn("Time of Birth", str(ctx.exception))

    def test_missing_place_clear_error(self):
        path = self._write_txt(
            "Name : No Place\nDate Of Birth : 1 Jan 2000\nTime Of Birth : 10:00\n"
        )
        with self.assertRaises(rm.BiodataParseError) as ctx:
            rm.extract_person_info(path)
        self.assertIn("Place of Birth", str(ctx.exception))

    def test_multiple_missing_listed_together(self):
        path = self._write_txt("Name : Nearly Empty\n")
        with self.assertRaises(rm.BiodataParseError) as ctx:
            rm.extract_person_info(path)
        msg = str(ctx.exception)
        self.assertIn("Date of Birth", msg)
        self.assertIn("Time of Birth", msg)
        self.assertIn("Place of Birth", msg)

    def test_empty_file_clear_error(self):
        path = self._write_txt("   \n  \n")
        with self.assertRaises(rm.BiodataParseError) as ctx:
            rm.extract_person_info(path)
        self.assertIn("No readable text", str(ctx.exception))


# ---------------------------------------------------------------------------
# Optional: real sample biodata files, if present in the repo
# ---------------------------------------------------------------------------
class TestRealSamples(unittest.TestCase):
    SAMPLES = {
        "agent_alpha.pdf": {
            "name": "John Doe", "day": 12, "month": 11, "year": 1993,
            "hour": 8, "minute": 45, "place": "Denver, Colorado",
        },
        "agent_beta.pdf": {
            "name": "ALICE GREEN", "day": 3, "month": 5, "year": 1997,
            "hour": 21, "minute": 43, "place": "Denver, Colorado",
        },
        "agent_gamma.pdf": {
            "name": "Jane Smith", "day": 29, "month": 4, "year": 1998,
            "hour": 12, "minute": 48, "place": "Seattle",
        },
    }

    def test_samples(self):
        for fname, expected in self.SAMPLES.items():
            if not os.path.isfile(fname):
                self.skipTest(f"sample file not present: {fname}")
            with self.subTest(file=fname):
                info = rm.extract_person_info(fname)
                for key, value in expected.items():
                    self.assertEqual(info[key], value,
                                     f"{fname}: {key} mismatch")


if __name__ == "__main__":
    unittest.main(verbosity=2)