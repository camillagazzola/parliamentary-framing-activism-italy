#!/usr/bin/env python3
"""
clean_corpus.py
---------------
Prepares the final analysis-ready corpus from the classified activism corpus.

Steps:
  1. Drop rows with missing or garbled party labels (segmentation errors)
  2. Map all non-standard party labels to canonical labels
  3. Output activism_corpus_final.csv

Input:  data/activism_corpus_classified.csv
Output: data/activism_corpus_final.csv

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import csv
import os
from pathlib import Path
from collections import Counter

BASE   = Path(__file__).parent.parent
INPUT  = BASE / "data" / "activism_corpus_classified.csv"
OUTPUT = BASE / "data" / "activism_corpus_final.csv"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

PARTY_MAP = {
    "AVS": "AVS", "A-VS": "AVS", "MISTO-AVS": "AVS",
    "PD": "PD", "PD-IDP": "PD", "PD--IDP": "PD",
    "FDI": "FDI",
    "LEGA": "LEGA", "L-SP": "LEGA",
    "M5S": "M5S",
    "FI": "FI", "FI-PPE": "FI", "FI-BP-PPE": "FI", "FIBP-UDC": "FI",
    "IV": "IV", "IV-C-RE": "IV", "IV-PSI": "IV", "A-IV-RE": "IV", "AZ-IV-RE": "IV",
    "AZ-PER-RE": "AZIONE", "MISTO-AZ-RE": "AZIONE",
    "LEU": "LEU", "MISTO-LEU": "LEU", "MISTO-LEU-ECO": "LEU",
    "+EUROPA": "+EUROPA", "MISTO-+EUROPA": "+EUROPA", "MISTO--+EUROPA": "+EUROPA",
    "MISTO-+E-CD": "+EUROPA", "MISTO-CD-RI-+E": "+EUROPA",
    "MISTO": "MISTO", "CI": "MISTO", "M-NCI-USEI-R-AC": "MISTO",
    "M-NCI-USEI-R--AC": "MISTO", "MISTO-NCI--USEI": "MISTO",
    "MISTO-IPI-PVU": "MISTO", "MISTO-CP-A-PS-A": "MISTO",
}

DROP_PARTIES = {"", "APPLAUSI"}

with open(INPUT, encoding="utf-8") as f:
    reader     = csv.DictReader(f)
    rows       = list(reader)
    fieldnames = reader.fieldnames

print(f"Input rows: {len(rows)}")

kept, dropped_missing, dropped_unmapped = [], 0, 0

for r in rows:
    raw_party = r.get("party", "").strip()
    if raw_party in DROP_PARTIES:
        dropped_missing += 1
        continue
    clean_party = PARTY_MAP.get(raw_party)
    if clean_party is None:
        print(f"  WARNING: unmapped party '{raw_party}' in {r['speech_id']} — dropping")
        dropped_unmapped += 1
        continue
    r["party_clean"] = clean_party
    kept.append(r)

print(f"Dropped (segmentation errors): {dropped_missing}")
print(f"Dropped (unmapped):            {dropped_unmapped}")
print(f"Kept:                          {len(kept)}")

dist = Counter(r["party_clean"] for r in kept)
print("\nParty distribution:")
for party, n in sorted(dist.items(), key=lambda x: -x[1]):
    print(f"  {party:15s} {n:4d}  ({100*n/len(kept):.1f}%)")

out_fields = list(dict.fromkeys((fieldnames or []) + ["party_clean"]))
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=out_fields)
    writer.writeheader()
    writer.writerows(kept)

print(f"\nOutput: {OUTPUT}")
print("Done.")
