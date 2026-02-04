import csv, re
from pathlib import Path
from pypdf import PdfReader

BASE = Path("/Users/camillagazzola/Desktop/data/senato")
OUT_META = BASE / "senato_metadata_2018_2025.csv"
TXT_BASE = Path("/Users/camillagazzola/Desktop/data/senato_txt")

MONTHS = {
    "GENNAIO":"01","FEBBRAIO":"02","MARZO":"03","APRILE":"04","MAGGIO":"05","GIUGNO":"06",
    "LUGLIO":"07","AGOSTO":"08","SETTEMBRE":"09","OTTOBRE":"10","NOVEMBRE":"11","DICEMBRE":"12",
}

def normalize_ws(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"

def first_page_one_line(pdf_path: Path) -> str:
    try:
        r = PdfReader(str(pdf_path))
        first = r.pages[0].extract_text() or ""
    except Exception:
        first = ""
    return re.sub(r"\s+", " ", first).strip()

def extract_date(one_line: str):
    # Works if header contains "SEDUTA DI <weekday> <day> <month> <year>"
    m = re.search(r"\bSEDUTA\s+DI\s+([A-ZÀÈÉÌÒÙ]+)\s+(\d{1,2})\s+([A-ZÀÈÉÌÒÙ]+)\s+(\d{4})\b", one_line, re.IGNORECASE)
    if not m:
        return None, None
    weekday, day, month_it, year = m.groups()
    month_it_u = month_it.upper()
    mm = MONTHS.get(month_it_u)
    date_raw_it = f"{weekday.upper()} {int(day)} {month_it_u} {year}"
    date_iso = f"{year}-{mm}-{int(day):02d}" if mm else None
    return date_raw_it, date_iso

def extract_legislature(one_line: str):
    m = re.search(r"\b([XVI]+)\s+LEGISLATURA\b", one_line, re.IGNORECASE)
    if not m:
        return None
    roman = m.group(1).upper()
    mapping = {"XVIII":18, "XIX":19, "XVII":17, "XX":20}
    return mapping.get(roman)

def extract_seduta_number(one_line: str):
    m = re.search(r"\bn\.\s*(\d{1,4})\b", one_line, re.IGNORECASE)
    return m.group(1) if m else None

def pdf_to_txt(pdf_path: Path, txt_path: Path):
    if txt_path.exists() and txt_path.stat().st_size > 0:
        return
    try:
        r = PdfReader(str(pdf_path))
        pages = [(p.extract_text() or "") for p in r.pages]
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(normalize_ws("\n\n".join(pages)), encoding="utf-8")
    except Exception:
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text("", encoding="utf-8")

all_rows = []

years = [str(y) for y in range(2018, 2026)]
for year in years:
    year_dir = BASE / year
    if not year_dir.exists():
        continue

    for pdf_path in sorted(year_dir.glob("*.pdf")):
        txt_path = TXT_BASE / year / (pdf_path.stem + ".txt")

        pdf_to_txt(pdf_path, txt_path)

        one_line = first_page_one_line(pdf_path)
        leg = extract_legislature(one_line)
        seduta_n = extract_seduta_number(one_line)
        date_raw_it, date_iso = extract_date(one_line)

        all_rows.append({
            "year_folder": year,
            "legislature": leg,
            "seduta_n": seduta_n,
            "date_raw_it": date_raw_it,
            "date_iso": date_iso,
            "pdf_filename": pdf_path.name,
            "pdf_path": str(pdf_path),
            "txt_path": str(txt_path),
            "txt_bytes": txt_path.stat().st_size if txt_path.exists() else 0,
        })

if not all_rows:
    raise SystemExit(f"No PDFs found under {BASE}/<year>/")

OUT_META.parent.mkdir(parents=True, exist_ok=True)
with OUT_META.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
    w.writeheader()
    w.writerows(all_rows)

print("Wrote:", OUT_META)
print("Rows:", len(all_rows))
print("Missing date_iso:", sum(1 for r in all_rows if not r["date_iso"]))
print("Missing legislature:", sum(1 for r in all_rows if not r["legislature"]))
