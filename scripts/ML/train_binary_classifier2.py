#!/usr/bin/env python3
"""
train_binary_classifier.py
--------------------------
Trains a binary classifier to distinguish activism-related speeches
from incidental keyword matches.

Input:  data/annotation/annotation_binary.csv (manually labelled)
        data/processed/activism_candidates.csv (full corpus)
Output: data/processed/activism_filtered_ml.csv
        data/processed/binary_classifier.pkl
        data/processed/classifier_report.txt

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pickle

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, accuracy_score
)

# =============================================================================
# CONFIGURATION
# =============================================================================

LABELED_CSV       = Path("data/annotation/annotation_binary.csv")
FULL_CORPUS_CSV   = Path("data/processed/activism_candidates.csv")
OUTPUT_DIR        = Path("data/processed")
FILTERED_CORPUS_CSV = OUTPUT_DIR / "activism_filtered_ml.csv"
MODEL_PATH        = OUTPUT_DIR / "binary_classifier.pkl"
REPORT_PATH       = OUTPUT_DIR / "classifier_report.txt"

TEST_SIZE         = 0.2
RANDOM_STATE      = 42
CV_FOLDS          = 5

# =============================================================================
# FUNCTIONS
# =============================================================================

def load_labeled_data(filepath):
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    df = pd.read_csv(filepath)
    df['is_activism_related'] = pd.to_numeric(df['is_activism_related'], errors='coerce')
    labeled_df = df[df['is_activism_related'].notna()].copy()
    labeled_df['label'] = labeled_df['is_activism_related'].astype(int)

    n_pos = (labeled_df['label'] == 1).sum()
    n_neg = (labeled_df['label'] == 0).sum()
    print(f"Labeled data: {len(labeled_df)} total | {n_pos} positive | {n_neg} negative")

    return labeled_df, n_pos, n_neg


def create_text_features(df, text_column='text'):
    features = df[text_column].fillna('').astype(str)
    if 'matched_terms' in df.columns:
        features = features + ' MATCHED_TERMS: ' + df['matched_terms'].fillna('').astype(str)
    if 'party' in df.columns:
        features = features + ' PARTY: ' + df['party'].fillna('unknown').astype(str)
    return features


def train_and_evaluate(X_train, X_test, y_train, y_test, model_name, model):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    metrics = {
        'model':      model_name,
        'accuracy':   accuracy_score(y_test, y_pred),
        'precision':  precision_score(y_test, y_pred, zero_division=0),
        'recall':     recall_score(y_test, y_pred, zero_division=0),
        'f1':         f1_score(y_test, y_pred, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, y_pred)
    }
    return metrics, model


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Load data
    labeled_df, n_pos, n_neg = load_labeled_data(LABELED_CSV)

    # Features
    X_text = create_text_features(labeled_df)
    y = labeled_df['label'].values
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # Vectorise
    vectorizer = TfidfVectorizer(
        max_df=0.8, min_df=3, ngram_range=(1, 2),
        max_features=10000, strip_accents='unicode', lowercase=True
    )
    X_train = vectorizer.fit_transform(X_train_text)
    X_test  = vectorizer.transform(X_test_text)

    # Train models
    models = {
        'Logistic Regression': LogisticRegression(
            max_iter=1000, class_weight='balanced', random_state=RANDOM_STATE),
        'Linear SVM': LinearSVC(
            max_iter=2000, class_weight='balanced', random_state=RANDOM_STATE),
        'Random Forest': RandomForestClassifier(
            n_estimators=100, class_weight='balanced',
            random_state=RANDOM_STATE, n_jobs=-1)
    }

    results, trained_models = [], {}
    for name, model in models.items():
        metrics, trained_model = train_and_evaluate(
            X_train, X_test, y_train, y_test, name, model)
        results.append(metrics)
        trained_models[name] = trained_model
        cm = metrics['confusion_matrix']
        print(f"{name}: accuracy={metrics['accuracy']:.3f} | "
              f"precision={metrics['precision']:.3f} | "
              f"recall={metrics['recall']:.3f} | "
              f"F1={metrics['f1']:.3f}")

    # Cross-validation on best model
    best = max(results, key=lambda x: x['f1'])
    print(f"\nBest model: {best['model']} (F1={best['f1']:.3f})")

    X_all = vectorizer.fit_transform(X_text)
    final_model = trained_models[best['model']]
    cv_scores = cross_val_score(final_model, X_all, y, cv=CV_FOLDS, scoring='f1')
    print(f"Cross-validation F1: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")

    # Train on all data and save
    final_model.fit(X_all, y)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump({'model': final_model, 'vectorizer': vectorizer,
                     'model_name': best['model'],
                     'cv_f1_mean': cv_scores.mean(),
                     'cv_f1_std': cv_scores.std()}, f)

    # Apply to full corpus
    if FULL_CORPUS_CSV.exists():
        full_df = pd.read_csv(FULL_CORPUS_CSV)
        X_full = vectorizer.transform(create_text_features(full_df))
        predictions = final_model.predict(X_full)

        if hasattr(final_model, 'predict_proba'):
            full_df['activism_probability'] = final_model.predict_proba(X_full)[:, 1]
        full_df['prediction'] = predictions

        filtered_df = full_df[full_df['prediction'] == 1].copy()
        filtered_df.to_csv(FILTERED_CORPUS_CSV, index=False)
        print(f"\nCorpus: {len(full_df):,} -> {len(filtered_df):,} retained "
              f"({len(filtered_df)/len(full_df)*100:.1f}%)")

    print(f"\nModel saved: {MODEL_PATH}")
    print(f"Filtered corpus: {FILTERED_CORPUS_CSV}")


if __name__ == "__main__":
    main()
