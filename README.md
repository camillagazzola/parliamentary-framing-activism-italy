# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025

**Camilla Gazzola** | POL30870 Advanced Seminar in Politics | University College Dublin, 2026 
**Supervisor:** Stephanie Dornschneider-Elkink

---

## Overview

This repository contains all code, annotation data, and documentation for the computational pipeline underlying the thesis *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025*.

The thesis analyses how Italian parliamentary discourse frames political activism across two legislatures (XVIII: 2018–2022; XIX: 2022–2025), combining supervised machine learning classification with Structural Topic Modelling (STM) and distinctive lemma analysis. It produces a corpus of 1,232 activism-related speeches drawn from ~287,000 plenary speeches across both chambers of the Italian Parliament.

**Research question:** How is activism framed in Italian parliamentary discourse between 2018 and 2025?

---

## Repository Structure

```
.
├── data_collection/
│   ├── download_transcripts.py       # Scraper for camera.it and senato.it
│   ├── segmenter.py                  # Speaker segmentation + metadata extraction
│   └── party_register_matcher.py     # Matches MPs to party affiliation by session date
│
├── preprocessing/
│   ├── spacy_pipeline.py             # NLP processing (it_core_news_lg): lemmas, POS, NER
│   └── build_dataset.py              # Assembles structured CSV from processed speeches
│
├── filtering/
│   ├── keyword_dictionary.json       # 6-domain activism keyword list
│   └── dictionary_filter.py         # Applies keyword filter, reduces to ~32,500 speeches
│
├── classification/
│   ├── annotate_sample.py            # Draws stratified annotation sample (~1,000 speeches)
│   ├── training_set_annotations.csv  # Manually labelled training data (Class 0/1)
│   ├── train_classifier.py           # TF-IDF + logistic regression, threshold=0.65
│   ├── classifier_model.pkl          # Serialised trained model
│   └── evaluate_classifier.py        # Cross-validation and performance reporting
│
├── topic_assignment/
│   ├── topic_dictionaries.json       # Keyword lists for all 14 topic categories
│   └── assign_topics.py             # 60-word windowed keyword matching
│
├── frame_analysis/
│   ├── stm_analysis.R                # STM fitting (K=4 per topic, party + year covariates)
│   ├── distinctive_lemmas.R          # Monroe et al. log-odds ratio analysis
│   └── frame_labelling.py           # Maps STM clusters and lemmas to 6 macro-frames
│
├── analysis/
│   ├── figures.py                    # All thesis figures (topic dist., temporal trends, heatmaps)
│   └── descriptive_stats.py          # Corpus-level statistics
│
├── data/
│   ├── final_corpus.csv              # 1,232-speech analysis dataset
│   └── training_set_annotations.csv  # Annotated training sample
│
├── docs/
│   ├── Codebook_Gazzola_Thesis.docx           # Full annotation and frame codebook
│   └── CorpusConstruction_TechnicalDoc.docx   # Technical pipeline documentation
│
├── requirements.txt
├── r_packages.txt
└── README.md
```

---

## Pipeline

The corpus is constructed in six sequential stages:

```
Raw transcripts (~287,000 speeches)
        │
        ▼
[Stage 1] Download & segmentation → structured speech-level dataset
        │
        ▼
[Stage 2] NLP preprocessing (spaCy it_core_news_lg) → lemmas, POS, NER
        │
        ▼
[Stage 3] Dictionary filtering (recall-oriented) → ~32,500 speeches (11.3%)
        │
        ▼
[Stage 4] Supervised classification (LR, threshold=0.65) → 1,232 speeches
        │
        ▼
[Stage 5] Topic assignment (60-word windowed keyword matching) → 1,013 speeches with topic
        │
        ▼
[Stage 6] Frame analysis (STM + distinctive lemma analysis)
```

### Stage 1 — Data Collection

