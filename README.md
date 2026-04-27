# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025

**Camilla Gazzola** | POL30870 Advanced Seminar in Politics | University College Dublin, 2025/2026  
**Supervisor:** Stephanie Dornschneider-Elkink

---

## Overview

This repository contains all code, annotation data, and documentation for the computational pipeline underlying the thesis *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025*.

The thesis analyses how Italian parliamentary discourse frames political activism across two legislatures (XVIII: 2018–2022; XIX: 2022–2025), combining supervised machine learning classification with keyness analysis and Structural Topic Modelling (STM). It produces a corpus of 1,144 activism-related speeches drawn from ~287,000 plenary speeches across both chambers of the Italian Parliament.

**Research question:** How is activism framed in Italian parliamentary discourse between 2018 and 2025?

---

## Repository Structure

```
.
├── data_collection/
│   ├── download_transcripts.py         # Scraper for camera.it and senato.it
│   ├── segmenter.py                    # Speaker segmentation + metadata extraction
│   └── party_register_matcher.py       # Matches MPs to party affiliation by session date
│
├── preprocessing/
│   ├── spacy_pipeline.py               # NLP processing (it_core_news_lg): lemmas, POS, NER
│   └── build_dataset.py                # Assembles structured CSV from processed speeches
│
├── filtering/
│   ├── keyword_dictionary.json         # 6-domain activism keyword list
│   └── dictionary_filter.py           # Applies keyword filter → ~32,500 speeches
│
├── classification/
│   ├── annotate_sample.py              # Draws stratified annotation sample (~1,000 speeches)
│   ├── training_set_annotations.csv    # Manually labelled training data (Class 0/1)
│   ├── train_classifier.py             # TF-IDF + logistic regression, threshold=0.65
│   ├── classifier_model.pkl            # Serialised trained model
│   └── evaluate_classifier.py          # Cross-validation and performance reporting
│
├── analysis_pipeline/
│   ├── clean_corpus.py                 # Drops segmentation errors, maps party labels
│   ├── 01_topic_assignment.R           # Dictionary classifier with priority hierarchy
│   ├── 02_keyword_window_extraction.R  # Extracts sentence-level windows for frame analysis
│   ├── 03a_stm_searchK.R              # Determines optimal K per topic via held-out likelihood
│   ├── 03_stm_confirmatory.R           # STM (confirmatory, topic-specific K, party covariate)
│   └── 04_keyness_analysis.R           # Keyness analysis via UDPipe + log2 TF ratio
│
├── analysis/
│   ├── figures.R                       # All thesis figures
│   └── descriptive_stats.R             # Corpus-level statistics
│
├── data/
│   ├── activism_corpus_final.csv       # 1,144-speech cleaned corpus (input to pipeline)
│   ├── final_corpus.csv                # Analysis-ready dataset with topic and frame labels
│   └── training_set_annotations.csv    # Annotated training sample
│
├── docs/
│   ├── Codebook_Gazzola_Thesis.docx    # Full annotation and frame codebook
│   └── Appendix_Gazzola_Thesis.docx   # Technical appendix (keywords, STM, keyness outputs)
│
├── requirements.txt
├── r_packages.txt
└── README.md
```

---

## Pipeline

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
[Stage 4] Supervised classification (LR, threshold=0.65) → 1,232 speeches (94% precision)
        │
        ▼
[Stage 4b] Corpus cleaning → 1,144 speeches (88 dropped: segmentation errors)
        │
        ▼
[Stage 5] Activism-category classification (dictionary + priority hierarchy) → 1,056 speeches with category
        │
        ▼
[Stage 5b] Keyword window extraction → sentence-level windows for frame analysis
        │
        ▼
[Stage 6] Frame analysis:
          ├── searchK → topic-specific K (K=2 for 7 topics, K=3 for 3 topics)
          ├── STM (confirmatory, party prevalence covariate)
          └── Keyness analysis (UDPipe lemmatisation + log2 TF ratio)
