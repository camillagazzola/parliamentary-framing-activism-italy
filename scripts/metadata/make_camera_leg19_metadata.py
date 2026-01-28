import csv, re
from pathlib import Path
from pypdf import PdfReader

IN_DIR = Path("/Users/camillagazzola/Desktop/data/camera/leg19_pdf")
OUT_CSV = Path("/Users/camillagazzola/Desktop/data/camera/leg19_metadata.csv")

MONTHS = {
    "GENNAIO":"01","FEBBRAIO":"02","MARZO":"03","APRILE":"04","MAGGIO":"05","GIUGNO":"06",
    "LUGLIO":"07","AGOSTO":"08","SETTEMBRE":"09","OTTOBRE":"10","NOVEMBRE":"11","DICEMBRE":"12",
}

def first_page_text(pdf_path: Path) -> str:
    r = PdfReader(str(pdf_path))
    t = r.pages[0].extract_text() or ""
    return re.sub(r"\s+", " ", t).strip()

def parse_date(text: str):
    # "SEDUTA DI MARTEDÌ 30 DICEMBRE 2025"
    m = re.search(r"\bSEDUTA\s+DI\s+([A-ZÀÈÉÌÒÙ]+)\s+(\d{1,2})\s+([A-ZÀÈÉÌÒÙ]+)\s+(\d{4})\b", text, re.IGNORECASE)
    if not m:
        return None, None
    weekday, day, month_it, year = m.groups()
    month_it = month_it.upper()
    date_raw_it = f"{weekday.upper()} {int(day)} {month_it} {year}"
    mm = MONTHS.get(month_it)
    date_iso = f"{year}-{mm}-{int(day):02d}" if mm else None
    return date_raw_it, date_iso

rows = []
pdfs = sorted(IN_DIR.glob("sed*.pdf"))

for pdf_path in pdfs:
    seduta = pdf_path.stem.replace("sed", "")  # '0590'
    try:
        t0 = first_page_text(pdf_path)
    except Exception:
        t0 = ""

    date_raw_it, date_iso = parse_date(t0)

    rows.append({
        "legislature": 19,
        "seduta": seduta,
        "date_raw_it": date_raw_it,
        "date_iso": date_iso,
        "pdf_path": str(pdf_path),
        "source_url_pdf": f"https://documenti.camera.it/leg19/resoconti/assemblea/html/sed{seduta}/stenografico.pdf",
    })

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print("Wrote:", OUT_CSV)
print("Rows:", len(rows))
print("Missing date_iso:", sum(1 for r in rows if not r["date_iso"]))
