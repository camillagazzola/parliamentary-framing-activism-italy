#!/usr/bin/env python3
"""
segment_speakers_v6.py
----------------------
Phase 2: Speaker Segmentation for Italian Parliamentary Corpus

VERSION 6: Uses metadata files for dates instead of parsing from text headers

Input:
    - Raw TXT files from Camera dei Deputati and Senato della Repubblica
    - Metadata CSVs with correct dates

Output:
    - data/processed/speeches_raw_v6.csv

Author: Camilla Gazzola
Project: Italian Parliament Activism Framing (2018-2025)
"""

import re
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

CAMERA_DIRS = [
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Camera/leg18_txt"),
    Path("/Users/camillagazzola/Desktop/data/raw_data/TXTs/Camera/leg19_txt"),
]

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

# Metadata files
CAMERA_META = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/raw/camera_metadata_leg18_19.csv")
SENATO_META = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/raw/senato_metadata_2018_2025_from_txt.csv")

OUTPUT_CSV = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v6.csv")

# =============================================================================
# LOAD METADATA
# =============================================================================

def load_metadata():
    """Load metadata and create lookup dictionaries by leg+filename."""
    
    # Camera metadata - key is "leg18_sed0001.txt" or "leg19_sed0001.txt"
    camera_lookup = {}
    if CAMERA_META.exists():
        camera_df = pd.read_csv(CAMERA_META)
        for _, row in camera_df.iterrows():
            # Extract filename from txt_path: sed0001.txt
            filename = Path(row['txt_path']).name
            leg = int(row['legislature']) if pd.notna(row['legislature']) else None
            
            # Create unique key: leg18_sed0001.txt or leg19_sed0001.txt
            key = f"leg{leg}_{filename}" if leg else filename
            
            # Convert date from DD/MM/YYYY to YYYY-MM-DD
            date_parts = str(row['date_iso']).split('/')
            if len(date_parts) == 3:
                date_iso = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                year = int(date_parts[2])
            else:
                date_iso = None
                year = None
            
            camera_lookup[key] = {
                'date': date_iso,
                'year': year,
                'legislature': leg,
                'seduta_number': int(row['seduta']) if pd.notna(row['seduta']) else None,
            }
        print(f"  Loaded {len(camera_lookup)} Camera metadata entries")
    
    # Senato metadata
    senato_lookup = {}
    if SENATO_META.exists():
        senato_df = pd.read_csv(SENATO_META)
        for _, row in senato_df.iterrows():
            # Extract filename from txt_path: BGT_1066733.txt
            filename = Path(row['txt_path']).name
            
            # Use year_folder directly - it's always correct!
            year = int(row['year_folder']) if pd.notna(row['year_folder']) else None
            
            # Convert date from DD/MM/YYYY to YYYY-MM-DD
            date_parts = str(row['date_iso']).split('/')
            if len(date_parts) == 3:
                date_iso = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
            else:
                date_iso = None
            
            # Determine legislature from year
            if year:
                legislature = 18 if year < 2022 or (year == 2022 and row.get('seduta_n', 999) < 500) else 19
            else:
                legislature = None
            
            senato_lookup[filename] = {
                'date': date_iso,
                'year': year,
                'legislature': legislature,
                'seduta_number': int(row['seduta_n']) if pd.notna(row['seduta_n']) else None,
            }
        print(f"  Loaded {len(senato_lookup)} Senato metadata entries")
    
    return camera_lookup, senato_lookup

# =============================================================================
# KNOWN SINGLE-WORD SPEAKERS
# =============================================================================

