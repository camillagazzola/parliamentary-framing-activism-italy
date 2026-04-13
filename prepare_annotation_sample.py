#!/usr/bin/env python3
"""
prepare_annotation_sample.py
----------------------------
Prepares stratified samples for manual annotation.

This script creates TWO annotation files:
1. annotation_binary.csv - For Step 1: Is this speech genuinely about activism?
2. annotation_frames.csv - For Step 3: What frames are present? (use after)

The samples are STRATIFIED to ensure you see:
- Different chambers (Camera, Senato)
- Different years (2018-2024)
- Different matched terms (including high-risk ones)
- Different parties

WHY STRATIFIED SAMPLING?
If you randomly sample, you might get 80% "occupazione" speeches and miss 
rare but important terms like "ultima generazione" or "forza nuova".
Stratified sampling ensures diversity.

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
import sys

# =============================================================================
# CONFIGURATION - ADJUST THESE AS NEEDED
# =============================================================================

# Input: your filtered corpus from filter_smart_spacy.py
INPUT_CSV = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/activism_candidates_v3.csv")

# Output directory
OUTPUT_DIR = Path("data/annotation")

# Sample sizes
BINARY_SAMPLE_SIZE = 500      # For "is this activism?" labeling
FRAMES_SAMPLE_SIZE = 300      # For frame coding (use after binary filtering)

# High-risk terms that often produce false positives
HIGH_RISK_TERMS = ['occupare', 'occupazione', 'movimento', 'presidio', 'manifestazione']

# Specific movement/group names (important to capture)
SPECIFIC_GROUPS = [
    'ultima generazione', 'extinction rebellion', 'fridays for future',
    'casapound', 'forza nuova', 'centri sociali', 'no tav', 'no tap',
    'no vax', 'no green pass', 'sea watch', 'open arms'
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_primary_term(matched_terms_str):
    """Extract the first/primary matched term."""
    if pd.isna(matched_terms_str) or matched_terms_str == '':
        return 'unknown'
    terms = [t.strip().lower() for t in matched_terms_str.split(';')]
    return terms[0] if terms else 'unknown'


def is_high_risk(matched_terms_str):
    """Check if speech contains high-risk polysemous terms."""
    if pd.isna(matched_terms_str):
        return False
    terms = [t.strip().lower() for t in matched_terms_str.split(';')]
    return any(t in HIGH_RISK_TERMS for t in terms)


def has_specific_group(matched_terms_str):
    """Check if speech mentions specific activist groups."""
    if pd.isna(matched_terms_str):
        return False
    terms_lower = matched_terms_str.lower()
    return any(group in terms_lower for group in SPECIFIC_GROUPS)


def get_term_category(matched_terms_str):
    """Categorize speech by type of activism term."""
    if pd.isna(matched_terms_str):
        return 'unknown'
    
    terms = matched_terms_str.lower()
    
    # Check for specific groups first (highest priority)
    if has_specific_group(matched_terms_str):
        return 'specific_group'
    
    # Then check categories
    if any(t in terms for t in ['protesta', 'protestare', 'dissenso', 'contestazione']):
        return 'protest_dissent'
    if any(t in terms for t in ['manifestazione', 'corteo', 'sit-in']):
        return 'demonstration'
    if any(t in terms for t in ['sciopero', 'scioperare']):
        return 'strike'
    if any(t in terms for t in ['movimento', 'attivista', 'attivismo']):
        return 'movement_activism'
    if any(t in terms for t in ['occupazione', 'occupare', 'blocco']):
        return 'occupation_blockade'
    if any(t in terms for t in ['rivolta', 'sommossa', 'insurrezione']):
        return 'radical_boundary'
    if any(t in terms for t in ['repressione', 'manganello', 'lacrimogeno']):
        return 'repression'
    if any(t in terms for t in ['mobilitazione', 'mobilitare']):
        return 'mobilisation'
    
    return 'other'


def extract_context(text, max_chars=500):
    """Extract a readable context snippet."""
    if pd.isna(text):
        return ""
    text = str(text).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def create_stratified_sample(df, n_samples, stratify_cols, random_state=42):
    """
    Create a stratified sample ensuring representation across multiple dimensions.
    
    This is more sophisticated than simple random sampling because it ensures
    you see examples from different:
    - Years
    - Chambers  
    - Term categories
    - Risk levels
    """
    np.random.seed(random_state)
    
    # Create stratification key
    df = df.copy()
    df['_strat_key'] = df[stratify_cols].astype(str).agg('_'.join, axis=1)
    
    # Count per stratum
    strat_counts = df['_strat_key'].value_counts()
    
    # Allocate samples proportionally, with minimum of 1 per stratum
    total = len(df)
    samples = []
    allocated = 0
    
    for strat_key in strat_counts.index:
        strat_df = df[df['_strat_key'] == strat_key]
        
        # Proportional allocation
        n_alloc = max(1, int(round(len(strat_df) / total * n_samples)))
        n_alloc = min(n_alloc, len(strat_df), n_samples - allocated)
        
        if n_alloc > 0 and allocated < n_samples:
            sample = strat_df.sample(n=n_alloc, random_state=random_state)
            samples.append(sample)
            allocated += n_alloc
    
    result = pd.concat(samples, ignore_index=True)
    
    # If we haven't reached target, add more randomly
    if len(result) < n_samples:
        remaining = df[~df.index.isin(result.index)]
        n_more = min(n_samples - len(result), len(remaining))
        if n_more > 0:
            more = remaining.sample(n=n_more, random_state=random_state)
            result = pd.concat([result, more], ignore_index=True)
    
    # Shuffle final result
    result = result.sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    # Remove helper column
    result = result.drop(columns=['_strat_key'], errors='ignore')
    
    return result.head(n_samples)


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def main():
    print("=" * 70)
    print("ANNOTATION SAMPLE PREPARATION")
    print("=" * 70)
    
    # Check input exists
    if not INPUT_CSV.exists():
        print(f"\n❌ ERROR: Input file not found: {INPUT_CSV}")
        print("Please run filter_smart_spacy.py first")
        sys.exit(1)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"\n📂 Loading data from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"   Loaded {len(df):,} speeches")
    
    # =================================================================
    # ADD HELPER COLUMNS FOR STRATIFICATION
    # =================================================================
    print("\n🔧 Preparing stratification columns...")
    
    # Extract year from date
    if 'year' not in df.columns:
        if 'date' in df.columns:
            df['year'] = pd.to_datetime(df['date'], errors='coerce').dt.year
        else:
            df['year'] = 'unknown'
    
    # Add categorization columns
    df['term_category'] = df['matched_terms'].apply(get_term_category)
    df['is_high_risk'] = df['matched_terms'].apply(is_high_risk)
    df['has_specific_group'] = df['matched_terms'].apply(has_specific_group)
    df['primary_term'] = df['matched_terms'].apply(get_primary_term)
    
    # Create risk stratum (for stratification)
    df['risk_stratum'] = df.apply(
        lambda row: 'specific_group' if row['has_specific_group'] 
                    else ('high_risk' if row['is_high_risk'] else 'standard'),
        axis=1
    )
    
    # =================================================================
    # PRINT CORPUS OVERVIEW
    # =================================================================
    print("\n📊 CORPUS OVERVIEW")
    print("-" * 50)
    print(f"   Total speeches: {len(df):,}")
    print(f"\n   By chamber:")
    for chamber, count in df['chamber'].value_counts().items():
        print(f"      {chamber}: {count:,} ({count/len(df)*100:.1f}%)")
    
    print(f"\n   By year:")
    for year, count in df['year'].value_counts().sort_index().items():
        print(f"      {year}: {count:,} ({count/len(df)*100:.1f}%)")
    
    print(f"\n   By term category:")
    for cat, count in df['term_category'].value_counts().items():
        print(f"      {cat}: {count:,} ({count/len(df)*100:.1f}%)")
    
    print(f"\n   By risk level:")
    for risk, count in df['risk_stratum'].value_counts().items():
        print(f"      {risk}: {count:,} ({count/len(df)*100:.1f}%)")
    
    # =================================================================
    # CREATE BINARY ANNOTATION SAMPLE (Step 1)
    # =================================================================
    print("\n" + "=" * 70)
    print("CREATING BINARY ANNOTATION SAMPLE")
    print("=" * 70)
    
    # Stratify by: chamber, year, risk_stratum
    binary_sample = create_stratified_sample(
        df, 
        n_samples=BINARY_SAMPLE_SIZE,
        stratify_cols=['chamber', 'year', 'risk_stratum'],
        random_state=42
    )
    
    # Add annotation columns
    binary_sample = binary_sample.copy()
    binary_sample['context_snippet'] = binary_sample['text'].apply(
        lambda x: extract_context(x, max_chars=600)
    )
    
    # Columns for annotation
    binary_sample['is_activism_related'] = ''  # 1 = yes, 0 = no
    binary_sample['confidence'] = ''           # 1 = certain, 2 = probable, 3 = uncertain
    binary_sample['if_no_reason'] = ''         # Why is this NOT about activism?
    binary_sample['notes'] = ''                # Any additional notes
    
    # Select and order columns for the annotation file
    binary_cols = [
        'chamber', 'year', 'date', 'speaker', 'party',
        'matched_terms', 'primary_term', 'is_high_risk', 'risk_stratum',
        'context_snippet',
        'is_activism_related', 'confidence', 'if_no_reason', 'notes',
        'text'  # Full text at the end for reference
    ]
    
    # Keep only columns that exist
    binary_cols = [c for c in binary_cols if c in binary_sample.columns]
    binary_sample = binary_sample[binary_cols]
    
    # Save
    binary_path = OUTPUT_DIR / "annotation_binary.csv"
    binary_sample.to_csv(binary_path, index_label='sample_id')
    
    print(f"\n✅ Binary annotation sample saved to: {binary_path}")
    print(f"   Sample size: {len(binary_sample)}")
    print(f"\n   Sample breakdown:")
    print(f"      High-risk terms: {binary_sample['is_high_risk'].sum()}")
    print(f"      Specific groups: {(binary_sample['risk_stratum'] == 'specific_group').sum()}")
    for chamber, count in binary_sample['chamber'].value_counts().items():
        print(f"      {chamber}: {count}")
    
    # =================================================================
    # CREATE FRAMES ANNOTATION SAMPLE (Step 3 - use after filtering)
    # =================================================================
    print("\n" + "=" * 70)
    print("CREATING FRAMES ANNOTATION SAMPLE")
    print("=" * 70)
    
    # For frames, we want diversity in term categories
    frames_sample = create_stratified_sample(
        df,
        n_samples=FRAMES_SAMPLE_SIZE,
        stratify_cols=['chamber', 'year', 'term_category'],
        random_state=123  # Different seed for different sample
    )
    
    # Add annotation columns for frames
    frames_sample = frames_sample.copy()
    frames_sample['context_snippet'] = frames_sample['text'].apply(
        lambda x: extract_context(x, max_chars=600)
    )
    
    # Frame columns (from your research proposal)
    frames_sample['frame_security'] = ''           # 0 = absent, 1 = present
    frames_sample['frame_legality'] = ''           # 0 = absent, 1 = present
    frames_sample['frame_morality'] = ''           # 0 = absent, 1 = present
    frames_sample['frame_national_identity'] = ''  # 0 = absent, 1 = present
    frames_sample['frame_humanitarianism'] = ''    # 0 = absent, 1 = present
    frames_sample['frame_public_order'] = ''       # 0 = absent, 1 = present
    
    # Additional metadata
    frames_sample['activism_type'] = ''            # left-wing, right-wing, environmental, etc.
    frames_sample['tone'] = ''                     # positive, negative, neutral
    frames_sample['violence_attributed'] = ''      # 0 = no, 1 = yes
    frames_sample['legitimacy_stance'] = ''        # legitimizing, delegitimizing, neutral
    frames_sample['specific_group_mentioned'] = '' # Name of group if any
    frames_sample['coder_notes'] = ''
    
    # Select and order columns
    frames_cols = [
        'chamber', 'year', 'date', 'speaker', 'party',
        'matched_terms', 'term_category',
        'context_snippet',
        'frame_security', 'frame_legality', 'frame_morality',
        'frame_national_identity', 'frame_humanitarianism', 'frame_public_order',
        'activism_type', 'tone', 'violence_attributed', 
        'legitimacy_stance', 'specific_group_mentioned', 'coder_notes',
        'text'
    ]
    
    frames_cols = [c for c in frames_cols if c in frames_sample.columns]
    frames_sample = frames_sample[frames_cols]
    
    # Save
    frames_path = OUTPUT_DIR / "annotation_frames.csv"
    frames_sample.to_csv(frames_path, index_label='sample_id')
    
    print(f"\n✅ Frames annotation sample saved to: {frames_path}")
    print(f"   Sample size: {len(frames_sample)}")
    print(f"\n   Term category breakdown:")
    for cat, count in frames_sample['term_category'].value_counts().items():
        print(f"      {cat}: {count}")
    
    # =================================================================
    # PRINT INSTRUCTIONS
    # =================================================================
    print("\n" + "=" * 70)
    print("📋 ANNOTATION INSTRUCTIONS")
    print("=" * 70)
    print("""
    STEP 1: BINARY ANNOTATION (annotation_binary.csv)
    ─────────────────────────────────────────────────
    Open the file in Excel/Google Sheets and for EACH row:
    
    1. Read the 'context_snippet' (or full 'text' if needed)
    
    2. Fill 'is_activism_related':
       • 1 = YES, this speech genuinely discusses activism/protest/social movements
       • 0 = NO, this is a false positive (e.g., "occupazione" means employment)
    
    3. Fill 'confidence':
       • 1 = Certain (clear case)
       • 2 = Probable (fairly confident)
       • 3 = Uncertain (borderline case)
    
    4. If you coded 0 (not activism), fill 'if_no_reason':
       • "employment" - occupazione/occupare refers to jobs
       • "party_name" - movimento refers to M5S or similar
       • "metaphorical" - term used metaphorically
       • "procedural" - parliamentary procedure mention
       • "other" - explain in notes
    
    5. Add any 'notes' for ambiguous cases
    
    ⏱️  Expected time: ~2-3 hours for 500 speeches
    🎯 Target: Label ALL 500 speeches
    
    
    STEP 2: RUN ML CLASSIFIER (after binary annotation)
    ─────────────────────────────────────────────────────
    Once you've annotated annotation_binary.csv:
    • Run the ML training script (I'll provide this)
    • It will filter out false positives from your full corpus
    
    
    STEP 3: FRAMES ANNOTATION (annotation_frames.csv)
    ─────────────────────────────────────────────────
    After Step 2, annotate frames on the FILTERED corpus sample.
    
    For EACH row, code the following frames (0 = absent, 1 = present):
    
    • frame_security: Speech frames activism as security threat
      Keywords: sicurezza, minaccia, pericolo, ordine pubblico, violenza
    
    • frame_legality: Speech frames activism in legal terms
      Keywords: legale/illegale, diritto, reato, codice penale, sanzioni
    
    • frame_morality: Speech frames activism in moral terms
      Keywords: responsabilità, dovere, giusto/sbagliato, etico, valori
    
    • frame_national_identity: Speech invokes national identity
      Keywords: Italia, patria, nazione, popolo italiano, tradizione
    
    • frame_humanitarianism: Speech invokes human rights/dignity
      Keywords: diritti umani, dignità, libertà, democrazia, civile
    
    • frame_public_order: Speech frames activism re: public order
      Keywords: decoro, quiete pubblica, disturbo, blocco, disordine
    
    Also code:
    • activism_type: left-wing / right-wing / environmental / labor / other
    • tone: positive / negative / neutral (toward the activism)
    • violence_attributed: 1 if speech attributes violence to activists
    • legitimacy_stance: legitimizing / delegitimizing / neutral
    
    ⏱️  Expected time: ~4-5 hours for 300 speeches
    🎯 Target: Label ALL 300 speeches
    """)
    
    print("\n" + "=" * 70)
    print("✅ ANNOTATION FILES READY")
    print("=" * 70)
    print(f"""
    Files created in: {OUTPUT_DIR}/
    
    1. annotation_binary.csv  ({len(binary_sample)} speeches)
       → Start here! Label is_activism_related (1/0)
    
    2. annotation_frames.csv  ({len(frames_sample)} speeches)  
       → Use after running ML classifier on binary labels
    
    Next step: Open annotation_binary.csv and start labeling!
    """)


if __name__ == "__main__":
    main()