```

---

## Stage Descriptions

### Stages 1–2 — Data Collection and Preprocessing

Plenary stenographic transcripts (*resoconti stenografici*) were downloaded from the official Italian parliamentary websites and processed with spaCy `it_core_news_lg`, extracting lemmas, POS tags, and named entities. Raw transcripts are not included in this repository — run `download_transcripts.py` to reproduce the collection.

### Stage 3 — Dictionary Filtering

A theory-informed keyword dictionary (`filtering/keyword_dictionary.json`) organised into six semantic domains identifies candidate speeches. This stage is recall-oriented, tolerating false positives to minimise false negatives.

### Stage 4 — Supervised Classification

A logistic regression classifier distinguishes substantive activism-related speeches from incidental keyword matches, trained on ~1,000 manually annotated speeches following McAdam's (1982) Political Process Model ("outside-in" criterion).

| Metric | Value |
|--------|-------|
| Algorithm | Logistic Regression (L2, class_weight='balanced') |
| Features | TF-IDF unigrams/bigrams + keyword domain features + speech length |
| Macro F1 (5-fold CV) | 0.71 (Class 1: F1=0.74 / Class 0: F1=0.68) |
| Probability threshold | 0.65 (precision-oriented) |
| Corpus precision | ~94% |
| Corpus size | 1,232 speeches |

### Stage 4b — Corpus Cleaning

88 rows with missing or garbled party labels (segmentation errors) are dropped and all non-standard party labels are mapped to canonical labels. Output: 1,144 speeches.

```bash
python analysis_pipeline/clean_corpus.py
```

### Stage 5 — Activism-Category Classification

Each speech is assigned to one of 14 activism categories using a dictionary-based classifier with a priority hierarchy applied to **full speech texts** (`01_topic_assignment.R`). This approach classifies known protest referents rather than discovering unknown topics (Laver, Benoit and Garry 2003; Grimmer and Stewart 2013).

**Priority logic:**
- Priority 1: named movements and organisations (most specific — e.g. Ultima Generazione, CasaPound, Hamas)
- Priority 2: clear movement categories (e.g. migrants, far right, prisoners' rights)
- Priority 3: broader categories (e.g. labour, students, police/security)
- When multiple topics match: lowest priority number wins; ties resolved by keyword match count

| Category | N | Category | N |
|----------|---|----------|---|
| Incarcerated Persons | 193 | Students | 55 |
| Migrants | 144 | No Vax | 53 |
| Climate Activists | 125 | Antisemitism | 52 |
| Police / Security | 113 | Far Left | 28 |
| Far Right | 87 | Antifascist | 26 |
| Labour | 83 | LGBTQ | 22 |
| Pro-Palestine | 58 | No TAV | 17 |

```r
Rscript analysis_pipeline/01_topic_assignment.R
```

### Stage 5b — Keyword Window Extraction

Sentence-level windows (1 sentence either side of an activism keyword) are extracted from each speech. These windows — not full speech texts — serve as input for STM and keyness analysis, ensuring frame identification reflects the immediate discursive context of activism references (Caiani and della Porta 2010).

```r
Rscript analysis_pipeline/02_keyword_window_extraction.R
```

### Stage 6 — Frame Analysis

#### searchK: K selection

The optimal K for each STM model was determined empirically using `searchK()` across K=2:7, selecting K based on held-out likelihood. Topics with n < 30 are excluded from STM.

| K=2 | K=3 |
|-----|-----|
| Incarcerated Persons, Climate Activists, Police/Security, Labour, Far Right, Students, No Vax | Migrants, Pro-Palestine, Antisemitism |

```r
Rscript analysis_pipeline/03a_stm_searchK.R
```

#### STM (confirmatory)

STM is run with topic-specific K and party affiliation as a prevalence covariate. Used in a **confirmatory role** to verify that meaningful latent thematic clusters exist before proceeding to keyness analysis. Results reported in the appendix.

```r
Rscript analysis_pipeline/03_stm_confirmatory.R
```

#### Keyness Analysis (primary)

Vocabulary overrepresented in each party's discourse relative to all other parties on the same topic, computed as a log2 relative term frequency ratio. Lemmatisation via UDPipe `italian-isdt-ud-2.5-191206`. Min frequency: n ≥ 3. Min speeches per party-topic cell: n ≥ 5.

```
distinctiveness = log2((tf_party + 0.0001) / (mean_tf_others + 0.0001))
```

Top lemmas per party-topic cell are qualitatively mapped onto six theoretical frames: Security, Legality, Morality, National Identity, Humanitarianism, Delegitimisation (Beetham 1991).

```r
Rscript analysis_pipeline/04_keyness_analysis.R
```

---

## Annotation Codebook

`docs/Codebook_Gazzola_Thesis.docx` covers:

- **Part A:** Binary speech classification rules (Class 0/1), exclusion criteria, polysemy handling
- **Part B:** 14 activism categories with priority levels, definitions, and keyword lists
- **Part C:** 6 macro-frames with definitions, indicative lemmas, decision rules, and legitimacy axis
- **Part D:** Inter-coder reliability notes and known ambiguity sources

---

## Data

| File | Description | Rows |
|------|-------------|------|
| `data/activism_corpus_final.csv` | Cleaned corpus, input to analysis pipeline | 1,144 |
| `data/final_corpus.csv` | Analysis-ready dataset with topic and frame labels | 1,056 |
| `data/training_set_annotations.csv` | Manually annotated training sample | ~1,000 |

### Dataset Schema (`final_corpus.csv`)

| Variable | Type | Description |
|----------|------|-------------|
| `speech_id` | String | Unique speech identifier |
| `chamber` | String | Camera / Senato |
| `date` | Date | Session date (YYYY-MM-DD) |
| `legislature` | Integer | XVIII or XIX |
| `speaker_name` | String | MP name |
| `party_clean` | String | Canonical party label at time of speech |
| `text` | String | Full speech text |
| `class_label` | Binary | Classifier output (0/1) |
| `class_prob` | Float | Classifier probability (Class 1) |
| `topic` | String | Assigned activism category |
| `keyword_window` | String | Extracted sentence-level window |
| `year` | Integer | Year of speech |
| `matched_keywords` | String | Keywords triggering category assignment |

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

### Run order

```bash
# 0. Clean corpus (Python)
python analysis_pipeline/clean_corpus.py

