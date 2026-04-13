#!/usr/bin/env python3
"""
sample_more_positives.py
------------------------
Sample 100 more likely-positive speeches for annotation.
Focus on speeches with strong activism signals.
"""

import pandas as pd
import re
from pathlib import Path

# Paths
RAW_CORPUS = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v3_enriched.csv")
EXISTING_ANNOTATIONS = [
    Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/ML_data/annotation/annotation_binary_v3.xlsx"),
    Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/ML_data/annotation/targeted_positives_sample.xlsx"),
]
OUTPUT_FILE = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/ML_data/annotation/targeted_positives_round2.xlsx")

print("=" * 60)
print("SAMPLING MORE LIKELY-POSITIVE SPEECHES")
print("=" * 60)

# Load corpus
print("\n📂 Loading corpus...")
df = pd.read_csv(RAW_CORPUS, low_memory=False)
df = df[df['speaker'].str.upper() != 'PRESIDENTE']
print(f"   Speeches (no PRESIDENTE): {len(df):,}")

# Load already annotated
print("\n📂 Loading existing annotations...")
already_annotated = set()
for ann_file in EXISTING_ANNOTATIONS:
    if ann_file.exists():
        ann_df = pd.read_excel(ann_file)
        texts = ann_df['text'].dropna().str[:100].tolist()
        already_annotated.update(texts)
        print(f"   {ann_file.name}: {len(texts)} texts")
print(f"   Total already annotated: {len(already_annotated)}")

# High-confidence activism patterns (likely to be TRUE positives)
STRONG_PATTERNS = [
    # Specific protest actions
    r'\b(manifestanti|corteo|cortei)\b.{0,50}\b(polizia|scontri|cariche|lacrimogeni)',
    r'\b(protesta|proteste)\b.{0,30}\b(piazza|strada|davanti)',
    r'\bsciopero\b.{0,30}\b(generale|nazionale|lavoratori)',
    r'\bblocco\b.{0,20}\b(stradale|strade|autostrada)',
    r'\boccupazione\b.{0,30}\b(edifici|scuole|università|fabbrica)',
    r'\bpresidio\b.{0,30}\b(permanente|davanti|contro)',
    r'\bsit-in\b',
    
    # Specific groups (strongest signal)
    r'\bultima generazione\b',
    r'\bextinction rebellion\b',
    r'\bfridays for future\b',
    r'\bno tav\b',
    r'\bno tap\b',
    r'\bcasapound\b',
    r'\bforza nuova\b',
    r'\bcentri sociali\b',
    
    # Target legislation in activism context
    r'\bdecreto sicurezza\b.{0,50}\b(protesta|manifestazione|attivisti|repressione)',
    r'\bdecreto rave\b',
    r'\banti-?rave\b',
    r'\beco-?vandali\b',
    r'\breato di rave\b',
    r'\bimbrattamento\b.{0,30}\b(opere|quadri|monumenti)',
    
    # Repression/criminalization context
    r'\b(criminalizza|repressione|reprimere)\b.{0,30}\b(protesta|dissenso|manifestanti)',
    r'\bdisobbedienza civile\b',
    r'\battivisti\b.{0,30}\b(arrestati|denunciati|fermati)',
]

def has_strong_pattern(text):
    if pd.isna(text):
        return False
    text_lower = str(text).lower()
    return any(re.search(p, text_lower) for p in STRONG_PATTERNS)

def get_strong_matches(text):
    if pd.isna(text):
        return []
    text_lower = str(text).lower()
    matches = []
    for p in STRONG_PATTERNS:
        m = re.search(p, text_lower)
        if m:
            matches.append(m.group(0)[:50])
    return matches

# Find speeches with strong patterns
print("\n🔍 Finding speeches with strong activism patterns...")
df['has_strong'] = df['text'].apply(has_strong_pattern)
df['strong_matches'] = df['text'].apply(get_strong_matches)

strong_df = df[df['has_strong']].copy()
print(f"   Found: {len(strong_df):,} speeches with strong patterns")

# Exclude already annotated
strong_df['text_start'] = strong_df['text'].str[:100]
strong_df = strong_df[~strong_df['text_start'].isin(already_annotated)]
print(f"   After excluding annotated: {len(strong_df):,}")

# Sample 100
sample_size = min(100, len(strong_df))
sample = strong_df.sample(n=sample_size, random_state=123)

print(f"\n📊 Sampled: {sample_size} speeches")

# Show pattern distribution
print("\n   Pattern examples in sample:")
all_matches = []
for matches in sample['strong_matches']:
    all_matches.extend(matches)
match_counts = pd.Series(all_matches).value_counts()
for match, count in match_counts.head(10).items():
    print(f"      '{match}': {count}")

# Create output file
output_df = sample[['chamber', 'year', 'date', 'speaker', 'party', 'text']].copy()
output_df.insert(0, 'sample_id', range(1, len(output_df)+1))
output_df['pattern_matched'] = sample['strong_matches'].apply(lambda x: '; '.join(x[:2]))
output_df['is_activism_related'] = ''
output_df['confidence'] = ''
output_df['notes'] = ''

# Reorder columns
output_df = output_df[['sample_id', 'pattern_matched', 'chamber', 'year', 'date', 
                       'speaker', 'party', 'is_activism_related', 'confidence', 'notes', 'text']]

# Save
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
output_df.to_excel(OUTPUT_FILE, index=False)

print(f"\n✅ Saved to: {OUTPUT_FILE}")

print(f"""

{'=' * 60}
NEXT STEPS
{'=' * 60}

1. Open: {OUTPUT_FILE}

2. These speeches have STRONG activism signals like:
   - "manifestanti" + "polizia/scontri"
   - "Ultima Generazione", "No TAV", etc.
   - "decreto rave", "eco-vandali"
   - "attivisti arrestati"

3. Annotate 'is_activism_related' (1 or 0)
   Most should be quick YES decisions!

4. After annotating, we'll combine with your ~400 existing
   and retrain with ~500 annotations (~150+ positives)

Expected: F1 should reach 0.6-0.7
""")
