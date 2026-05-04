#!/usr/bin/env Rscript
# =============================================================================
# 02_keyword_window_extraction.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2026
#
# PURPOSE: Extract sentence-level windows (1 sentence either side) around
#   activism keywords from each speech. These windows are used as input for
#   STM and keyness analysis, ensuring frame identification reflects the
#   immediate discursive context of activism references rather than unrelated
#   sections of longer speeches (Caiani and della Porta 2010).
#
# INPUT:  data/corpus_with_topics.csv
# OUTPUT: data/corpus_with_windows.csv
# =============================================================================

library(tidyverse)
library(stringr)

BASE       <- here::here()
INPUT_CSV  <- file.path(BASE, "data", "corpus_with_topics.csv")
OUTPUT_DIR <- file.path(BASE, "data")

WINDOW_SIZE <- 1

activism_keywords <- c(
  "protesta","proteste","protestare","manifestazione","manifestazioni",
  "corteo","cortei","sciopero","scioperi","mobilitazione","mobilitazioni",
  "attivismo","attivista","attivisti","movimento sociale","movimenti sociali",
  "occupazione","presidio","dissenso","contestazione","rivolta","rivolte",
  "blocco stradale","blocchi stradali","disobbedienza civile",
  "azione collettiva","boicottaggio","sit-in","picchetto"
)

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

cat("Loading corpus...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE) %>%
  filter(topic != "unassigned")
cat("Speeches:", nrow(df), "\n\n")

cat("Extracting windows...\n")
df <- df %>%
  rowwise() %>%
  mutate(keyword_window = extract_window(text, activism_keywords, WINDOW_SIZE)) %>%
  ungroup()

cat("Speeches with window:", sum(nchar(df$keyword_window) > 20, na.rm = TRUE),
    "/", nrow(df), "\n")
cat("Average window length:", round(mean(nchar(df$keyword_window), na.rm = TRUE)), "chars\n\n")

write_csv(df, file.path(OUTPUT_DIR, "corpus_with_windows.csv"))
cat("Done.\n") 
