import re, csv
from pathlib import Path

TXT_BASE = Path("/Users/camillagazzola/Desktop/data/senato_txt")
OUT = Path("/Users/camillagazzola/Desktop/data/senato/senato_metadata_2018_2025_from_txt.csv")

MONTHS = {
    "gennaio":"01","febbraio":"02","marzo":"03","aprile":"04","maggio":"05","giugno":"06",
    "luglio":"07","agosto":"08","settembre":"09","ottobre":"10","novembre":"11","dicembre":"12",
}

def read_head(txt_path: Path, max_chars=6000) -> str:
    # Only need the top part where the header is
    with txt_path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read(max_chars)

def extract_seduta(text: str):
    # e.g., "392ª seduta pubblica" or "392a seduta"
    m = re.search(r"\b(\d{1,4})\s*(?:ª|a)\s+seduta\b", text, re.IGNORECASE)
    return m.group(1) if m else None

def extract_date(text: str):
    # e.g., "lunedì 3 gennaio 2022"
    m = re.search(
        r"\b([a-zàèéìòù]+)\s+(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})\b",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None, None
    weekday, day, month_it, year = m.groups()
    mm = MONTHS.get(month_it.lower())
    date_raw_it = f"{weekday.lower()} {int(day)} {month_it.lower()} {year}"
    date_iso = f"{year}-{mm}-{int(day):02d}" if mm else None
    return date_raw_it, date_iso

rows = []
txt_files = sorted(TXT_BASE.rglob("*.txt"))

for txt_path in txt_files:
    head = re.sub(r"\s+", " ", read_head(txt_path)).strip()

    seduta_n = extract_seduta(head)
    date_raw_it, date_iso = extract_date(head)

    # Try to infer year folder (e.g., .../2022/BGT_....txt)
    year_folder = None
    for part in txt_path.parts:
        if re.fullmatch(r"\d{4}", part):
            year_folder = part

    rows.append({
        "txt_path": str(txt_path),
        "year_folder": year_folder,
        "seduta_n": seduta_n,
        "date_raw_it": date_raw_it,
        "date_iso": date_iso,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print("Wrote:", OUT)
print("Rows:", len(rows))
print("Missing date_iso:", sum(1 for r in rows if not r["date_iso"]))
print("Missing seduta_n:", sum(1 for r in rows if not r["seduta_n"]))
