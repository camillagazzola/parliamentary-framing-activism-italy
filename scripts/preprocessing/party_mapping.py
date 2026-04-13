#!/usr/bin/env python3
"""
party_mapping.py
----------------
Party name normalization for Italian Parliament (2018-2025)

This maps the various party abbreviations found in transcripts to 
standardized names and political position categories.

Use this to:
1. Normalize party names in your corpus
2. Add political position (left/center/right) for analysis
3. Handle party name changes across legislatures

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

# =============================================================================
# PARTY MAPPING: Raw abbreviation -> Standardized name
# =============================================================================

# Legislature XVIII (2018-2022) and XIX (2022-present)
PARTY_MAPPING = {
    # === CENTRO-DESTRA (Right/Center-Right) ===
    
    # Fratelli d'Italia
    'FDI': 'FDI',
    'FRATELLI D\'ITALIA': 'FDI',
    'FD\'I': 'FDI',
    "FD'I": 'FDI',
    
    # Lega
    'LEGA': 'LEGA',
    'LEGA-SALVINI': 'LEGA',
    'LEGA-SP': 'LEGA',
    'L-SP': 'LEGA',
    'LSP-PSD\'AZ': 'LEGA',
    'LEGA SALVINI PREMIER': 'LEGA',
    
    # Forza Italia
    'FI': 'FI',
    'FI-PPE': 'FI',
    'FORZA ITALIA': 'FI',
    'FORZA ITALIA-PPE': 'FI',
    'FI-B-P-P': 'FI',
    
    # Noi Moderati / UDC / Centrist right
    'NM': 'NM',
    'NM(N-C-U-I)': 'NM',
    'NM(N-C-U-I)-M': 'NM',
    'NOI MODERATI': 'NM',
    'UDC': 'NM',
    
    # === CENTRO-SINISTRA (Left/Center-Left) ===
    
    # Partito Democratico
    'PD': 'PD',
    'PD-IDP': 'PD',
    'PARTITO DEMOCRATICO': 'PD',
    
    # Movimento 5 Stelle
    'M5S': 'M5S',
    'MOV5STELLE': 'M5S',
    'MOVIMENTO 5 STELLE': 'M5S',
    
    # Italia Viva / Azione
    'IV': 'IV',
    'IV-C-RE': 'IV',
    'ITALIA VIVA': 'IV',
    'AZ-IV-RE': 'AZIONE-IV',
    'AZIONE-IV': 'AZIONE-IV',
    'AZIONE': 'AZIONE-IV',
    'AZ': 'AZIONE-IV',
    'A-IV-RE': 'AZIONE-IV',
    
    # Alleanza Verdi Sinistra
    'AVS': 'AVS',
    'VERDI': 'AVS',
    'SI': 'AVS',  # Sinistra Italiana
    'SINISTRA ITALIANA': 'AVS',
    'EUROPA VERDE': 'AVS',
    
    # Liberi e Uguali (Leg XVIII)
    'LEU': 'LEU',
    'LIBERI E UGUALI': 'LEU',
    'LEUS': 'LEU',
    
    # +Europa
    '+EUROPA': '+EUROPA',
    'PIU EUROPA': '+EUROPA',
    '+E': '+EUROPA',
    'MISTO-+EUROPA': '+EUROPA',
    
    # === MISTO (Mixed Group) ===
    'MISTO': 'MISTO',
    'MISTO-NCI': 'MISTO',
    'MISTO-MIN.LING.': 'MISTO',
    'MISTO-MAIE': 'MISTO',
    'MISTO-CD': 'MISTO',
    'MISTO-PSI': 'MISTO',
    'M-NCI-USEI-C!-AC': 'MISTO',
    
    # === INSTITUTIONAL (Non-party) ===
    'PRESIDENTE': 'PRESIDENTE',
    '': '',
}

# =============================================================================
# POLITICAL POSITION MAPPING
# =============================================================================

POLITICAL_POSITION = {
    # Right
    'FDI': 'right',
    'LEGA': 'right',
    
    # Center-Right
    'FI': 'center-right',
    'NM': 'center-right',
    
    # Center
    'IV': 'center',
    'AZIONE-IV': 'center',
    '+EUROPA': 'center',
    
    # Center-Left
    'PD': 'center-left',
    
    # Left
    'AVS': 'left',
    'LEU': 'left',
    
    # Populist/Other
    'M5S': 'populist',
    
    # Mixed/Unknown
    'MISTO': 'mixed',
    'PRESIDENTE': 'institutional',
    '': 'unknown',
}

# =============================================================================
# GOVERNMENT POSITION (by period)
# =============================================================================

# Governo Conte I: June 2018 - September 2019 (M5S + Lega)
# Governo Conte II: September 2019 - February 2021 (M5S + PD + LEU + IV)
# Governo Draghi: February 2021 - October 2022 (unity government)
# Governo Meloni: October 2022 - present (FDI + Lega + FI + NM)

def get_government_position(party: str, date: str) -> str:
    """
    Determine if party is in government or opposition at a given date.
    
    Args:
        party: Normalized party name
        date: ISO date string (YYYY-MM-DD)
    
    Returns:
        'government', 'opposition', or 'unknown'
    """
    if not date or not party:
        return 'unknown'
    
    try:
        from datetime import datetime
        d = datetime.strptime(date, '%Y-%m-%d')
    except:
        return 'unknown'
    
    # Conte I (June 2018 - Sept 2019)
    if d < datetime(2019, 9, 5):
        government = ['M5S', 'LEGA']
    # Conte II (Sept 2019 - Feb 2021)
    elif d < datetime(2021, 2, 13):
        government = ['M5S', 'PD', 'LEU', 'IV', '+EUROPA']
    # Draghi (Feb 2021 - Oct 2022)
    elif d < datetime(2022, 10, 22):
        government = ['M5S', 'PD', 'LEU', 'IV', 'FI', 'LEGA', '+EUROPA', 'AZIONE-IV']
    # Meloni (Oct 2022 - present)
    else:
        government = ['FDI', 'LEGA', 'FI', 'NM']
    
    if party in government:
        return 'government'
    elif party in ['PRESIDENTE', 'MISTO', '']:
        return 'unknown'
    else:
        return 'opposition'


# =============================================================================
# NORMALIZATION FUNCTION
# =============================================================================

def normalize_party(raw_party: str) -> dict:
    """
    Normalize a raw party string and return enriched info.
    
    Returns dict with:
        - party: normalized party name
        - position: political position (left/right/center)
        - original: original string
    """
    if not raw_party:
        return {
            'party': '',
            'position': 'unknown',
            'original': ''
        }
    
    # Clean up
    raw_upper = raw_party.strip().upper()
    raw_upper = raw_upper.replace('–', '-').replace('—', '-')
    
    # Try direct lookup
    if raw_upper in PARTY_MAPPING:
        normalized = PARTY_MAPPING[raw_upper]
    else:
        # Try partial matches
        normalized = None
        for key, value in PARTY_MAPPING.items():
            if key and key in raw_upper:
                normalized = value
                break
        
        if normalized is None:
            normalized = raw_upper  # Keep original if no match
    
    position = POLITICAL_POSITION.get(normalized, 'unknown')
    
    return {
        'party': normalized,
        'position': position,
        'original': raw_party
    }


# =============================================================================
# ENRICHMENT FUNCTION (for use in pipeline)
# =============================================================================

def enrich_speeches_with_party_info(speeches_df):
    """
    Add normalized party and political position columns to speeches DataFrame.
    
    Args:
        speeches_df: DataFrame with 'party' and 'date' columns
    
    Returns:
        DataFrame with added columns:
            - party_normalized
            - political_position  
            - government_position
    """
    import pandas as pd
    
    # Normalize parties
    party_info = speeches_df['party'].apply(normalize_party)
    speeches_df['party_normalized'] = party_info.apply(lambda x: x['party'])
    speeches_df['political_position'] = party_info.apply(lambda x: x['position'])
    
    # Add government position if date available
    if 'date' in speeches_df.columns:
        speeches_df['government_position'] = speeches_df.apply(
            lambda row: get_government_position(row['party_normalized'], row['date']),
            axis=1
        )
    
    return speeches_df


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    # Test normalization
    test_parties = [
        'PD-IDP', 'FDI', 'LEGA', 'M5S', 'FI-PPE', 
        'IV-C-RE', 'AVS', 'MISTO-+EUROPA', '', None,
        'NM(N-C-U-I)-M', 'LEU'
    ]
    
    print("Party Normalization Test:")
    print("-" * 60)
    for raw in test_parties:
        result = normalize_party(raw)
        print(f"  '{raw}' -> {result['party']} ({result['position']})")
    
    print("\n\nGovernment Position Test (FDI):")
    print("-" * 60)
    test_dates = ['2019-01-15', '2020-06-01', '2021-06-01', '2023-01-15']
    for date in test_dates:
        pos = get_government_position('FDI', date)
        print(f"  {date}: {pos}")
