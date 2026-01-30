import yaml
import re
import pandas as pd
import csv
from pathlib import Path

# ---------- PATHS ----------
DICT_PATH = Path("docs/dictionaries/dictionary_activism.yml")
RAW_BASE = Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs")
OUT_PATH = Path("data/filtered/activism_dictionary_hits.csv")

CHAMBERS = {
    "Camera": RAW_BASE / "Camera",
    "Senato": RAW_BASE / "Senato"
}

# ---------- LOAD METADATA ----------
senato_meta = pd.read_csv("data/raw/senato_metadata_2018_2025_from_txt.csv")
camera_meta = pd.read_csv("data/raw/camera_metadata_leg18_19.csv")

# Normalize to filename-only keys
senato_meta["filename"] = senato_meta["txt_path"].apply(lambda x: Path(x).name)
camera_meta["filename"] = camera_meta["txt_path"].apply(lambda x: Path(x).name)

# Build lookups
senato_year_lookup = (
    senato_meta
    .set_index("filename")["year_folder"]
    .to_dict()
)

camera_year_lookup = (
    camera_meta
    .assign(year=lambda df: df["date_iso"].str[-4:])
    .set_index("filename")["year"]
    .to_dict()
)

# ---------- LOAD DICTIONARY ----------
with open(DICT_PATH, "r", encoding="utf-8") as f:
    dictionary = yaml.safe_load(f)

terms = dictionary["ACTIVE_TERMS"]

# escape regex characters & build pattern
terms = sorted(set(terms), key=len, reverse=True)
pattern = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b",
    flags=re.IGNORECASE
)

# ---------- HELPERS ----------
def extract_word_window(text, match_start, match_end, window=30):
    words = text.split()
    char_count = 0
    match_word_idx = None

    for i, w in enumerate(words):
        char_count += len(w) + 1
        if char_count >= match_start:
            match_word_idx = i
            break

    if match_word_idx is None:
        return ""

    start = max(0, match_word_idx - window)
    end = min(len(words), match_word_idx + window + 1)

    return " ".join(words[start:end])

# ---------- PROCESS ----------
rows = []

for chamber, folder in CHAMBERS.items():
    for txt_path in folder.rglob("*.txt"):
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        matches = list(pattern.finditer(text))

        if not matches:
            continue

        matched_terms = sorted(set(m.group(0).lower() for m in matches))
        context_window = extract_word_window(
         text,
         matches[0].start(),
         matches[0].end(),
         window=30
        )
        
        filename = txt_path.name

        if chamber == "Senato":
            year = senato_year_lookup.get(filename, "")
        else:
            year = camera_year_lookup.get(filename, "")

        chamber_meta = chamber

        rows.append({
            "speech_id": filename,
            "chamber": chamber_meta,
            "year": year,
            "path": str(txt_path),
            "matched_terms": "; ".join(matched_terms),
            "n_matches": len(matches),
            "context_window": context_window
       })

# ---------- WRITE CSV ----------
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} speeches to {OUT_PATH}")

