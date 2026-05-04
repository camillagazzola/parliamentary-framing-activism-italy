#!/usr/bin/env python3
"""
extract_senato_metadata.py
--------------------------
Extracts session metadata (date, session number) from Senato della Repubblica
plain text transcripts. Produces the metadata CSV used by segment_speakers.py.

Input:  data/raw/senato/senato_txt/ (plain text transcripts)
Output: data/senato_metadata_2018_2025_from_txt.csv

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import re
import csv
from pathlib import Path

BASE     = Path(__file__).parent.parent
TXT_BASE = BASE / "data" / "raw" / "senato" / "senato_txt"
OUT      = BASE / "data" / "senato_metadata_2018_2025_from_txt.csv"

MONTHS = {
    "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04",
    "maggio": "05", "giugno": "06", "luglio": "07", "agosto": "08",
    "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12",
}

def read_head(txt_path: Path, max_chars: int = 6000) -> str:
    with txt_path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read(max_chars)

def extract_seduta(text: str):
    m = re.search(r"\b(\d{1,4})\s*(?:ª|a)\s+seduta\b", text, re.IGNORECASE)
    return m.group(1) if m else None

def extract_date(text: str):
    m = re.search(
        r"\b([a-zàèéìòù]+)\s+(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
        r"settembre|ottobre|novembre|dicembre)\s+(\d{4})\b",
        text, re.IGNORECASE,
    )
    if not m:
        return None, None
    weekday, day, month_it, year = m.groups()
    mm          = MONTHS.get(month_it.lower())
    date_raw_it = f"{weekday.lower()} {int(day)} {month_it.lower()} {year}"
    date_iso    = f"{year}-{mm}-{int(day):02d}" if mm else None
    return date_raw_it, date_iso

rows = []
for txt_path in sorted(TXT_BASE.rglob("*.txt")):
    head       = re.sub(r"\s+", " ", read_head(txt_path)).strip()
    seduta_n   = extract_seduta(head)
    date_raw_it, date_iso = extract_date(head)
    year_folder = next(
        (part for part in txt_path.parts if re.fullmatch(r"\d{4}", part)), None
    )
    rows.append({
        "txt_path":    str(txt_path),
        "year_folder": year_folder,
        "seduta_n":    seduta_n,
        "date_raw_it": date_raw_it,
        "date_iso":    date_iso,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"Output: {OUT}")
print(f"Rows:   {len(rows)}")
print(f"Missing date_iso:  {sum(1 for r in rows if not r['date_iso'])}")
print(f"Missing seduta_n:  {sum(1 for r in rows if not r['seduta_n'])}")
