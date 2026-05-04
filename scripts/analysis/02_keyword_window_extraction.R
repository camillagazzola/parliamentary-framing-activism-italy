#!/usr/bin/env Rscript
# =============================================================================
# 02_keyword_window_extraction.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2025
#
# PURPOSE: Extract sentence-level windows (1 sentence either side) around
#   activism keywords from each speech. These windows are used as input for
#   STM and keyness analysis, ensuring frame identification reflects the
#   immediate discursive context of activism references rather than unrelated
#   sections of longer speeches (Caiani and della Porta 2010).
#
# INPUT:  /Users/camillagazzola/Desktop/thesis_test/output/corpus_with_topics.csv
# OUTPUT: /Users/camillagazzola/Desktop/thesis_test/output/corpus_with_windows.csv
#
# Run from anywhere:
#   Rscript /Users/camillagazzola/Desktop/thesis_test/02_keyword_window_extraction.R
# =============================================================================

library(tidyverse)
library(stringr)

# ── PATHS ─────────────────────────────────────────────────────────────────────

INPUT_CSV  <- "/Users/camillagazzola/Desktop/thesis_test/output/corpus_with_topics.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/thesis_test/output"

WINDOW_SIZE <- 1  # sentences before and after the keyword sentence

# ── ACTIVISM KEYWORDS ─────────────────────────────────────────────────────────

activism_keywords <- c(
  "protesta","proteste","protestare","manifestazione","manifestazioni",
  "corteo","cortei","sciopero","scioperi","mobilitazione","mobilitazioni",
  "attivismo","attivista","attivisti","movimento sociale","movimenti sociali",
  "occupazione","presidio","dissenso","contestazione","rivolta","rivolte",
  "blocco stradale","blocchi stradali","disobbedienza civile",
  "azione collettiva","boicottaggio","sit-in","picchetto"
)

# ── WINDOW EXTRACTION ─────────────────────────────────────────────────────────

extract_window <- function(text, keywords, window_size = 1) {
  if (is.na(text) || nchar(text) < 10) return("")

  sentences <- str_split(text, "(?<=[.!?])\\s+")[[1]]
  if (length(sentences) == 0) return("")

  matched_idx <- c()
  for (i in seq_along(sentences)) {
    sent_lower <- tolower(sentences[i])
    for (kw in keywords) {
      if (str_detect(sent_lower, fixed(tolower(kw)))) {
        matched_idx <- c(matched_idx, i)
        break
      }
    }
  }

  if (length(matched_idx) == 0) return("")

  all_idx <- c()
  for (idx in unique(matched_idx)) {
    start   <- max(1, idx - window_size)
    end     <- min(length(sentences), idx + window_size)
    all_idx <- c(all_idx, start:end)
  }
  all_idx <- sort(unique(all_idx))

  window_text <- paste(sentences[all_idx], collapse = " ")
  if (nchar(window_text) > 3000) window_text <- str_sub(window_text, 1, 3000)
  window_text
}

# ── LOAD & PROCESS ────────────────────────────────────────────────────────────

cat("Loading corpus with topics...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE) %>%
  filter(topic != "unassigned")

cat("Speeches:", nrow(df), "\n\n")
cat("Extracting windows...\n")

df <- df %>%
  rowwise() %>%
  mutate(keyword_window = extract_window(text, activism_keywords, WINDOW_SIZE)) %>%
  ungroup()

has_window <- sum(nchar(df$keyword_window) > 20, na.rm = TRUE)
cat("Speeches with window:", has_window, "/", nrow(df), "\n")
cat("Average window length:", round(mean(nchar(df$keyword_window), na.rm = TRUE)), "chars\n\n")

# ── SAVE ──────────────────────────────────────────────────────────────────────

write_csv(df, file.path(OUTPUT_DIR, "corpus_with_windows.csv"))
cat("✓ corpus_with_windows.csv\n")
cat("\nDone.\n")
