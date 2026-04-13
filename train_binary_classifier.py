#!/usr/bin/env python3
"""
train_binary_classifier.py
--------------------------
Step 2: Train a binary classifier to filter false positives

WHAT THIS SCRIPT DOES:
1. Loads your manually labeled data (annotation_binary.csv)
2. Trains a machine learning model to distinguish:
   - Genuine activism-related speeches (label = 1)
   - False positives (label = 0)
3. Evaluates the model's performance
4. Applies the model to your full corpus
5. Outputs a filtered corpus for frame analysis

WHEN TO RUN THIS:
- AFTER you have completed labeling annotation_binary.csv
- You need at least 400+ labeled examples for reliable results

WHAT YOU NEED:
- Python packages: pandas, scikit-learn, tqdm
- Labeled file: data/annotation/annotation_binary.csv (with is_activism_related filled in)
- Full corpus: data/processed/activism_candidates.csv

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pickle
from collections import Counter

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    precision_score, 
    recall_score, 
    f1_score,
    accuracy_score
)
from sklearn.pipeline import Pipeline

# Optional: progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Note: Install tqdm for progress bars (pip install tqdm)")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input files
LABELED_CSV = Path("data/annotation/annotation_binary.csv")
FULL_CORPUS_CSV = Path("data/processed/activism_candidates.csv")

# Output files
OUTPUT_DIR = Path("data/processed")
FILTERED_CORPUS_CSV = OUTPUT_DIR / "activism_filtered_ml.csv"
MODEL_PATH = OUTPUT_DIR / "binary_classifier.pkl"
REPORT_PATH = OUTPUT_DIR / "classifier_report.txt"

# Model settings
TEST_SIZE = 0.2          # 20% for testing
RANDOM_STATE = 42        # For reproducibility
CV_FOLDS = 5             # Cross-validation folds

# Minimum confidence threshold for predictions (optional)
# Set to 0.5 for standard classification, higher for more conservative filtering
CONFIDENCE_THRESHOLD = 0.5


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_labeled_data(filepath):
    """
    Load and validate the labeled annotation file.
    
    Returns:
        df: DataFrame with labeled examples
        n_positive: Number of positive labels (activism-related)
        n_negative: Number of negative labels (false positives)
    """
    print(f"\n📂 Loading labeled data from: {filepath}")
    
    if not filepath.exists():
        print(f"❌ ERROR: File not found: {filepath}")
        print("   Please complete annotation_binary.csv first!")
        sys.exit(1)
    
    df = pd.read_csv(filepath)
    
    # Check for required columns
    if 'is_activism_related' not in df.columns:
        print("❌ ERROR: Column 'is_activism_related' not found")
        sys.exit(1)
    
    if 'text' not in df.columns:
        print("❌ ERROR: Column 'text' not found")
        sys.exit(1)
    
    # Filter to only labeled rows (non-empty is_activism_related)
    df['is_activism_related'] = pd.to_numeric(df['is_activism_related'], errors='coerce')
    labeled_df = df[df['is_activism_related'].notna()].copy()
    labeled_df['label'] = labeled_df['is_activism_related'].astype(int)
    
    n_total = len(labeled_df)
    n_positive = (labeled_df['label'] == 1).sum()
    n_negative = (labeled_df['label'] == 0).sum()
    
    print(f"   Total labeled: {n_total}")
    print(f"   Positive (activism): {n_positive} ({n_positive/n_total*100:.1f}%)")
    print(f"   Negative (false positive): {n_negative} ({n_negative/n_total*100:.1f}%)")
    
    if n_total < 100:
        print("\n⚠️  WARNING: Very few labeled examples!")
        print("   Recommend at least 300-500 for reliable results")
    
    if n_positive < 20 or n_negative < 20:
        print("\n⚠️  WARNING: Severe class imbalance!")
        print("   Need more examples of the minority class")
    
    return labeled_df, n_positive, n_negative


def create_text_features(df, text_column='text'):
    """
    Combine text with matched terms for better features.
    
    The model learns from:
    1. The actual speech text
    2. Which activism terms were matched
    3. Speaker and party info (if available)
    """
    features = df[text_column].fillna('').astype(str)
    
    # Add matched terms as additional features
    if 'matched_terms' in df.columns:
        matched = df['matched_terms'].fillna('').astype(str)
        features = features + ' MATCHED_TERMS: ' + matched
    
    # Add party info (can help distinguish framing styles)
    if 'party' in df.columns:
        party = df['party'].fillna('unknown').astype(str)
        features = features + ' PARTY: ' + party
    
    return features


def train_and_evaluate(X_train, X_test, y_train, y_test, model_name, model):
    """
    Train a model and return evaluation metrics.
    """
    # Train
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'model': model_name,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, y_pred)
    }
    
    return metrics, model


def print_metrics(metrics):
    """Pretty print evaluation metrics."""
    print(f"\n   {metrics['model']}:")
    print(f"      Accuracy:  {metrics['accuracy']:.3f}")
    print(f"      Precision: {metrics['precision']:.3f}")
    print(f"      Recall:    {metrics['recall']:.3f}")
    print(f"      F1 Score:  {metrics['f1']:.3f}")
    
    cm = metrics['confusion_matrix']
    print(f"      Confusion Matrix:")
    print(f"         Pred 0  Pred 1")
    print(f"      True 0:  {cm[0,0]:4d}    {cm[0,1]:4d}")
    print(f"      True 1:  {cm[1,0]:4d}    {cm[1,1]:4d}")


# =============================================================================
# MAIN TRAINING PIPELINE
# =============================================================================

def main():
    print("=" * 70)
    print("BINARY CLASSIFIER TRAINING")
    print("Step 2: Filter False Positives from Activism Corpus")
    print("=" * 70)
    
    # =========================================================================
    # STEP 1: Load labeled data
    # =========================================================================
    labeled_df, n_pos, n_neg = load_labeled_data(LABELED_CSV)
    
    # =========================================================================
    # STEP 2: Prepare features
    # =========================================================================
    print("\n🔧 Preparing features...")
    
    # Create combined text features
    X_text = create_text_features(labeled_df)
    y = labeled_df['label'].values
    
    # Split into train/test
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, 
        test_size=TEST_SIZE, 
        random_state=RANDOM_STATE,
        stratify=y  # Maintain class balance in split
    )
    
    print(f"   Training set: {len(X_train_text)} examples")
    print(f"   Test set: {len(X_test_text)} examples")
    
    # =========================================================================
    # STEP 3: Create TF-IDF vectorizer
    # =========================================================================
    print("\n🔧 Creating TF-IDF features...")
    
    # TF-IDF converts text to numerical features
    # Parameters explained:
    # - max_df=0.8: Ignore terms that appear in >80% of documents (too common)
    # - min_df=3: Ignore terms that appear in <3 documents (too rare)
    # - ngram_range=(1,2): Use both single words and word pairs
    # - max_features=10000: Limit to top 10k features for efficiency
    
    vectorizer = TfidfVectorizer(
        max_df=0.8,
        min_df=3,
        ngram_range=(1, 2),
        max_features=10000,
        strip_accents='unicode',
        lowercase=True
    )
    
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)
    
    print(f"   Feature dimensions: {X_train.shape[1]} features")
    
    # =========================================================================
    # STEP 4: Train multiple models and compare
    # =========================================================================
    print("\n" + "=" * 70)
    print("📊 TRAINING AND COMPARING MODELS")
    print("=" * 70)
    
    models = {
        'Logistic Regression': LogisticRegression(
            max_iter=1000, 
            class_weight='balanced',  # Handle class imbalance
            random_state=RANDOM_STATE
        ),
        'Linear SVM': LinearSVC(
            max_iter=2000,
            class_weight='balanced',
            random_state=RANDOM_STATE
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=100,
            class_weight='balanced',
            random_state=RANDOM_STATE,
            n_jobs=-1  # Use all CPU cores
        )
    }
    
    results = []
    trained_models = {}
    
    for name, model in models.items():
        print(f"\n   Training {name}...")
        metrics, trained_model = train_and_evaluate(
            X_train, X_test, y_train, y_test, name, model
        )
        results.append(metrics)
        trained_models[name] = trained_model
        print_metrics(metrics)
    
    # =========================================================================
    # STEP 5: Cross-validation on best model
    # =========================================================================
    print("\n" + "=" * 70)
    print("📊 CROSS-VALIDATION (more robust evaluation)")
    print("=" * 70)
    
    # Find best model based on F1 score
    best_result = max(results, key=lambda x: x['f1'])
    best_model_name = best_result['model']
    
    print(f"\n   Best model: {best_model_name} (F1 = {best_result['f1']:.3f})")
    
    # Re-fit on all data and do cross-validation
    X_all = vectorizer.fit_transform(X_text)
    
    if best_model_name == 'Logistic Regression':
        final_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=RANDOM_STATE)
    elif best_model_name == 'Linear SVM':
        final_model = LinearSVC(max_iter=2000, class_weight='balanced', random_state=RANDOM_STATE)
    else:
        final_model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=RANDOM_STATE, n_jobs=-1)
    
    cv_scores = cross_val_score(final_model, X_all, y, cv=CV_FOLDS, scoring='f1')
    
    print(f"\n   {CV_FOLDS}-Fold Cross-Validation F1 Scores:")
    for i, score in enumerate(cv_scores, 1):
        print(f"      Fold {i}: {score:.3f}")
    print(f"      Mean:   {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")
    
    # =========================================================================
    # STEP 6: Train final model on ALL labeled data
    # =========================================================================
    print("\n" + "=" * 70)
    print("🎯 TRAINING FINAL MODEL ON ALL LABELED DATA")
    print("=" * 70)
    
    final_model.fit(X_all, y)
    
    # Save model and vectorizer
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    model_package = {
        'model': final_model,
        'vectorizer': vectorizer,
        'model_name': best_model_name,
        'cv_f1_mean': cv_scores.mean(),
        'cv_f1_std': cv_scores.std()
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_package, f)
    
    print(f"\n   ✅ Model saved to: {MODEL_PATH}")
    
    # =========================================================================
    # STEP 7: Apply to full corpus
    # =========================================================================
    print("\n" + "=" * 70)
    print("🚀 APPLYING MODEL TO FULL CORPUS")
    print("=" * 70)
    
    if not FULL_CORPUS_CSV.exists():
        print(f"\n⚠️  Full corpus not found: {FULL_CORPUS_CSV}")
        print("   Skipping corpus filtering step")
    else:
        print(f"\n   Loading full corpus from: {FULL_CORPUS_CSV}")
        full_df = pd.read_csv(FULL_CORPUS_CSV)
        print(f"   Total speeches: {len(full_df):,}")
        
        # Create features for full corpus
        print("   Creating features...")
        X_full_text = create_text_features(full_df)
        X_full = vectorizer.transform(X_full_text)
        
        # Predict
        print("   Predicting...")
        predictions = final_model.predict(X_full)
        
        # For Logistic Regression, also get probabilities
        if hasattr(final_model, 'predict_proba'):
            probabilities = final_model.predict_proba(X_full)[:, 1]
            full_df['activism_probability'] = probabilities
            full_df['prediction'] = predictions
        else:
            full_df['prediction'] = predictions
            full_df['activism_probability'] = predictions  # Binary for SVM
        
        # Filter to activism-related
        filtered_df = full_df[full_df['prediction'] == 1].copy()
        
        print(f"\n   Results:")
        print(f"      Predicted activism-related: {(predictions == 1).sum():,}")
        print(f"      Predicted false positives:  {(predictions == 0).sum():,}")
        print(f"      Retention rate: {(predictions == 1).sum() / len(predictions) * 100:.1f}%")
        
        # Save filtered corpus
        filtered_df.to_csv(FILTERED_CORPUS_CSV, index=False)
        print(f"\n   ✅ Filtered corpus saved to: {FILTERED_CORPUS_CSV}")
    
    # =========================================================================
    # STEP 8: Generate report
    # =========================================================================
    print("\n" + "=" * 70)
    print("📝 GENERATING REPORT")
    print("=" * 70)
    
    report_lines = [
        "=" * 60,
        "BINARY CLASSIFIER REPORT",
        "=" * 60,
        "",
        "1. TRAINING DATA",
        f"   Total labeled examples: {len(labeled_df)}",
        f"   Positive (activism): {n_pos}",
        f"   Negative (false positive): {n_neg}",
        "",
        "2. MODEL COMPARISON (Test Set)",
        "-" * 40,
    ]
    
    for r in results:
        report_lines.extend([
            f"   {r['model']}:",
            f"      Accuracy:  {r['accuracy']:.3f}",
            f"      Precision: {r['precision']:.3f}",
            f"      Recall:    {r['recall']:.3f}",
            f"      F1:        {r['f1']:.3f}",
            ""
        ])
    
    report_lines.extend([
        "3. BEST MODEL",
        f"   Model: {best_model_name}",
        f"   Cross-validation F1: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})",
        "",
        "4. INTERPRETATION",
        "-" * 40,
        "   Precision = Of speeches predicted as activism, what % actually are?",
        "   Recall = Of actual activism speeches, what % did we catch?",
        "   F1 = Harmonic mean of precision and recall",
        "",
        "   For YOUR use case (filtering false positives):",
        "   - High PRECISION means fewer false positives slip through",
        "   - High RECALL means you don't lose true activism speeches",
        "",
    ])
    
    if FULL_CORPUS_CSV.exists():
        report_lines.extend([
            "5. CORPUS FILTERING RESULTS",
            f"   Original corpus: {len(full_df):,} speeches",
            f"   After filtering: {len(filtered_df):,} speeches",
            f"   Removed as false positives: {len(full_df) - len(filtered_df):,}",
            f"   Retention rate: {len(filtered_df)/len(full_df)*100:.1f}%",
        ])
    
    report_text = '\n'.join(report_lines)
    REPORT_PATH.write_text(report_text)
    
    print(f"\n   ✅ Report saved to: {REPORT_PATH}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE")
    print("=" * 70)
    print(f"""
    OUTPUTS:
    ├── {MODEL_PATH}
    │   (Trained classifier - can reuse later)
    │
    ├── {FILTERED_CORPUS_CSV}
    │   (Filtered corpus for frame analysis)
    │
    └── {REPORT_PATH}
        (Detailed performance report)
    
    NEXT STEPS:
    1. Review the classifier report
    2. If F1 < 0.7, consider:
       - Labeling more examples
       - Adjusting the dictionary
    3. If F1 >= 0.7, proceed to:
       - Frame annotation (annotation_frames.csv)
       - Then train frame classifier
    """)


if __name__ == "__main__":
    main()