KNOWN_SINGLE_SPEAKERS = {
    'PRESIDENTE',
    'TAJANI', 'SALVINI', 'MELONI', 'CONTE', 'DRAGHI',
    'RENZI', 'LETTA', 'BERLUSCONI', 'GRILLO', 'CASELLATI', 'FICO',
    'FONTANA', 'CALDEROLI', 'GASPARRI', 'CIRIANI', 'NORDIO', 'CROSETTO',
    'PIANTEDOSI', 'GIORGETTI', 'URSO', 'LOLLOBRIGIDA', 'SANTANCHÈ',
    'FITTO', 'MUSUMECI', 'LOCATELLI', 'SCHILLACI', 'ZANGRILLO',
    'CASINI', 'BOSCHI', 'DELRIO', 'ORLANDO', 'GUERINI', 'FRANCESCHINI',
    'BONAFEDE', 'AZZOLINA', 'SPERANZA', 'LAMORGESE', 'GUALTIERI',
    'PATUANELLI', 'CATALFO', 'DADONE', 'COSTA', 'BONETTI', 'SPADAFORA',
    'MAGNI', 'MALPEZZI', 'MARCUCCI', 'MALAN', 'ALFIERI', 'BAZOLI',
    'SCALFAROTTO', 'NUGNES', 'ERRANI', 'CANGINI', 'FLORIDIA',
    'LICHERI', 'DAMIANI', 'ROMEO', 'BORGONZONI', 'CANDIANI',
    'TURCO', 'FERRARA', 'FINOCCHIARO', 'GINETTI', 'GRASSO',
    'IANNONE', 'LAFORGIA', 'LANNUTTI', 'LAUS', 'MAIORINO',
    'MONTEVECCHI', 'NANNICINI', 'PAROLI', 'PERILLI', 'PESCO',
    'PITTELLA', 'PRESUTTO', 'QUAGLIARIELLO', 'RICHETTI', 'RUOTOLO',
    'SANTILLO', 'SEGRE', 'STEFANI', 'TERNULLO', 'TOSATO',
    'VALENTE', 'VALLARDI', 'VERDUCCI', 'VITALI', 'ZAFFINI',
}

# =============================================================================
# FAKE SPEAKER PATTERNS
# =============================================================================

FAKE_SPEAKER_PATTERNS = [
    r'^NE HA FACOLTÀ',
    r'^DOMANDO DI PARLARE',
    r'^PASSIAMO ALLA VOTAZIONE',
    r'^PASSIAMO AI VOTI',
    r'^PASSIAMO ALL',
    r'^INDÌCO',
    r'^DICHIARO',
    r'^METTO AI VOTI',
    r'^PREGO',
    r'^PROCEDIAMO',
    r'^PROSEGUIAMO',
    r'^RINGRAZIO',
    r'^AVVERTO',
    r'^COMUNICO',
    r'^RICORDO',
    r'^RISULTATO DI VOTAZIONE',
    r'^TRASMISSIONE',
    r'^COMUNICAZIONI',
    r'^CONGEDI E MISSIONI',
    r'^DISEGNI DI LEGGE',
    r'^MOZIONI',
    r'^INTERPELLANZE',
    r'^INTERROGAZIONI',
    r'^RISOLUZIONI',
    r'^PETIZIONI',
    r'^ANNUNZIO',
    r'^DEFERIMENTO',
    r'^ALLEGATO',
    r'^INDICE',
    r'^PROGRAMMA DEI LAVORI',
    r'^CALENDARIO DEI LAVORI',
    r'^ORDINE DEL GIORNO',
    r'^ACCETTAZIONE DIMISSIONI',
    r'^DOC\b',
    r'^ART\b',
    r'^N\.\s*\d',
    r'^I\.\s',
    r'^II\.\s',
    r'^III\.\s',
    r'^\d+[ªa°]?\s*SEDUTA',
    r'^SEDUTA',
    r'^RESOCONTO',
    r'^ASSEMBLEA',
    r'^LEGISLATURA',
    r'^SENATO',
    r'^CAMERA',
    r'^GOVERNO$',
    r'^REPUBBLICA',
    r'^ITALIA$',
    r'^EUROPA$',
    r'^STATO$',
    r'^COSTITUZIONE',
    r'^PARLAMENTO$',
    r'^COMMISSIONE$',
    r'^COMITATO$',
    r'^CORTE$',
    r'^CONSIGLIO$',
    r'^MINISTERO',
    r'^ROMA$',
    r'^MILANO$',
    r'^NAPOLI$',
    r'^REGIONE$',
    r'^PROVINCIA$',
    r'^QUESTO',
    r'^QUELLO',
    r'^SONO FATTI',
    r'^NON ESISTONO',
    r'^ABBIAMO',
    r'^AVETE',
    r'^IL PROVVEDIMENTO',
    r'^TALI RISOLUZIONI',
    r'^LO STESSO VALE',
    r'^BASTA SCORRERE',
    r'^NON È APPROVAT[OA]',
    r'^È APPROVAT[OA]',
    r'^SI DIA LETTURA',
    r'^VOTAZIONE',
    r"^SULL.ORDINE DEI LAVORI",
    r'^SUI LAVORI DEL',
    r'^LA CHIAMA',
    r'^PRESIDENZA DEL',
    r'^COMMEMORAZIONE',
    r'^SALUTO AD',
]

