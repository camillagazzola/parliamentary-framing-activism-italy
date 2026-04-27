#!/usr/bin/env python3
"""
Sample 100 likely-positive speeches for annotation.
"""

import re
from pathlib import Path

import pandas as pd


RAW_CORPUS = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/speeches_raw_v3_enriched.csv")

EXISTING_ANNOTATIONS = [
    Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/ML_data/annotation/annotation_binary_v3.xlsx"),
    Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/ML_data/annotation/targeted_positives_sample.xlsx"),
]

OUTPUT_FILE = Path("/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/ML_data/annotation/targeted_positives_round2.xlsx")

STRONG_PATTERNS = [
    r"\b(manifestanti|corteo|cortei)\b.{0,50}\b(polizia|scontri|cariche|lacrimogeni)",
    r"\b(protesta|proteste)\b.{0,30}\b(piazza|strada|davanti)",
    r"\bsciopero\b.{0,30}\b(generale|nazionale|lavoratori)",
    r"\bblocco\b.{0,20}\b(stradale|strade|autostrada)",
    r"\boccupazione\b.{0,30}\b(edifici|scuole|università|fabbrica)",
    r"\bpresidio\b.{0,30}\b(permanente|davanti|contro)",
    r"\bsit-in\b",
    r"\bultima generazione\b",
    r"\bextinction rebellion\b",
    r"\bfridays for future\b",
    r"\bno tav\b",
    r"\bno tap\b",
    r"\bcasapound\b",
    r"\bforza nuova\b",
    r"\bcentri sociali\b",
    r"\bdecreto sicurezza\b.{0,50}\b(protesta|manifestazione|attivisti|repressione)",
    r"\bdecreto rave\b",
    r"\banti-?rave\b",
    r"\beco-?vandali\b",
    r"\breato di rave\b",
    r"\bimbrattamento\b.{0,30}\b(opere|quadri|monumenti)",
    r"\b(criminalizza|repressione|reprimere)\b.{0,30}\b(protesta|dissenso|manifestanti)",
    r"\bdisobbedienza civile\b",
    r"\battivisti\b.{0,30}\b(arrestati|denunciati|fermati)",
]


def has_strong_pattern(text):
    if pd.isna(text):
        return False

    text = str(text).lower()
    return any(re.search(pattern, text) for pattern in STRONG_PATTERNS)


def get_strong_matches(text):
    if pd.isna(text):
        return []

    text = str(text).lower()
    matches = []

    for pattern in STRONG_PATTERNS:
        match = re.search(pattern, text)
        if match:
            matches.append(match.group(0)[:50])

    return matches


def load_annotated_text_starts(annotation_files):
    annotated = set()

    for file in annotation_files:
        if not file.exists():
            continue

        annotation_df = pd.read_excel(file)

        if "text" not in annotation_df.columns:
            continue

        annotated.update(annotation_df["text"].dropna().str[:100].tolist())

    return annotated


def main():
    df = pd.read_csv(RAW_CORPUS, low_memory=False)
    df = df[df["speaker"].str.upper() != "PRESIDENTE"].copy()

    already_annotated = load_annotated_text_starts(EXISTING_ANNOTATIONS)

    df["has_strong"] = df["text"].apply(has_strong_pattern)
    df["strong_matches"] = df["text"].apply(get_strong_matches)
    df["text_start"] = df["text"].str[:100]

    candidates = df[df["has_strong"]].copy()
    candidates = candidates[~candidates["text_start"].isin(already_annotated)]

    sample_size = min(100, len(candidates))
    sample = candidates.sample(n=sample_size, random_state=123)

    output_df = sample[["chamber", "year", "date", "speaker", "party", "text"]].copy()
    output_df.insert(0, "sample_id", range(1, len(output_df) + 1))
    output_df["pattern_matched"] = sample["strong_matches"].apply(lambda x: "; ".join(x[:2]))
    output_df["is_activism_related"] = ""
    output_df["confidence"] = ""
    output_df["notes"] = ""

    output_df = output_df[
        [
            "sample_id",
            "pattern_matched",
            "chamber",
            "year",
            "date",
            "speaker",
            "party",
            "is_activism_related",
            "confidence",
            "notes",
            "text",
        ]
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_excel(OUTPUT_FILE, index=False)

    print(f"Saved {sample_size} speeches to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
