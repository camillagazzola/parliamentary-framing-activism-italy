#!/usr/bin/env python3
"""
train_classifier.py
-------------------
Binary classifier to distinguish activism-related speeches from incidental
keyword matches. Uses dictionary pre-filtering followed by logistic regression
with a precision-oriented threshold (≥0.65).

Input:  data/training_data_corrected.csv
        data/activism_corpus_final.csv
Output: data/binary_classifier.pkl
        data/activism_corpus_classified.csv

Author: Camilla Gazzola
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

# 
# PATHS
# 

BASE = Path(__file__).parent.parent
TRAINING_DATA = BASE / "data/training_data_corrected.csv"
RAW_CORPUS = BASE / "data/activism_corpus_final.csv"
OUTPUT_DIR = BASE / "data"
MODEL_PATH = OUTPUT_DIR / "binary_classifier.pkl"
FILTERED_CORPUS = OUTPUT_DIR / "activism_corpus_classified.csv"

RANDOM_STATE = 42
THRESHOLD = 0.65

# 
# DICTIONARY
# 

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

# 
# PREPROCESSING
# 

def preprocess_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
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

# 
# MAIN
# 

# Load training data
training_df = pd.read_csv(TRAINING_DATA)
training_df = training_df.drop_duplicates(subset=['text'], keep='first')
print(f"Training data: {len(training_df)} | Positives: {(training_df['label']==1).sum()} | Negatives: {(training_df['label']==0).sum()}")

# Preprocess
training_df['text_processed'] = training_df['text'].apply(preprocess_text)
X_text = training_df['text_processed'].values
y = training_df['label'].values

# Train/test split
X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

# Vectorise
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

# Train
model = LogisticRegression(
    max_iter=1000,
    class_weight='balanced',
    C=1.0,
    random_state=RANDOM_STATE
)
model.fit(X_train, y_train)

# Evaluate at default and thesis threshold
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]
y_pred_65 = (y_prob >= THRESHOLD).astype(int)

print(f"\nTest results (threshold 0.5):  P={precision_score(y_test, y_pred):.3f} R={recall_score(y_test, y_pred):.3f} F1={f1_score(y_test, y_pred):.3f}")
print(f"Test results (threshold {THRESHOLD}): P={precision_score(y_test, y_pred_65):.3f} R={recall_score(y_test, y_pred_65):.3f} F1={f1_score(y_test, y_pred_65):.3f}")

# Cross-validation
X_all = vectorizer.fit_transform(X_text)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_f1 = cross_val_score(model, X_all, y, cv=cv, scoring='f1')
cv_prec = cross_val_score(model, X_all, y, cv=cv, scoring='precision')
print(f"5-fold CV: F1={cv_f1.mean():.3f} (+/-{cv_f1.std()*2:.3f}) | Precision={cv_prec.mean():.3f} (+/-{cv_prec.std()*2:.3f})")

# Retrain on all data
model.fit(X_all, y)

# Apply to corpus
raw_df = pd.read_csv(RAW_CORPUS, low_memory=False)
raw_df = raw_df[raw_df['speaker'].str.upper() != 'PRESIDENTE']
raw_df['has_activism_term'] = raw_df['text'].apply(has_activism_term)
dict_filtered = raw_df[raw_df['has_activism_term']].copy()
print(f"\nDictionary filtered: {len(dict_filtered):,}")

dict_filtered['text_processed'] = dict_filtered['text'].apply(preprocess_text)
X_corpus = vectorizer.transform(dict_filtered['text_processed'].values)
dict_filtered['ml_probability'] = model.predict_proba(X_corpus)[:, 1]
final_corpus = dict_filtered[dict_filtered['ml_probability'] >= THRESHOLD].copy()
print(f"Final corpus (threshold {THRESHOLD}): {len(final_corpus):,}")

# Save
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
model_package = {
    'model': model,
    'vectorizer': vectorizer,
    'threshold': THRESHOLD,
    'cv_f1_mean': cv_f1.mean(),
    'cv_precision_mean': cv_prec.mean(),
    'n_training': len(training_df),
}
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model_package, f)

final_corpus.to_csv(FILTERED_CORPUS, index=False)
print(f"\nModel saved: {MODEL_PATH}")
print(f"Corpus saved: {FILTERED_CORPUS}")