FAKE_SPEAKER_REGEX = [re.compile(p, re.IGNORECASE) for p in FAKE_SPEAKER_PATTERNS]

# =============================================================================
# HEADER/FOOTER PATTERNS
# =============================================================================

HEADER_PATTERNS = [
    r'Senato della Repubblica\s*[–—-]+\s*\d+\s*[–—-]+\s*X{1,2}I{0,3}V?\s*LEGISLATURA',
    r'\d+[ªa°]?\s*Seduta\s+(?:pubblica\s+)?ASSEMBLEA\s*[-–—]+\s*(?:RESOCONTO|INDICE|ALLEGATO)',
    r'ASSEMBLEA\s*[-–—]+\s*(?:RESOCONTO STENOGRAFICO|ALLEGATO\s*[AB]|INDICE)',
    r'Camera dei Deputati\s*[–—-]+\s*\d+\s*[–—-]+',
    r'Atti Parlamentari\s*[–—-]+\s*\d+\s*[–—-]+',
    r'X{1,2}I{0,3}V?\s*LEGISLATURA\s*[–—-]+\s*DISCUSSIONI',
    r'^\s*[–—-]+\s*\d{1,4}\s*[–—-]+\s*$',
    r'I\s+N\s+D\s+I\s+C\s+E',
    r'\.{5,}',
    r'N\.B\.\s+Sigle dei Gruppi parlamentari:.*?(?=\n\n|\Z)',
    r'PAGINA BIANCA',
    r'Stabilimenti Tipografici',
]

HEADER_REGEX = [re.compile(p, re.IGNORECASE | re.MULTILINE | re.DOTALL) for p in HEADER_PATTERNS]

# =============================================================================
# ENCODING FIXES
# =============================================================================

ENCODING_FIXES = {
    'Ã ': 'à', 'Ã¨': 'è', 'Ã©': 'é', 'Ã¬': 'ì', 'Ã²': 'ò', 'Ã¹': 'ù',
    'Ã€': 'À', 'Ãˆ': 'È', 'Ã‰': 'É', 'ÃŒ': 'Ì', 'Ã': 'Ò', 'Ã™': 'Ù',
    'â€™': "'", 'â€œ': '"', 'â€': '"', 'â€"': '–', 'â€"': '—',
    '‚Äì': '–', '‚Äô': "'", '‚Äú': '"', '‚Äù': '"',
    '√†': 'à', '√©': 'é', '√®': 'è', '√¨': 'ì', '√≤': 'ò', '√π': 'ù',
    'ï¬': 'fi', 'ï¬‚': 'fl',
}

# =============================================================================
# SPEAKER PATTERNS (CONSERVATIVE - NEWLINE BASED)
# =============================================================================

CAMERA_SPEAKER_PATTERN = re.compile(
    r'''
    (?:^|\n)                                    
    \s*                                         
    ([A-ZÀÈÉÌÒÙ][A-ZÀÈÉÌÒÙ\s'\-\.]{2,40}?)     
    \s*                                         
    (?:\(\s*([A-Za-z0-9\-\+\/\s]{1,30}?)\s*\))? 
    \s*\.                                       
    \s+                                         
    (?=[A-ZÀÈÉÌÒÙ])                             
    ''',
    re.VERBOSE | re.MULTILINE
)

