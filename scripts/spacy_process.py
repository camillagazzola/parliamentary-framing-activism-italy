#!/usr/bin/env python3
"""
spacy_process.py
----------------
Phase 3: spaCy Processing for Italian Parliamentary Corpus (RESUMABLE VERSION)

This script processes the segmented speeches with spaCy to extract:
- Lemmas (base forms of words)
- POS tags (part-of-speech: NOUN, VERB, ADJ, etc.)
- Named entities (PER, ORG, LOC, etc.)

RESUMABLE: Saves progress every 5000 speeches. If interrupted, restart and it
will continue from where it left off.

Input:
    - data/processed/speeches_raw.csv (from Phase 2)

Output:
    - data/processed/speeches_spacy.csv (with added linguistic features)
    - data/processed/.spacy_progress.csv (temporary progress file)

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import csv
import sys
import os
from pathlib import Path
from typing import List, Dict

import pandas as pd
import spacy
from tqdm import tqdm

# =============================================================================
# CONFIGURATION
# =============================================================================

INPUT_CSV = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v3_enriched.csv")
OUTPUT_CSV = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_spacy_v3.csv")
PROGRESS_CSV = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/.spacy_progress_v3.csv")  # Temporary file

# spaCy model - use the large Italian model for better accuracy
SPACY_MODEL = "it_core_news_lg"

# Process in batches to manage memory
BATCH_SIZE = 100

# Save progress every N speeches (for resumability)
SAVE_EVERY = 5000

# Maximum text length to process (spaCy has limits)
MAX_TEXT_LENGTH = 100000

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_spacy_model(model_name: str):
    """Load spaCy model, with helpful error message if not installed."""
    try:
        nlp = spacy.load(model_name)
        print(f"Loaded spaCy model: {model_name}")
        return nlp
    except OSError:
        print(f"\nERROR: spaCy model '{model_name}' not found!")
        print(f"Install it with: python -m spacy download {model_name}")
        sys.exit(1)

def process_text_with_spacy(doc) -> Dict:
    """
    Extract linguistic features from a spaCy Doc object.
    """
    # Extract lemmas (lowercase, excluding punctuation and spaces)
    lemmas = [token.lemma_.lower() for token in doc 
              if not token.is_punct and not token.is_space]
    
    # Extract POS tags (aligned with lemmas)
    pos_tags = [token.pos_ for token in doc 
                if not token.is_punct and not token.is_space]
    
    # Extract named entities
    entities = [f"{ent.text}|{ent.label_}" for ent in doc.ents]
    
    return {
        'lemmas': ' '.join(lemmas),
        'pos_tags': ' '.join(pos_tags),
        'entities': ';'.join(entities) if entities else '',
        'n_tokens': len(lemmas),
        'n_sentences': len(list(doc.sents))
    }

def load_progress() -> int:
    """Load progress from temporary file. Returns number of rows already processed."""
    if PROGRESS_CSV.exists():
        try:
            progress_df = pd.read_csv(PROGRESS_CSV)
            return len(progress_df)
        except Exception as e:
            print(f"Warning: Could not read progress file: {e}")
            return 0
    return 0

def save_progress(results: List[Dict], append: bool = True):
    """Save processed results to progress file."""
    df = pd.DataFrame(results)
    
    if append and PROGRESS_CSV.exists():
        df.to_csv(PROGRESS_CSV, mode='a', header=False, index=False)
    else:
        df.to_csv(PROGRESS_CSV, index=False)

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def main():
    print("="*60)
    print("SPACY PROCESSING - Italian Parliamentary Corpus")
    print("="*60)
    
    # Check input file exists
    if not INPUT_CSV.exists():
        print(f"\nERROR: Input file not found: {INPUT_CSV}")
        print("Run segment_speakers.py first (Phase 2)")
        sys.exit(1)
    
    # Load spaCy model
    print(f"\nLoading spaCy model: {SPACY_MODEL}")
    nlp = load_spacy_model(SPACY_MODEL)
    nlp.max_length = MAX_TEXT_LENGTH
    
    # Load input data
    print(f"\nLoading speeches from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    total_speeches = len(df)
    print(f"Total speeches in corpus: {total_speeches:,}")
    
    # Check for existing progress
    already_processed = load_progress()
    
    if already_processed > 0:
        print(f"\n*** RESUMING: Found {already_processed:,} already processed ***")
        print(f"    Remaining: {total_speeches - already_processed:,} speeches")
        start_idx = already_processed
    else:
        print(f"\nStarting fresh processing...")
        start_idx = 0
    
    # Prepare texts to process
    texts = df['text'].fillna('').tolist()
    
    # Process remaining speeches
    print(f"\nProcessing with spaCy (batch size: {BATCH_SIZE})...")
    print(f"Progress will be saved every {SAVE_EVERY:,} speeches\n")
    
    batch_results = []
    
    for i in tqdm(range(start_idx, total_speeches), 
                  desc="Processing", 
                  initial=start_idx, 
                  total=total_speeches):
        
        # Get text (truncate if too long)
        text = texts[i]
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        
        # Process with spaCy
        doc = nlp(text)
        features = process_text_with_spacy(doc)
        features['original_index'] = i
        batch_results.append(features)
        
        # Save progress periodically
        if len(batch_results) >= SAVE_EVERY:
            save_progress(batch_results, append=(start_idx > 0 or i > SAVE_EVERY))
            print(f"\n  [Saved progress: {i+1:,}/{total_speeches:,} speeches]")
            batch_results = []
    
    # Save any remaining results
    if batch_results:
        save_progress(batch_results, append=(start_idx > 0 or total_speeches > SAVE_EVERY))
        print(f"\n  [Saved final batch]")
    
    # Now merge with original data
    print("\nMerging results with original data...")
    results_df = pd.read_csv(PROGRESS_CSV)
    results_df = results_df.sort_values('original_index').reset_index(drop=True)
    
    # Add columns to original dataframe
    df['lemmas'] = results_df['lemmas']
    df['pos_tags'] = results_df['pos_tags']
    df['entities'] = results_df['entities']
    df['n_tokens'] = results_df['n_tokens']
    df['n_sentences'] = results_df['n_sentences']
    
    # Save final output
    print(f"\nSaving final output to: {OUTPUT_CSV}")
    df.to_csv(OUTPUT_CSV, index=False)
    
    # Clean up progress file
    if PROGRESS_CSV.exists():
        os.remove(PROGRESS_CSV)
        print("Cleaned up temporary progress file.")
    
    # Print summary
    print(f"\n{'='*60}")
    print("OUTPUT SUMMARY")
    print(f"{'='*60}")
    print(f"Total speeches processed: {len(df):,}")
    print(f"Output file: {OUTPUT_CSV}")
    print(f"File size: {OUTPUT_CSV.stat().st_size / (1024*1024):.1f} MB")
    
    print(f"\nAverage tokens per speech: {df['n_tokens'].mean():.0f}")
    print(f"Average sentences per speech: {df['n_sentences'].mean():.1f}")
    
    entities_count = df['entities'].str.count(';').sum() + (df['entities'] != '').sum()
    print(f"Total named entities found: {entities_count:,}")
    
    print("\n✅ DONE! Ready for Phase 4 (smart filtering)")

if __name__ == "__main__":
    main()
