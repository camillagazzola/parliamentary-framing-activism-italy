#!/usr/bin/env python3
"""
filter_activism.py
------------------
Applies dictionary-based filtering to identify activism-related speeches
from the full parliamentary corpus. Speeches must contain at least one
term from the activism dictionary to be retained.

Input:  data/speeches_raw.csv
Output: data/dictionary_filtered.csv

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import pandas as pd
import re
from pathlib import Path

BASE   = Path(__file__).parent.parent
INPUT  = BASE / "data" / "speeches_raw.csv"
OUTPUT = BASE / "data" / "dictionary_filtered.csv"

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

    # Named groups and organisations
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

pattern = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in sorted(ACTIVISM_TERMS, key=len, reverse=True)) + r')\b',
    flags=re.IGNORECASE
)

df = pd.read_csv(INPUT)
print(f"Loaded {len(df):,} speeches")

df = df[df['speaker'] != 'PRESIDENTE'].copy()
print(f"After removing PRESIDENTE: {len(df):,}")

df['matches']      = df['text'].apply(lambda x: pattern.findall(str(x)))
df['n_matches']    = df['matches'].apply(len)
df['matched_terms'] = df['matches'].apply(
    lambda x: '; '.join(sorted(set(t.lower() for t in x)))
)

df_filtered = df[df['n_matches'] > 0].copy()
print(f"Dictionary hits: {len(df_filtered):,} ({len(df_filtered)/len(df)*100:.1f}%)")

df_filtered.to_csv(OUTPUT, index=False)
print(f"\nSaved to: {OUTPUT}")

print(f"\nTop matched terms:")
all_terms = [t.lower() for matches in df_filtered['matches'] for t in matches]
print(pd.Series(all_terms).value_counts().head(20))

print(f"\nBy year:")
print(df_filtered['year'].value_counts().sort_index())

print(f"\nBy chamber:")
print(df_filtered['chamber'].value_counts())
