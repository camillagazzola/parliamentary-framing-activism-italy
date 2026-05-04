# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025

**Camilla Gazzola** | POL30870 Advanced Seminar in Politics | University College Dublin, 2025/2026
**Supervisor:** Stephanie Dornschneider-Elkink

---

## Overview

This repository contains the code, annotation data, and documentation for the computational pipeline underlying the thesis *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025*. The pipeline produces a corpus of 1,144 activism-related speeches drawn from approximately 287,000 plenary transcripts across both chambers of the Italian Parliament (2018–2025).

Full methodological details, codebook, and analytical decisions are documented in the thesis and its appendices.

---

## Repository Structure

```
├── data_collection/        # Scraping and segmentation
├── preprocessing/          # NLP processing (spaCy)
├── filtering/              # Keyword dictionary and filter
├── classification/         # Supervised classifier (logistic regression)
├── analysis_pipeline/      # Topic assignment, keyness, STM (R)
├── analysis/               # Figures and descriptive stats
├── data/                   # Corpora and annotated training data
├── docs/                   # Codebook and appendix
├── requirements.txt
└── r_packages.txt
```

---

## Data

| File | Description | Rows |
|------|-------------|------|
| `data/activism_corpus_final.csv` | Cleaned corpus, input to analysis pipeline | 1,144 |
| `data/final_corpus.csv` | Analysis-ready dataset with topic labels | 1,056 |
| `data/training_set_annotations.csv` | Manually annotated training sample | ~1,000 |

---

## Reproducing the Analysis

```bash
# Python
pip install -r requirements.txt

# R
install.packages(readLines("r_packages.txt"))
```

Run order:

```bash
python analysis_pipeline/clean_corpus.py
Rscript analysis_pipeline/01_topic_assignment.R
Rscript analysis_pipeline/02_keyword_window_extraction.R
Rscript analysis_pipeline/03a_stm_searchK.R
Rscript analysis_pipeline/03_stm_confirmatory.R
Rscript analysis_pipeline/04_keyness_analysis.R
```

Steps 1–4 can be run directly from `data/activism_corpus_final.csv` without re-running data collection.

---

## Data Sources

- Camera dei Deputati: https://www.camera.it
- Senato della Repubblica: https://www.senato.it