# 1. Assign activism categories (R, ~5 min)
Rscript analysis_pipeline/01_topic_assignment.R

# 2. Extract keyword windows (R, ~5 min)
Rscript analysis_pipeline/02_keyword_window_extraction.R

# 3a. Determine optimal K per topic (R, ~1 hour)
Rscript analysis_pipeline/03a_stm_searchK.R

# 3b. Run STM confirmatory analysis (R, ~20 min)
Rscript analysis_pipeline/03_stm_confirmatory.R

# 4. Keyness analysis (R, ~20 min first run, cached after)
Rscript analysis_pipeline/04_keyness_analysis.R
```

> **Note:** Steps 0–4 can be run directly from `data/activism_corpus_final.csv` without re-running the full collection and preprocessing pipeline. UDPipe parsing in Step 4 is cached to `parsed_windows.rds` — delete this file to force re-parsing. STM (Step 3b) is not fully deterministic; the deposited `stm_models.rds` reproduces the exact results reported in the thesis.

---

## Dependencies

**Python:**

| Package | Purpose |
|---------|---------|
| `spacy` + `it_core_news_lg` | NLP preprocessing |
| `scikit-learn` | Classification |
| `pandas`, `numpy` | Data manipulation |
| `beautifulsoup4`, `requests` | Transcript scraping |

**R:**

| Package | Purpose |
|---------|---------|
| `stm` | Structural Topic Modelling + searchK |
| `udpipe` | Italian lemmatisation |
| `quanteda` | Corpus tokenisation |
| `tidyverse` | Data manipulation |
| `stringr` | Regex-based keyword classification |

---

## Citation

If you use this code or data, please cite:

> Gazzola, C. (2025). *(De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018–2025.* BA thesis, University College Dublin. POL30870 Advanced Seminar in Politics.

---

## Data Sources

- Italian Parliament — Camera dei Deputati: https://www.camera.it
- Italian Parliament — Senato della Repubblica: https://www.senato.it

Parliamentary transcripts are public records. All speeches are attributed to identifiable Members of Parliament in their public capacity.

---

## References

- Beetham, D. (1991). *The Legitimation of Power.* Macmillan.
- Caiani, M., & Della Porta, D. (2010). Cross-national diffusion: The case of extreme right movements in action in five European countries. *Mobilization*, 15(4), 475–488.
- Grimmer, J., & Stewart, B. M. (2013). Text as data. *Political Analysis*, 21(3), 267–297.
- Laver, M., Benoit, K., & Garry, J. (2003). Extracting policy positions from political texts using words as data. *American Political Science Review*, 97(2), 311–331.
- McAdam, D. (1982). *Political Process and the Development of Black Insurgency, 1930–1970.* University of Chicago Press.
- Roberts, M. E., Stewart, B. M., Tingley, D., et al. (2014). Structural topic models for open-ended survey responses. *American Journal of Political Science*, 58(4), 1064–1082.
- Watanabe, K., & Zhou, Y. (2020). Theory-driven, empirical text analysis. *Social Science Computer Review*, 38(3), 317–335.

---

*Supervisor: Stephanie Dornschneider-Elkink | Module: POL30870 | UCD School of Politics and International Relations*
