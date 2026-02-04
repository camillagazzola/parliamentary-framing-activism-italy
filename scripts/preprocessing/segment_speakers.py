#!/usr/bin/env python3
"""
segment_speakers.py
-------------------
Phase 2: Speaker Segmentation for Italian Parliamentary Corpus

This script segments raw parliamentary transcripts (TXT files) into 
individual speeches. Each speech is associated with a speaker name,
party affiliation, and metadata.

Input:
    - Raw TXT files from Camera dei Deputati and Senato della Repubblica
    - Camera: leg18_txt and leg19_txt folders
    - Senato: yearly folders (2018-2025)

Output:
    - CSV file: speeches_raw.csv
    - One row per speech with columns:
        speech_id, session_id, speaker, party, chamber, text, n_chars

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# =============================================================================
# CONFIGURATION - Modify these paths for your setup
# =============================================================================

# Camera directories (one per legislature)
CAMERA_DIRS = [
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Camera/leg18_txt"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Camera/leg19_txt"),
]

# Senato directories (yearly folders)
SENATO_DIRS = [
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2018"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2019"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2020"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2021"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2022"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2022.18"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2023"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2024"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Senato/senato_txt/2025"),
]

# Output file - will be created in your project folder
OUTPUT_CSV = Path("data/processed/speeches_raw.csv")

# =============================================================================
# REGEX PATTERNS FOR SPEAKER IDENTIFICATION
# =============================================================================

# Camera dei Deputati pattern
# Examples:
#   "RICCARDO MAGI (MISTO-+EUROPA). Text..."
#   "RICCARDO MAGI ( MISTO-+EUROPA). Text..."
#   "PRESIDENTE. Text..."
#   "FRANCESCO BATTISTONI , Segretario, legge..."

CAMERA_SPEAKER_PATTERN = re.compile(
    r"""
    \n\s*                                    # Newline + optional whitespace
    ([A-ZÀÈÉÌÒÙ][A-ZÀÈÉÌÒÙ\s'\.]+?)          # Speaker name (UPPERCASE with accents)
    \s*                                      # Optional space
    (?:
        \(\s*([A-Za-z0-9\-\+\/\(\)]+)\s*\)   # Party in parentheses
        |
        ,\s*(?:Segretario|segretario)        # Or ", Segretario"
    )?
    \s*\.                                    # Period after name/party
    \s+                                      # Whitespace before speech text
    """,
    re.VERBOSE | re.MULTILINE
)

# Senato della Repubblica pattern
# Examples:
#   "VALENTE (PD). Domando di parlare."
#   "SBROLLINI (IV-PSI). Signora Presidente..."
#   "PRESIDENTE. La seduta è aperta..."
#   "GIRO, segretario, dà lettura..."

SENATO_SPEAKER_PATTERN = re.compile(
    r"""
    \n\s*                                    # Newline + optional whitespace
    ([A-ZÀÈÉÌÒÙ][A-Za-zàèéìòù\s'\.]+?)       # Speaker name (First letter uppercase)
    \s*                                      # Optional space
    (?:
        \(\s*([A-Za-z0-9\-\+\/\(\)\s]+?)\s*\)  # Party in parentheses
        |
        ,\s*(?:segretario|Segretario)        # Or ", segretario"
    )?
    \s*\.                                    # Period after name/party
    \s+                                      # Whitespace before speech text
    """,
    re.VERBOSE | re.MULTILINE
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_speaker_name(name: str) -> str:
    """Normalize speaker name (trim, collapse whitespace)."""
    name = re.sub(r'\s+', ' ', name.strip())
    return name.upper()  # Standardize to uppercase

def clean_party(party: Optional[str]) -> str:
    """Normalize party abbreviation."""
    if party is None:
        return ""
    party = re.sub(r'\s+', '', party.strip())  # Remove all whitespace
    return party.upper()

def clean_speech_text(text: str) -> str:
    """Clean speech text (normalize whitespace, remove page headers)."""
    # Remove page headers like "Atti Parlamentari — 5 — Camera dei Deputati"
    text = re.sub(
        r'Atti Parlamentari\s*[—–-]\s*\d+\s*[—–-]\s*(?:Camera dei Deputati|Senato della Repubblica)',
        ' ',
        text
    )
    # Remove legislature headers
    text = re.sub(
        r'X+I*V*\s+LEGISLATURA\s*[—–-]\s*DISCUSSIONI.*?(?=\n|$)',
        ' ',
        text
    )
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_session_id(filepath: Path) -> str:
    """Extract session ID from filename."""
    # Camera: sed0590.txt -> sed0590
    # Senato: BGT_1360790.txt -> BGT_1360790
    return filepath.stem

def is_procedural_text(text: str) -> bool:
    """Check if speech is purely procedural (very short or boilerplate)."""
    procedural_phrases = [
        'la seduta è aperta',
        'la seduta comincia',
        'ne ha facoltà',
        'domando di parlare',
        'è approvato',
        'si intende approvato',
        'è così stabilito',
        'passiamo al'
    ]
    text_lower = text.lower()
    # Very short texts that match procedural patterns
    if len(text) < 50:
        for phrase in procedural_phrases:
            if phrase in text_lower:
                return True
    return False

def find_transcript_start(text: str) -> int:
    """
    Find where the actual transcript begins (after index/header section).
    Look for markers like "RESOCONTO STENOGRAFICO" followed by "PRESIDENZA"
    or "La seduta comincia" or "La seduta è aperta".
    """
    # Patterns that indicate actual transcript content
    start_markers = [
        r'La seduta comincia',
        r'La seduta è aperta',
        r'RESOCONTO STENOGRAFICO\s+PRESIDENZA',
        r'Presidenza del (?:presidente|vice\s*presidente)',
    ]
    
    for marker in start_markers:
        match = re.search(marker, text, re.IGNORECASE)
        if match:
            # Return position just before this match
            return max(0, match.start() - 50)
    
    # Fallback: look for "N.B." section end or page marker
    nb_match = re.search(r'MISTO-\+EUROPA\.?\s*\n', text)
    if nb_match:
        return nb_match.end()
    
    return 0  # Start from beginning if no marker found

def segment_speeches(
    text: str, 
    pattern: re.Pattern,
    chamber: str
) -> List[Dict]:
    """
    Segment a transcript into individual speeches.
    
    Returns a list of dictionaries with speaker, party, text.
    """
    speeches = []
    
    # Skip the index/header section
    start_pos = find_transcript_start(text)
    text_to_parse = text[start_pos:]
    
    # Find all speaker matches
    matches = list(pattern.finditer(text_to_parse))
    
    if not matches:
        return speeches
    
    for i, match in enumerate(matches):
        speaker = clean_speaker_name(match.group(1))
        party = clean_party(match.group(2) if len(match.groups()) > 1 else None)
        
        # Get the text of this speech (until next speaker or end of document)
        speech_start = match.end()
        if i + 1 < len(matches):
            speech_end = matches[i + 1].start()
        else:
            speech_end = len(text_to_parse)
        
        speech_text = text_to_parse[speech_start:speech_end]
        speech_text = clean_speech_text(speech_text)
        
        # Skip if too short (likely just "Ne ha facoltà" or similar)
        if len(speech_text) < 20:
            continue
            
        # Skip if speaker name is clearly not a person (index artifacts)
        skip_speakers = [
            'ALLEGATO', 'INDICE', 'N.B', 'NOTA', 'RESOCONTO',
            'PRESIDENTE.', 'PRESIDENTE..', 'PRESIDENTE...', 
            'PRESIDENZA DEL', 'LETTERA DEL'
        ]
        if any(speaker.startswith(s) for s in skip_speakers):
            # Only skip if it looks like index content (has page numbers or dots)
            if re.search(r'\.{3,}|\d+,\s*\d+', speech_text[:100]):
                continue
        
        speeches.append({
            'speaker': speaker,
            'party': party,
            'text': speech_text,
            'n_chars': len(speech_text),
            'is_procedural': is_procedural_text(speech_text)
        })
    
    return speeches

def process_file(filepath: Path, chamber: str) -> List[Dict]:
    """Process a single transcript file."""
    try:
        text = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []
    
    # Choose pattern based on chamber
    pattern = CAMERA_SPEAKER_PATTERN if chamber == "Camera" else SENATO_SPEAKER_PATTERN
    
    # Segment into speeches
    speeches = segment_speeches(text, pattern, chamber)
    
    # Add metadata
    session_id = extract_session_id(filepath)
    for i, speech in enumerate(speeches):
        speech['speech_id'] = f"{session_id}_sp{i:04d}"
        speech['session_id'] = session_id
        speech['chamber'] = chamber
        speech['source_file'] = str(filepath.name)
    
    return speeches

def process_corpus(
    camera_dirs: list,
    senato_dirs: list,
    output_path: Path
) -> None:
    """Process all files in the corpus."""
    all_speeches = []
    
    # Process Camera files (multiple directories)
    camera_files = []
    for cam_dir in camera_dirs:
        if cam_dir.exists():
            found_files = sorted(cam_dir.glob("*.txt"))
            camera_files.extend(found_files)
            print(f"  Found {len(found_files)} files in {cam_dir.name}")
        else:
            print(f"WARNING: Camera directory not found: {cam_dir}")
    
    print(f"\nTotal Camera files: {len(camera_files)}")
    for filepath in camera_files:
        speeches = process_file(filepath, "Camera")
        all_speeches.extend(speeches)
        if len(speeches) > 0:
            print(f"  {filepath.name}: {len(speeches)} speeches")
    
    # Process Senato files (multiple directories)
    senato_files = []
    for sen_dir in senato_dirs:
        if sen_dir.exists():
            found_files = sorted(sen_dir.glob("*.txt"))
            senato_files.extend(found_files)
            print(f"  Found {len(found_files)} files in {sen_dir.name}")
        else:
            print(f"WARNING: Senato directory not found: {sen_dir}")
    
    print(f"\nTotal Senato files: {len(senato_files)}")
    for filepath in senato_files:
        speeches = process_file(filepath, "Senato")
        all_speeches.extend(speeches)
        if len(speeches) > 0:
            print(f"  {filepath.name}: {len(speeches)} speeches")
    
    # Write output
    if all_speeches:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'speech_id', 'session_id', 'chamber', 'speaker', 'party',
            'text', 'n_chars', 'is_procedural', 'source_file'
        ]
        
        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_speeches)
        
        print(f"\n{'='*60}")
        print(f"OUTPUT SUMMARY")
        print(f"{'='*60}")
        print(f"Total speeches extracted: {len(all_speeches)}")
        print(f"Output file: {output_path}")
        
        # Summary statistics
        camera_speeches = [s for s in all_speeches if s['chamber'] == 'Camera']
        senato_speeches = [s for s in all_speeches if s['chamber'] == 'Senato']
        procedural = [s for s in all_speeches if s['is_procedural']]
        
        print(f"\nBy chamber:")
        print(f"  Camera: {len(camera_speeches)} speeches")
        print(f"  Senato: {len(senato_speeches)} speeches")
        print(f"\nProcedural speeches (short/boilerplate): {len(procedural)}")
        print(f"Substantive speeches: {len(all_speeches) - len(procedural)}")
        
        # Average speech length
        avg_chars = sum(s['n_chars'] for s in all_speeches) / len(all_speeches)
        print(f"\nAverage speech length: {avg_chars:.0f} characters")
    else:
        print("No speeches extracted!")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("SPEAKER SEGMENTATION - Italian Parliamentary Corpus")
    print("="*60)
    print(f"\nCamera directories: {len(CAMERA_DIRS)}")
    for d in CAMERA_DIRS:
        print(f"  - {d}")
    print(f"\nSenato directories: {len(SENATO_DIRS)}")
    for d in SENATO_DIRS:
        print(f"  - {d}")
    print(f"\nOutput file: {OUTPUT_CSV}\n")
    
    process_corpus(CAMERA_DIRS, SENATO_DIRS, OUTPUT_CSV)