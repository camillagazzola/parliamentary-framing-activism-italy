#!/usr/bin/env python3
"""
retrain_clean_v11.py
--------------------
Clean approach:
- Original training data ONLY (no quality review samples)
- Dictionary filter → ML
- Threshold ≥0.65

Run: python retrain_clean_v11.py
"""

import pandas as pd
import numpy as np
import pickle
import re
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# PATHS
# =============================================================================

BASE = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing")

# ORIGINAL training data only - no quality review additions
TRAINING_DATA = BASE / "data/processed/training_data_corrected.csv"
RAW_CORPUS = BASE / "data/processed/speeches_raw_v3_enriched.csv"

OUTPUT_DIR = BASE / "data/processed"
MODEL_PATH = OUTPUT_DIR / "binary_classifier_v11.pkl"
FILTERED_CORPUS = OUTPUT_DIR / "activism_corpus_v11.csv"
NEW_QUALITY_REVIEW = OUTPUT_DIR / "quality_review_v11.xlsx"

RANDOM_STATE = 42
THRESHOLD = 0.65  # Higher threshold for better precision

# =============================================================================
# DICTIONARY
# =============================================================================

ACTIVISM_TERMS = [
    'protesta', 'proteste', 'manifestazione', 'manifestazioni', 'manifestanti',
    'corteo', 'cortei', 'sciopero', 'scioperi', 'presidio', 'presidi', 'sit-in',
    'mobilitazione', 'attivista', 'attivisti', 'attivismo',
    'ultima generazione', 'extinction rebellion', 'fridays for future',
    'no tav', 'no tap', 'casapound', 'casa pound', 'forza nuova',
    'centri sociali', 'centro sociale', 'gilet gialli', 'black bloc',
    'decreto sicurezza', 'decreto salvini', 'decreto rave', 'ddl sicurezza',
    'eco-vandali', 'blocco stradale', 'blocchi stradali',
    'rivolta', 'rivolte', 'dissenso', 'contestazione',
]

def has_activism_term(text):
    if pd.isna(text):
        return False
    text_lower = str(text).lower()
    return any(term in text_lower for term in ACTIVISM_TERMS)

# =============================================================================
# PREPROCESSING
# =============================================================================

def preprocess_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    
    # Preserve important bigrams
    replacements = [
        (r'ultima generazione', 'ultima_generazione'),
        (r'extinction rebellion', 'extinction_rebellion'),
        (r'fridays for future', 'fridays_for_future'),
        (r'\bno tav\b', 'no_tav'),
        (r'\bno tap\b', 'no_tap'),
        (r'casa\s*pound', 'casa_pound'),
        (r'forza nuova', 'forza_nuova'),
        (r'centri sociali', 'centri_sociali'),
        (r'decreto sicurezza', 'decreto_sicurezza'),
        (r'ordine pubblico', 'ordine_pubblico'),
        (r'blocco stradale', 'blocco_stradale'),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    return text

# =============================================================================
# MAIN
# =============================================================================

print("=" * 70)
print("CLEAN CLASSIFIER v11")
print("=" * 70)
print(f"Using threshold ≥{THRESHOLD}")

# -----------------------------------------------------------------------------
# STEP 1: Load ORIGINAL training data only
# -----------------------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 1: LOADING ORIGINAL TRAINING DATA")
print("=" * 70)

training_df = pd.read_csv(TRAINING_DATA)
training_df = training_df.drop_duplicates(subset=['text'], keep='first')

n_pos = (training_df['label'] == 1).sum()
n_neg = (training_df['label'] == 0).sum()

print(f"\nTraining data: {len(training_df)}")
print(f"  Positives: {n_pos}")
print(f"  Negatives: {n_neg}")
print(f"\n  (No quality review samples added)")

# -----------------------------------------------------------------------------
# STEP 2: Train ML model
# -----------------------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 2: TRAINING ML MODEL")
print("=" * 70)

training_df['text_processed'] = training_df['text'].apply(preprocess_text)

X_text = training_df['text_processed'].values
y = training_df['label'].values

# Split
X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

print(f"Train: {len(y_train)} | Test: {len(y_test)}")

# Vectorize
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.90,
    strip_accents='unicode',
    token_pattern=r'\b\w[\w_]+\b',
)

X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)

print(f"Features: {X_train.shape[1]}")

# Train LogReg (same as v7)
model = LogisticRegression(
    max_iter=1000,
    class_weight='balanced',
    C=1.0,
    random_state=RANDOM_STATE
)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"\nTest Results (threshold 0.5):")
print(f"  Precision: {prec:.3f}")
print(f"  Recall:    {rec:.3f}")
print(f"  F1:        {f1:.3f}")

# Evaluate at threshold 0.65
y_pred_65 = (y_prob >= THRESHOLD).astype(int)
prec_65 = precision_score(y_test, y_pred_65)
rec_65 = recall_score(y_test, y_pred_65)
f1_65 = f1_score(y_test, y_pred_65)

