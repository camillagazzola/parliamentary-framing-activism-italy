# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025

**Camilla Gazzola** | POL30870 Advanced Seminar in Politics | University College Dublin, 2025/2026

---

## Overview

This repository contains the code, annotation data, and documentation for the computational pipeline underlying the thesis *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025*. The pipeline combines web scraping, speaker segmentation, supervised machine learning classification, keyness analysis, and structural topic modelling to analyse how Italian parliamentary discourse frames activism and protest across two legislatures (2018–2025).

Full methodological details, codebook, and analytical decisions are documented in the thesis and its appendices.

---

## Repository Structure

```
├── scripts/                # Analysis pipeline scripts
│   ├── download/           # Web scraping from parliamentary sources
│   ├── build_corpus/       # Corpus construction 
│   ├── preprocessing/      # Segmentation
│   ├── filtering/          # Keyword filtering
│   ├── metadata/           # Metadata extraction and cleaning
│   ├── ML/                 # Supervised classification (logistic regression)
│   └── analysis/           # Analysis (R)
│
├── data/                   # Data files (processed)
│   ├── corpus/             # Parliamentary speeches corpus
│   ├── analysis/           # Analysis-ready datasets
│   └── README.md           
│
├── docs/                   # Documentation and resources
│   ├── codebook.pdf        # Detailed codebook
│   ├── Appendices.pdf      # Thesis appendices
│   ├── dictionaries/       # Filtering dictionary
│   └── README.md         
│
├── results/                # Output figures and analysis results
│   └── *.png               # Visualizations for thesis
│
└── README.md
```

---

---

## Pipeline

| Step | Script | Language | Output |
|------|--------|----------|--------|
| 1 | `download_camera_transcripts.sh` | Bash | Raw Camera PDFs |
| 2 | `download_senato_transcripts.sh` | Bash | Raw Senato PDFs |
| 3 | `build_corpus.py` | Python | Camera TXT + metadata |
| 4 | `build_corpus_senato.py` | Python | Senato TXT |
| 5 | `extract_senato_metadata.py` | Python | Senato metadata CSV |
| 6 | `segment_speakers.py` | Python | `speeches_raw.csv` |
| 7 | `filter_activism.py` | Python | `dictionary_filtered.csv` |
| 8 | `train_classifier.py` | Python | `activism_corpus_classified.csv` |
| 9 | `clean_corpus.py` | Python | `activism_corpus_final.csv` |
| 10 | `01_topic_assignment.R` | R | `corpus_with_topics.csv` |
| 11 | `02_keyword_window_extraction.R` | R | `corpus_with_windows.csv` |
| 12 | `03a_stm_searchK.R` | R | `searchK_results.csv` |
| 13 | `03_stm_confirmatory.R` | R | `stm_models.rds` |
| 14 | `04_keyness_analysis.R` | R | `keyness_all.csv` |
| 15 | `plot_frames_dotplot.R` | R | `frame_dotplot.png` |

---

## Data

| File | Description | Rows |
|------|-------------|------|
| `data/activism_corpus_final.csv` | Cleaned corpus, input to analysis pipeline | 1,144 |
| `data/final_corpus.csv` | Analysis-ready dataset with topic labels | 1,056 |
| `data/training_data_corrected.csv` | Manually annotated training sample | ~1,600 |
| `data/frame_coding.csv` | Qualitative frame coding per party-topic-year cell | 84 |

Raw PDFs are not included due to file size. Run steps 1–5 to reproduce data collection, or start from `data/activism_corpus_final.csv` for analysis only.

---

## Reproducing the Analysis

### Full pipeline

```bash
# Data collection
bash data_collection/download_camera_transcripts.sh
bash data_collection/download_senato_transcripts.sh

# Corpus construction
python preprocessing/build_corpus.py
python preprocessing/build_corpus_senato.py
python preprocessing/extract_senato_metadata.py
python preprocessing/segment_speakers.py

# Classification
python classification/filter_activism.py
python classification/train_classifier.py

# Analysis pipeline
python analysis_pipeline/clean_corpus.py
Rscript analysis_pipeline/01_topic_assignment.R
Rscript analysis_pipeline/02_keyword_window_extraction.R
Rscript analysis_pipeline/03a_stm_searchK.R
Rscript analysis_pipeline/03_stm_confirmatory.R
Rscript analysis_pipeline/04_keyness_analysis.R
Rscript analysis/plot_frames_dotplot.R
```

### Analysis only

If you have `data/activism_corpus_final.csv`, skip directly to:

```bash
Rscript analysis_pipeline/01_topic_assignment.R
Rscript analysis_pipeline/02_keyword_window_extraction.R
Rscript analysis_pipeline/03a_stm_searchK.R
Rscript analysis_pipeline/03_stm_confirmatory.R
Rscript analysis_pipeline/04_keyness_analysis.R
Rscript analysis/plot_frames_dotplot.R
```

---

## Documentation

- **Codebook:** `docs/codebook.docx`
- **Appendices:** `docs/Appendices.docx`

---

## Data Sources

- Camera dei Deputati: https://www.camera.it
- Senato della Repubblica: https://www.senato.it

Parliamentary transcripts are public records attributed to identifiable Members of Parliament in their public capacity.

---

## Citation

> Gazzola, C. (2026). *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025.* BA thesis, University College Dublin. POL30870 Advanced Seminar in Politics.# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025

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