Plenary stenographic transcripts (*resoconti stenografici*) were downloaded from:
- **Camera dei Deputati:** [camera.it](https://www.camera.it)
- **Senato della Repubblica:** [senato.it](https://www.senato.it)

The scraper (`download_transcripts.py`) iterates over all session identifiers for both legislatures and chambers. HTML is used as the primary format; PDF fallback (via `pdftotext`) is applied where HTML is unavailable. Raw transcripts are **not** included in this repository due to size — run `download_transcripts.py` to reproduce the collection.

### Stage 2 — NLP Preprocessing

Speeches were processed with [spaCy](https://spacy.io/) `it_core_news_lg` (large Italian model), extracting lemmas, part-of-speech tags, and named entities. The large model was selected for superior NER accuracy on activist group names and legislative entities.

```bash
python preprocessing/spacy_pipeline.py --input data/raw_speeches.csv --output data/processed_speeches.csv
```

### Stage 3 — Dictionary Filtering

A theory-informed keyword dictionary (`filtering/keyword_dictionary.json`) organised into six semantic domains (protest/dissent, collective action, movements/activism, demonstrations, claim-making, disruption) identifies candidate speeches. Matching is performed on lemmatised text. Retention criterion: at least one keyword present. This stage is deliberately recall-oriented, tolerating false positives to minimise false negatives.

```bash
python filtering/dictionary_filter.py --input data/processed_speeches.csv --output data/filtered_speeches.csv
```

### Stage 4 — Supervised Classification

A logistic regression classifier distinguishes substantive activism-related speeches from incidental keyword matches. Trained on ~1,000 manually annotated speeches following McAdam's (1982) Political Process Model ("outside-in" criterion). A probability threshold of 0.65 prioritises precision over recall.

| Metric | Value |
|--------|-------|
| Algorithm | Logistic Regression (L2, class_weight='balanced') |
| Features | TF-IDF unigrams/bigrams + keyword domain features + speech length |
| Macro F1 (5-fold CV) | 0.71 (Class 1: 0.74 / Class 0: 0.68) |
| Probability threshold | 0.65 |
| Final corpus precision | ~94% |
| Final corpus size | 1,232 speeches |

```bash
python classification/train_classifier.py --input data/filtered_speeches.csv --annotations classification/training_set_annotations.csv
python classification/evaluate_classifier.py
```

### Stage 5 — Topic Assignment

Each speech is assigned an activism topic via keyword matching within 60-word contextual windows centred on the activism keyword. 14 topic categories are defined (see codebook). Of 1,232 speeches, 1,013 (82%) received a clear topic assignment.

```bash
python topic_assignment/assign_topics.py --input data/classified_corpus.csv --output data/topic_corpus.csv
```

### Stage 6 - Frame Analysis

Two complementary methods:

1. **Structural Topic Modelling (STM):** Applied to 60-word contextual windows for each topic with n ≥ 30 speeches. K=4 topics per model, with party affiliation and year as prevalence covariates. Implemented in R using the `stm` package (Roberts et al. 2014).

2. **Distinctive Lemma Analysis:** Monroe et al. (2008) log-odds ratio with Dirichlet prior, identifying terms statistically overrepresented in each party's discourse relative to all other parties on the same topic. Implemented in R using `quanteda`.

```r
Rscript frame_analysis/stm_analysis.R
Rscript frame_analysis/distinctive_lemmas.R
```

---

## Annotation Codebook

The full annotation scheme is documented in `docs/Codebook_Gazzola_Thesis.docx`. It covers:

- **Part A:** Binary speech classification rules (Class 0/1), exclusion criteria, polysemy handling
- **Part B:** 14 activism topic categories with definitions, key actors, and indicative Italian keywords
- **Part C:** 6 macro-frames (Security, Legality, Morality, National Identity, Humanitarianism, Delegitimisation) with definitions, indicative lemmas, frame decision rules, and the legitimacy axis
- **Part D:** Inter-coder reliability notes

---

## Data

| File | Description | Rows |
|------|-------------|------|
| `data/final_corpus.csv` | Analysis-ready dataset, 1,232 speeches with all metadata, topic, and frame labels | 1,232 |
| `data/training_set_annotations.csv` | Manually annotated training sample with Class 0/1 labels | ~1,000 |

### Dataset Schema (`final_corpus.csv`)

| Variable | Type | Description |
|----------|------|-------------|
| `speech_id` | String | Unique speech identifier |
| `chamber` | String | Camera / Senato |
| `date` | Date | Session date (YYYY-MM-DD) |
| `legislature` | Integer | XVIII or XIX |
| `speaker_name` | String | MP name |
| `speaker_party` | String | Party affiliation at time of speech |
| `text_raw` | String | Full speech text |
| `text_lemmatised` | String | SpaCy-lemmatised text |
| `class_label` | Binary | Classifier output (0/1) |
| `class_prob` | Float | Classifier probability (Class 1) |
| `activism_topic` | String | Assigned topic category |
| `frame_stm` | String | Dominant STM frame label |
| `year` | Integer | Year of speech |
| `keyword_matched` | String | Triggering activism keyword |

---

## Reproducing the Analysis

### Requirements

**Python (≥ 3.9):**
```bash
pip install -r requirements.txt
```

**R (≥ 4.2):**
```r
install.packages(readLines("r_packages.txt"))
```

### Full pipeline (in order):

```bash
# 1. Collect transcripts (runtime: several hours)
python data_collection/download_transcripts.py

# 2. Segment and preprocess
python data_collection/segmenter.py
python preprocessing/spacy_pipeline.py
python preprocessing/build_dataset.py

# 3. Filter
python filtering/dictionary_filter.py

# 4. Classify
python classification/train_classifier.py
python classification/evaluate_classifier.py

# 5. Assign topics
python topic_assignment/assign_topics.py

# 6. Frame analysis (R)
Rscript frame_analysis/stm_analysis.R
Rscript frame_analysis/distinctive_lemmas.R

# 7. Generate figures
python analysis/figures.py
```

> **Note:** Steps 1–2 are computationally intensive. Steps 4–7 can be run directly from `data/final_corpus.csv` and `data/training_set_annotations.csv` without re-running the full collection and preprocessing pipeline.

---

## Dependencies

**Python:**

| Package | Purpose |
|---------|---------|
| `spacy` + `it_core_news_lg` | NLP preprocessing |
| `scikit-learn` | Classification |
| `pandas`, `numpy` | Data manipulation |
| `beautifulsoup4`, `requests` | Transcript scraping |
| `matplotlib`, `seaborn` | Figures |

**R:**

| Package | Purpose |
|---------|---------|
| `stm` | Structural Topic Modelling |
| `quanteda` | Corpus analysis, keyness |
| `tidyverse` | Data manipulation |
| `ggplot2` | Figures |

---

## Citation

If you use this code or data, please cite:

> Gazzola, C. (2026). *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025.* BA thesis, University College Dublin. POL30870 Advanced Seminar in Politics.

---

## Data Sources

- Italian Parliament — Camera dei Deputati: https://www.camera.it
- Italian Parliament — Senato della Repubblica: https://www.senato.it

Parliamentary transcripts are public records. All speeches are attributed to identifiable Members of Parliament in their public capacity.

---

## References

- McAdam, D. (1982). *Political Process and the Development of Black Insurgency, 1930–1970.* University of Chicago Press.
- Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words. *Political Analysis*, 16(4), 372–403.
- Roberts, M. E., Stewart, B. M., Tingley, D., et al. (2014). Structural topic models for open-ended survey responses. *American Journal of Political Science*, 58(4), 1064–1082.
- Grimmer, J., & Stewart, B. M. (2013). Text as data. *Political Analysis*, 21(3), 267–297.
- Caiani, M., & Della Porta, D. (2010). *Cross-national Diffusion: The Case of Extreme Right Movements in Action in Five European Countries.* Working paper.

---

*Supervisor: Stephanie Dornschneider-Elkink | Module: POL30870 | UCD School of Politics and International Relations*
