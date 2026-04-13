#!/usr/bin/env python3
"""
filter_activism_v6.py
---------------------
Apply dictionary filtering to v6 corpus
"""

import pandas as pd
import re
from pathlib import Path

INPUT = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v6_enriched.csv")
OUTPUT = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/dictionary_filtered_v6.csv")

# Activism dictionary terms
ACTIVISM_TERMS = [
    # Protest and dissent
    'protesta', 'proteste', 'protestare', 'protestano', 'protestando',
    'dissenso', 'contestazione', 'contestazioni', 'contestare',
    
    # Collective action
    'mobilitazione', 'mobilitazioni', 'mobilitare',
    'azione collettiva', 'partecipazione collettiva',
    
    # Movements and activism
    'attivismo', 'attivista', 'attivisti', 'attiviste',
    'movimento', 'movimenti',
    'movimento sociale', 'movimenti sociali',
    
    # Demonstrations
    'manifestazione', 'manifestazioni', 'manifestante', 'manifestanti',
    'corteo', 'cortei',
    'presidio', 'presidi',
    'sit-in', 'sit in',
    'sciopero', 'scioperi', 'scioperare',
    'blocco stradale', 'blocchi stradali',
    
    # Claims and grievances
    'rivendicazione', 'rivendicazioni',
    
    # Boundary terms
    'rivolta', 'rivolte',
    'sommossa', 'sommosse',
    'insurrezione',
    
    # Specific groups (Italian context)
    'no tav', 'notav',
    'no tap', 'notap', 
    'ultima generazione',
    'extinction rebellion',
    'fridays for future',
    'centri sociali', 'centro sociale',
    'casapound', 'casa pound',
    'forza nuova',
    'antagonisti', 'antagonista',
    'black bloc', 'black block',
    'antifa', 'antifascisti', 'antifascista',
    'eco-vandali', 'ecovandali',
]

# Build regex pattern
pattern = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in sorted(ACTIVISM_TERMS, key=len, reverse=True)) + r')\b',
    flags=re.IGNORECASE
)

print("Loading v6 enriched corpus...")
df = pd.read_csv(INPUT)
print(f"  Loaded {len(df):,} speeches")

# Exclude PRESIDENTE
print("Excluding PRESIDENTE speeches...")
df_non_pres = df[df['speaker'] != 'PRESIDENTE'].copy()
print(f"  Non-PRESIDENTE: {len(df_non_pres):,}")

# Apply dictionary filter
print("Applying dictionary filter...")
df_non_pres['matches'] = df_non_pres['text'].apply(lambda x: pattern.findall(str(x)))
df_non_pres['n_matches'] = df_non_pres['matches'].apply(len)
df_non_pres['matched_terms'] = df_non_pres['matches'].apply(lambda x: '; '.join(sorted(set(t.lower() for t in x))))

# Filter to speeches with at least one match
df_filtered = df_non_pres[df_non_pres['n_matches'] > 0].copy()
print(f"  Dictionary hits: {len(df_filtered):,}")

# Save
df_filtered.to_csv(OUTPUT, index=False)
print(f"\nSaved to: {OUTPUT}")

# Stats
print(f"\n{'='*60}")
print("DICTIONARY FILTERING SUMMARY")
print(f"{'='*60}")
print(f"Input (non-PRESIDENTE): {len(df_non_pres):,}")
print(f"Dictionary hits: {len(df_filtered):,} ({len(df_filtered)/len(df_non_pres)*100:.1f}%)")

print(f"\nTop matched terms:")
all_terms = []
for matches in df_filtered['matches']:
    all_terms.extend([t.lower() for t in matches])
term_counts = pd.Series(all_terms).value_counts().head(20)
print(term_counts)

print(f"\nBy year:")
print(df_filtered['year'].value_counts().sort_index())

print(f"\nBy chamber:")
print(df_filtered['chamber'].value_counts())
