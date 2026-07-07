# Astro Agent

An automated agent that calculates the Vedic **Guna Milan** (Ashtakoot) compatibility
score between a boy and a girl from their biodata files.

Given two biodata files (**PDF, DOCX, DOC, or TXT**), the agent:

1. Parses **Date of Birth**, **Time of Birth**, and **Place of Birth** from each file.
2. Opens [AstroSage Matchmaking](https://www.astrosage.com/freechart/matchmaking.asp)
   in a **headless** (background) browser.
3. Fills the web form, handles the place autocomplete and the confirmation step.
4. Reads the total **Guna score out of 36** from the result page.
5. Clicks **"Download Match Making PDF"** to save the official, nicely-formatted
   report locally, and prints the score to the terminal.

If a required field is missing from a file, the agent stops with a **clear,
actionable error message** instead of a raw traceback.

---

## Requirements

- **Python 3.9+**
- Internet access (the agent uses the live AstroSage website)
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF text extraction
- [python-docx](https://python-docx.readthedocs.io/) — Word (.docx) text extraction
- [Playwright](https://playwright.dev/python/) — headless browser automation

---

## Setup

Clone the repository:

```bash
git clone https://github.com/NishantKJani/Astro-Agent.git
cd Astro-agent
```

(Optional but recommended) create and activate a virtual environment:

```bash
# Windows (PowerShell)
python3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip3 install -r requirements.txt
```

Install the Playwright browser (one-time, downloads Chromium):

```bash
python3 -m playwright install chromium
```

---

## Usage

Run the matchmaking script with the boy's and girl's biodata PDFs:

```bash
python3 run_match.py --boy "path/to/boy.pdf" --girl "path/to/girl.pdf"
```

### Options

| Flag | Required | Description |
| --- | --- | --- |
| `--boy` | yes | Path to the boy's biodata file (`.pdf`, `.docx`, `.doc`, `.txt`) |
| `--girl` | yes | Path to the girl's biodata file (`.pdf`, `.docx`, `.doc`, `.txt`) |
| `--output` | no | Output PDF file name (default: `<BoyFirstName>_<GirlFirstName>_astro_match_result.pdf`) |

### Example

```bash
python3 run_match.py --boy "Rahul_biodata.pdf" --girl "Priya_biodata.pdf"
```

Sample output:

```
[*] Parsing boy's biodata ...
    Name : • Name: Rahul
    DOB  : 01/02/1998
    Time : 12:00
    Place: Mumbai, Maharashtra
[*] Parsing girl's biodata ...
    Name : • Name: Priya
    DOB  : 15/03/1997
    Time : 15:00
    Place: New Delhi, India
[*] Navigating to https://www.astrosage.com/freechart/matchmaking.asp ...
[*] Filling Boy's details ...
[*] Filling Girl's details ...
[*] Submitting form ...
[*] Waiting for results ...
[*] Match Making PDF downloaded to: Rahul_Priya_astro_match_result.pdf

==================================================
  ASTRO MATCH SCORE : 18/36
==================================================
```

The full, official Match Making report is saved as
`<BoyFirstName>_<GirlFirstName>_astro_match_result.pdf` (e.g.
`Rahul_Priya_astro_match_result.pdf`) in the current directory.

---

## How the Score Works

The Ashtakoot system distributes **36 points** across eight factors (Varna, Vashya,
Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi).

| Obtained Points | Interpretation |
| --- | --- |
| Less than 18 | Not recommended match |
| 18 to 24 | Average, acceptable match |
| 24 to 32 | Very good match |
| 32 to 36 | Excellent match |

---

## Biodata File Format

The agent reads **PDF, DOCX, DOC, and TXT** files. The parser looks for these
fields anywhere in the text and supports common formats:

- **Date of Birth** — e.g. `1 March 1998`, `3rd May 1997`, `5 Sep 2000`, or `5/9/2000`
- **Time of Birth** — e.g. `12:16`, `09:43 pm`, `2:16 PM`, `12:48 PM`
- **Place of Birth** — a line containing `Birthplace:`, `Place:` or `Place of Birth:`

### Error handling

If a file is unreadable, empty/scanned, an unsupported type, or missing any of the
three required fields, the agent exits with a **clear message** describing exactly
what is wrong and which file caused it — for example:

```
[ERROR] Problem with the BOY's biodata file:
Could not extract the following required field(s) from 'boy.pdf':
  - Date of Birth (e.g. '12 February 1998' or '12/02/1998')
Please make sure the file clearly contains these details.
```

---

## Running the Tests

The parser is covered by unit tests in `test_parser.py` (uses Python's built-in
`unittest`, no extra dependency required):

```bash
python3 -m unittest test_parser.py -v
```

The tests cover date/time/place/name parsing across formats, `.txt`/`.docx`
extraction, unsupported-type and missing-field error messages, and — when the
sample files are present — the bundled biodata PDFs.

---

## Project Structure

```
Astro-agent/
├── run_match.py          # Main CLI script (parser + browser automation)
├── test_parser.py        # Unit tests for the biodata parser
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── *.pdf / *.docx / *.txt  # Sample biodata files / generated results
```

---

## Notes

- No personal information was used in development of this project. The boy and girl details mentioned are just for illustrative purposes. The photos used were generated by AI.
- The browser runs **headless** by default — no window appears during execution.
- An active internet connection is required since the score is computed by the
  live AstroSage website.
- The saved PDF is the official AstroSage Match Making report (downloaded via the
  site's "Download Match Making PDF" button), so it is fully formatted. If the
  download fails, the script falls back to rendering the result page to PDF.
