#!/usr/bin/env python3
"""
enrich_corpus_v6.py
-------------------
Add word counts and other metadata to v6 corpus
"""

import pandas as pd
from pathlib import Path

INPUT = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v6.csv")
OUTPUT = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v6_enriched.csv")

print("Loading v6 corpus...")
df = pd.read_csv(INPUT)
print(f"  Loaded {len(df):,} speeches")

# Add word count
print("Adding word counts...")
df['word_count'] = df['text'].str.split().str.len()

# Save
df.to_csv(OUTPUT, index=False)
print(f"\nSaved to: {OUTPUT}")

# Stats
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"Total speeches: {len(df):,}")
print(f"Average word count: {df['word_count'].mean():.0f}")
print(f"Median word count: {df['word_count'].median():.0f}")
print(f"Short speeches (<20 words): {(df['word_count'] < 20).sum():,}")
print(f"\nBy year:")
print(df['year'].value_counts().sort_index())
print(f"\nMissing dates: {df['date'].isna().sum():,}")