print(f"\nTest Results (threshold {THRESHOLD}):")
print(f"  Precision: {prec_65:.3f}")
print(f"  Recall:    {rec_65:.3f}")
print(f"  F1:        {f1_65:.3f}")

# Cross-validation
X_all = vectorizer.fit_transform(X_text)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_f1 = cross_val_score(model, X_all, y, cv=cv, scoring='f1')
cv_prec = cross_val_score(model, X_all, y, cv=cv, scoring='precision')

print(f"\n5-Fold CV (threshold 0.5):")
print(f"  F1:        {cv_f1.mean():.3f} (+/- {cv_f1.std()*2:.3f})")
print(f"  Precision: {cv_prec.mean():.3f} (+/- {cv_prec.std()*2:.3f})")

# Retrain on all data
model.fit(X_all, y)

# -----------------------------------------------------------------------------
# STEP 3: Apply to corpus
# -----------------------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 3: APPLYING TO CORPUS")
print("=" * 70)

# Load corpus
raw_df = pd.read_csv(RAW_CORPUS, low_memory=False)
print(f"\nTotal speeches: {len(raw_df):,}")

# Remove PRESIDENTE
raw_df = raw_df[raw_df['speaker'].str.upper() != 'PRESIDENTE']
print(f"After removing PRESIDENTE: {len(raw_df):,}")

# Step 1: Dictionary filter
print("\n[Step 1] Dictionary filter...")
raw_df['has_activism_term'] = raw_df['text'].apply(has_activism_term)
dict_filtered = raw_df[raw_df['has_activism_term']].copy()
print(f"  Dictionary matches: {len(dict_filtered):,}")

# Step 2: ML classification
print("\n[Step 2] ML classification...")
dict_filtered['text_processed'] = dict_filtered['text'].apply(preprocess_text)
X_corpus = vectorizer.transform(dict_filtered['text_processed'].values)

dict_filtered['ml_probability'] = model.predict_proba(X_corpus)[:, 1]

# Show probability distribution
print("\n  Probability distribution:")
for thresh in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
    count = (dict_filtered['ml_probability'] >= thresh).sum()
    print(f"    ≥{thresh}: {count:,}")

# Apply threshold
final_corpus = dict_filtered[dict_filtered['ml_probability'] >= THRESHOLD].copy()

print(f"\n  RESULTS (threshold ≥{THRESHOLD}):")
print(f"    Dictionary filtered: {len(dict_filtered):,}")
print(f"    Final corpus: {len(final_corpus):,}")

# Year distribution
print(f"\n  By year:")
for year in sorted(final_corpus['year'].dropna().unique()):
    count = (final_corpus['year'] == year).sum()
    print(f"    {int(year)}: {count:,}")

# -----------------------------------------------------------------------------
# STEP 4: Save
# -----------------------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 4: SAVING")
print("=" * 70)

# Save model
model_package = {
    'model': model,
    'vectorizer': vectorizer,
    'preprocess_func': preprocess_text,
    'threshold': THRESHOLD,
    'test_precision_05': prec,
    'test_recall_05': rec,
    'test_f1_05': f1,
    'test_precision_065': prec_65,
    'test_recall_065': rec_65,
    'test_f1_065': f1_65,
    'cv_f1_mean': cv_f1.mean(),
    'cv_precision_mean': cv_prec.mean(),
    'n_training': len(training_df),
}

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model_package, f)
print(f"  Model: {MODEL_PATH}")

# Save corpus
final_corpus.to_csv(FILTERED_CORPUS, index=False)
print(f"  Corpus: {FILTERED_CORPUS}")

# Quality review sample
review_sample = final_corpus.sample(n=min(50, len(final_corpus)), random_state=45)
review_cols = ['chamber', 'year', 'date', 'speaker', 'party', 'ml_probability', 'text']
review_df = review_sample[[c for c in review_cols if c in review_sample.columns]].copy()
review_df.insert(0, 'review_id', range(1, len(review_df)+1))
review_df['is_correct'] = ''
review_df['notes'] = ''
review_df.to_excel(NEW_QUALITY_REVIEW, index=False)
print(f"  Quality review: {NEW_QUALITY_REVIEW}")

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"""
METHOD: Dictionary → ML (LogReg) with threshold ≥{THRESHOLD}
  
TRAINING: Original data only ({len(training_df)} samples)
  - No quality review samples (they were biasing the model)

TEST METRICS (at {THRESHOLD} threshold):
  Precision: {prec_65:.3f}
  Recall:    {rec_65:.3f}
  F1:        {f1_65:.3f}

CORPUS:
  Dictionary: {len(dict_filtered):,}
  Final:      {len(final_corpus):,}

EXPECTED: Higher precision than v7-v10 due to:
  1. Clean training data (no biased QR samples)
  2. Higher threshold (0.65 vs 0.50)

NEXT: Review {NEW_QUALITY_REVIEW.name}!
""")