SENATO_SPEAKER_PATTERN = re.compile(
    r'''
    (?:^|\n)                                    
    \s*                                         
    ([A-ZÀÈÉÌÒÙ][A-Za-zàèéìòù\s'\-\.]{1,40}?)  
    \s*                                         
    (?:
        \(\s*([A-Za-z0-9\-\+\/\(\)\s]{1,40}?)\s*\)
        |
        ,\s*[Ss]egretario
    )?
    \s*\.                                       
    \s+                                         
    (?=[A-ZÀÈÉÌÒÙ])                             
    ''',
    re.VERBOSE | re.MULTILINE
)

# =============================================================================
# TEXT CLEANING
# =============================================================================

def fix_encoding(text: str) -> str:
    for bad, good in ENCODING_FIXES.items():
        text = text.replace(bad, good)
    return text

def remove_headers(text: str) -> str:
    for pattern in HEADER_REGEX:
        text = pattern.sub(' ', text)
    return text

def fix_hyphenation(text: str) -> str:
    text = re.sub(r'(\w)-\s*\n\s*([a-zàèéìòù])', r'\1\2', text)
    text = re.sub(r'(\w)-\s{2,}([a-zàèéìòù])', r'\1\2', text)
    return text

def normalize_whitespace(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def clean_text(text: str) -> str:
    text = fix_encoding(text)
    text = remove_headers(text)
    text = fix_hyphenation(text)
    text = normalize_whitespace(text)
    return text

# =============================================================================
# SPEAKER VALIDATION
# =============================================================================

def is_fake_speaker(name: str, chamber: str = "Camera") -> bool:
    """Check if this is a fake speaker."""
    name_upper = name.upper().strip()
    
    for pattern in FAKE_SPEAKER_REGEX:
        if pattern.match(name_upper):
            return True
    
    if len(name) > 50:
        return True
    
    if len(name) < 3:
        return True
    
    if re.search(r'\d', name) and 'M5S' not in name_upper:
        return True
    
    words = name.split()
    word_count = len(words)
    
    if word_count > 5:
        return True
    
    # Camera: require 2+ words (except known speakers)
    if chamber == "Camera":
        if word_count == 1 and name_upper not in KNOWN_SINGLE_SPEAKERS:
            return True
    
    # Senato: allow single surnames but validate
    if chamber == "Senato":
        if word_count == 1 and name_upper not in KNOWN_SINGLE_SPEAKERS:
            if len(name) < 4 or len(name) > 15:
                return True
            if not re.match(r'^[A-ZÀÈÉÌÒÙa-zàèéìòù]+$', name):
                return True
    
    # Suspicious substrings
    suspicious = ['VOTAZIONE', 'TRASMISSIONE', 'COMUNICAZION', 'ANNUNZIO',
                  'FACOLTÀ', 'PARLARE', 'PROSEGU', 'PASSIAM', 'PROCEDIAM',
                  'DICHIARO', 'INDÌCO', 'METTO AI', 'AVVERTO', 'COMUNICO',
                  'RICORDO', 'RINGRAZIO', 'ALLEGATO', 'DOCUMENTO', 'ATTI E',
                  'RISULTATO', 'SEGUITO', 'ESAME', 'DISCUSSIONE', 'QUESTO',
                  'QUELLO', 'ABBIAMO', 'AVETE', 'ESISTONO', 'CONTENUTO',
                  'PROVVEDIMENTO', 'RISOLUZIONI', 'STESSO VALE', 'SCORRERE',
                  'CIFRE', 'FATTI', 'CONCETTO', 'MONOPATTINI', 'DIMISSIONI']
    for sus in suspicious:
        if sus in name_upper:
            return True
    
    # Bad words in middle of name
    bad_words = {'DI', 'DEL', 'DELLA', 'DELLO', 'DEGLI', 'DELLE', 'DA', 'DAL',
                 'PER', 'CON', 'SU', 'SUL', 'SULLA', 'TRA', 'FRA', 'IN', 'NEL',
                 'È', 'SONO', 'HA', 'HANNO', 'ESSERE', 'FARE', 'NON', 'CHE',
                 'IL', 'LA', 'LE', 'LO', 'GLI', 'UN', 'UNA', 'UNO',
                 'ALLA', 'ALLE', 'AI', 'AGLI', 'AL'}
    if word_count > 2:
        middle_words = set(words[1:-1])
        if middle_words & bad_words - {'DE', 'DI', 'DEL', 'DELLA', 'LA', 'LO'}:
            return True
    
    return False

def clean_speaker(name: str) -> str:
    name = re.sub(r'\s+', ' ', name.strip())
    name = re.sub(r'[\.,]+$', '', name)
    return name.upper()

def clean_party(party: Optional[str]) -> str:
    if not party:
        return ''
    party = re.sub(r'\s+', '-', party.strip())
    return party.upper()

# =============================================================================
# SEGMENTATION
# =============================================================================

def segment_speeches(text: str, pattern: re.Pattern, chamber: str) -> List[Dict]:
    speeches = []
    matches = list(pattern.finditer(text))
    
    if not matches:
        return speeches
    
    for i, match in enumerate(matches):
        speaker_raw = match.group(1)
        party_raw = match.group(2) if match.lastindex >= 2 else None
        
        speaker = clean_speaker(speaker_raw)
        
        if is_fake_speaker(speaker, chamber):
            continue
        
        party = clean_party(party_raw)
        
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        speech_text = text[start:end].strip()
        
        speech_text = re.sub(r'Senato della Repubblica.*?LEGISLATURA', '', speech_text, flags=re.IGNORECASE | re.DOTALL)
        speech_text = re.sub(r'Camera dei Deputati.*?LEGISLATURA', '', speech_text, flags=re.IGNORECASE | re.DOTALL)
        speech_text = re.sub(r'\d+[ªa°]?\s*Seduta.*?(?:STENOGRAFICO|ALLEGATO|INDICE)', '', speech_text, flags=re.IGNORECASE)
        speech_text = re.sub(r'\s+', ' ', speech_text).strip()
        
        if len(speech_text) < 20:
            continue
        
        is_procedural = len(speech_text) < 100 and any(
            phrase in speech_text.lower() 
            for phrase in ['ne ha facoltà', 'è approvato', 'passiamo ai voti', 'la seduta è']
        )
        
        speeches.append({
            'speaker': speaker,
            'party': party,
            'text': speech_text,
            'n_chars': len(speech_text),
            'is_procedural': is_procedural,
        })
    
    return speeches

# =============================================================================
# FILE PROCESSING
# =============================================================================

def process_file(filepath: Path, chamber: str, metadata_lookup: Dict) -> List[Dict]:
    try:
        text = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return []
    
    # Get metadata from lookup
    filename = filepath.name
    
    # For Camera, we need to include legislature in the key
    if chamber == "Camera":
        # Extract leg from path: .../leg18_txt/sed0001.txt or .../leg19_txt/sed0001.txt
        if 'leg18' in str(filepath):
            key = f"leg18_{filename}"
        elif 'leg19' in str(filepath):
            key = f"leg19_{filename}"
        else:
            key = filename
    else:
        key = filename
    
    meta = metadata_lookup.get(key, {})
    
    date = meta.get('date')
    year = meta.get('year')
    legislature = meta.get('legislature')
    seduta_number = meta.get('seduta_number')
    
    # Skip if year is invalid
    if year and (year < 2018 or year > 2025):
        print(f"  SKIPPING {filename}: year={year} out of range")
        return []
    
    text_cleaned = clean_text(text)
    
    pattern = CAMERA_SPEAKER_PATTERN if chamber == "Camera" else SENATO_SPEAKER_PATTERN
    speeches = segment_speeches(text_cleaned, pattern, chamber)
    
    session_id = filepath.stem
    for i, speech in enumerate(speeches):
        speech['speech_id'] = f"{session_id}_sp{i:04d}"
        speech['session_id'] = session_id
        speech['chamber'] = chamber
        speech['legislature'] = legislature
        speech['date'] = date
        speech['year'] = year
        speech['seduta_number'] = seduta_number
        speech['source_file'] = filename
    
    return speeches

# =============================================================================
# MAIN
# =============================================================================

def process_corpus():
    print("\nLoading metadata files...")
    camera_lookup, senato_lookup = load_metadata()
    
    all_speeches = []
    stats = {'camera_files': 0, 'senato_files': 0, 'camera_speeches': 0, 'senato_speeches': 0}
    
    print("\n" + "=" * 60)
    print("PROCESSING CAMERA FILES")
    print("=" * 60)
    
    for cam_dir in CAMERA_DIRS:
        if not cam_dir.exists():
            print(f"  WARNING: {cam_dir} not found")
            continue
        files = sorted(cam_dir.glob("*.txt"))
        print(f"\n  {cam_dir.name}: {len(files)} files")
        for f in files:
            speeches = process_file(f, "Camera", camera_lookup)
            all_speeches.extend(speeches)
            stats['camera_files'] += 1
            stats['camera_speeches'] += len(speeches)
    
    print("\n" + "=" * 60)
    print("PROCESSING SENATO FILES")
    print("=" * 60)
    
    for sen_dir in SENATO_DIRS:
        if not sen_dir.exists():
            print(f"  WARNING: {sen_dir} not found")
            continue
        files = sorted(sen_dir.glob("*.txt"))
        print(f"\n  {sen_dir.name}: {len(files)} files")
        for f in files:
            speeches = process_file(f, "Senato", senato_lookup)
            all_speeches.extend(speeches)
            stats['senato_files'] += 1
            stats['senato_speeches'] += len(speeches)
    
    # Write output
    if all_speeches:
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'speech_id', 'session_id', 'chamber', 'legislature', 'date', 'year',
            'seduta_number', 'speaker', 'party', 'text', 'n_chars',
            'is_procedural', 'source_file'
        ]
        
        with OUTPUT_CSV.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_speeches)
        
        # Stats
        missing_date = sum(1 for s in all_speeches if not s['date'])
        missing_party = sum(1 for s in all_speeches if not s['party'])
        presidente = sum(1 for s in all_speeches if s['speaker'] == 'PRESIDENTE')
        
        print("\n" + "=" * 60)
        print("OUTPUT SUMMARY")
        print("=" * 60)
        print(f"\nTotal speeches: {len(all_speeches):,}")
        print(f"  Camera: {stats['camera_speeches']:,}")
        print(f"  Senato: {stats['senato_speeches']:,}")
        print(f"\nMetadata quality:")
        print(f"  Missing date: {missing_date:,} ({missing_date/len(all_speeches)*100:.1f}%)")
        print(f"  Missing party: {missing_party:,} ({missing_party/len(all_speeches)*100:.1f}%)")
        print(f"  PRESIDENTE speeches: {presidente:,} ({presidente/len(all_speeches)*100:.1f}%)")
        print(f"\nOutput: {OUTPUT_CSV}")
        
        # Year distribution
        print(f"\nBy year:")
        years = {}
        for s in all_speeches:
            y = s['year'] if s['year'] else 'unknown'
            years[y] = years.get(y, 0) + 1
        for y in sorted([k for k in years.keys() if k != 'unknown']) + (['unknown'] if 'unknown' in years else []):
            print(f"  {y}: {years[y]:,}")


if __name__ == "__main__":
    print("=" * 60)
    print("SPEAKER SEGMENTATION v6")
    print("=" * 60)
    print("\nKey features:")
    print("  ✓ Uses metadata files for dates (no header parsing)")
    print("  ✓ Strict fake speaker filtering")
    print("  ✓ Camera: requires 2+ word names")
    print("  ✓ Senato: validates single-word surnames")
    
    response = input("\nProceed? [y/N]: ")
    if response.lower() == 'y':
        process_corpus()
