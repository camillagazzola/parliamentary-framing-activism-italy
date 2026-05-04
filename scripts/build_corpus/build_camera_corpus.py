#!/usr/bin/env python3
"""
build_corpus.py
---------------
Converts Italian parliamentary PDF transcripts to plain text and extracts
session metadata (legislature, session number, date) for both chambers.

Processes Camera dei Deputati transcripts for legislatures XVIII and XIX.
PDFs are downloaded from:
  https://documenti.camera.it/leg{N}/resoconti/assemblea/html/sed{N}/stenografico.pdf

Input:  data/raw/camera/leg18_pdf/ and leg19_pdf/ (PDF transcripts)
Output: data/raw/camera/leg18_txt/ and leg19_txt/ (plain text)
        data/camera_metadata_leg18_19.csv (session metadata)

Note: Raw PDFs are not included in this repository due to file size.
      This script is provided for transparency and reproducibility of the
      corpus construction process.

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import csv
import re
from pathlib import Path
from pypdf import PdfReader

BASE     = Path(__file__).parent.parent / "data" / "raw" / "camera"
OUT_META = Path(__file__).parent.parent / "data" / "camera_metadata_leg18_19.csv"

MONTHS = {
    "GENNAIO": "01", "FEBBRAIO": "02", "MARZO": "03", "APRILE": "04",
    "MAGGIO": "05", "GIUGNO": "06", "LUGLIO": "07", "AGOSTO": "08",
    "SETTEMBRE": "09", "OTTOBRE": "10", "NOVEMBRE": "11", "DICEMBRE": "12",
}

def normalize_ws(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"

def extract_date(first_page_one_line: str):
    m = re.search(
        r"\bSEDUTA\s+DI\s+([A-ZÀÈÉÌÒÙ]+)\s+(\d{1,2})\s+([A-ZÀÈÉÌÒÙ]+)\s+(\d{4})\b",
        first_page_one_line,
        re.IGNORECASE,
    )
    if not m:
        return None, None
    weekday, day, month_it, year = m.groups()
    month_it_u = month_it.upper()
    mm = MONTHS.get(month_it_u)
    date_raw_it = f"{weekday.upper()} {int(day)} {month_it_u} {year}"
    date_iso = f"{year}-{mm}-{int(day):02d}" if mm else None
    return date_raw_it, date_iso

def pdf_to_text_and_meta(leg: int):
    pdf_dir = BASE / f"leg{leg}_pdf"
    txt_dir = BASE / f"leg{leg}_txt"
    txt_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for pdf_path in sorted(pdf_dir.glob("sed*.pdf")):
        seduta   = pdf_path.stem.replace("sed", "")
        txt_path = txt_dir / f"sed{seduta}.txt"

        if not txt_path.exists() or txt_path.stat().st_size == 0:
            try:
                r          = PdfReader(str(pdf_path))
                page_texts = [p.extract_text() or "" for p in r.pages]
                full       = normalize_ws("\n\n".join(page_texts))
                txt_path.write_text(full, encoding="utf-8")
            except Exception:
                txt_path.write_text("", encoding="utf-8")

        try:
            r     = PdfReader(str(pdf_path))
            first = r.pages[0].extract_text() or ""
        except Exception:
            first = ""

        first_one_line      = re.sub(r"\s+", " ", first).strip()
        date_raw_it, date_iso = extract_date(first_one_line)

        rows.append({
            "legislature": leg,
            "seduta":      seduta,
            "date_raw_it": date_raw_it,
            "date_iso":    date_iso,
            "pdf_path":    str(pdf_path),
            "txt_path":    str(txt_path),
            "source_url_pdf": (
                f"https://documenti.camera.it/leg{leg}/resoconti/assemblea"
                f"/html/sed{seduta}/stenografico.pdf"
            ),
            "txt_bytes": txt_path.stat().st_size if txt_path.exists() else 0,
        })

    return rows

all_rows = []
for leg in (18, 19):
    all_rows.extend(pdf_to_text_and_meta(leg))

OUT_META.parent.mkdir(parents=True, exist_ok=True)
with OUT_META.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
    w.writeheader()
    w.writerows(all_rows)

print(f"Metadata written: {OUT_META}")
print(f"Total sessions:   {len(all_rows)}")
for leg in (18, 19):
    missing = sum(1 for r in all_rows if r["legislature"] == leg and not r["date_iso"])
    print(f"Missing date_iso leg{leg}: {missing}")
