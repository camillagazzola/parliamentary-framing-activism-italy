#!/usr/bin/env Rscript
# =============================================================================
# 04_keyness_analysis.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis - Camilla Gazzola, UCD 2026
#
# PURPOSE: Identify vocabulary disproportionately associated with each party's
#   discourse relative to all other parties on the same activism topic.
#   Method: log2 relative term frequency ratio.
#   Lemmatisation: UDPipe italian-isdt-ud-2.5-191206.
#   Content words only (NOUN, VERB, ADJ, ADV).
#   Min frequency: n >= 2. Min speeches per party-topic cell: n >= 5.
#
#   Formula:
#     distinctiveness = log2((tf_party + 0.0001) / (mean_tf_others + 0.0001))
#
# INPUT:  data/corpus_with_windows.csv
# OUTPUT: data/keyness_all.csv
#         data/keyness_top15_wide.csv
#         data/keyness_by_year.csv
#         data/keyness_[topic].csv
#
# Note: UDPipe parsing is cached to data/parsed_windows.rds.
#   Delete this file to force re-parsing.
# =============================================================================

library(tidyverse)
library(udpipe)
library(stringr)

BASE        <- here::here()
INPUT_CSV   <- file.path(BASE, "data", "corpus_with_windows.csv")
OUTPUT_DIR  <- file.path(BASE, "data")
MODEL_DIR   <- file.path(BASE, "udpipe")
PARSED_RDS  <- file.path(BASE, "data", "parsed_windows.rds")

dir.create(MODEL_DIR, recursive = TRUE, showWarnings = FALSE)

MIN_DOCS <- 5
MIN_FREQ <- 2

italian_stop_lemmas <- c(
  "essere","avere","fare","dire","potere","dovere","volere","andare",
  "venire","stare","dare","vedere","sapere","parlare","pensare","credere",
  "mettere","prendere","trovare","lasciare","passare","portare","tenere",
  "sentire","rimanere","sembrare","diventare","tornare","entrare","uscire",
  "cosa","modo","parte","tempo","anno","giorno","volta","caso","fatto",
  "punto","momento","luogo","paese","mondo","vita","ora","oggi",
  "molto","poco","tanto","tutto","altro","stesso","proprio","grande",
  "piccolo","nuovo","vecchio","buono","bello","primo","ultimo",
  "presidente","ministro","governo","parlamento","camera","senato",
  "onorevole","collega","signore","signora",
  "italia","italiano","europea","europeo","nazionale"
)

cat("Loading corpus...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE) %>%
  filter(!is.na(keyword_window), nchar(keyword_window) > 20) %>%
  filter(!is.na(party_clean), party_clean != "MISTO",
         !party_clean %in% c("+EUROPA", "AZIONE")) %>%
  mutate(year = as.integer(year))

cat("Speeches:", nrow(df), "\n")
cat("Parties: ", paste(sort(unique(df$party_clean)), collapse = ", "), "\n\n")

cat("Loading UDPipe model...\n")
model_path <- file.path(MODEL_DIR, "italian-isdt-ud-2.5-191206.udpipe")

if (!file.exists(model_path)) {
  cat("  Downloading Italian model...\n")
  info       <- udpipe_download_model(language = "italian", model_dir = MODEL_DIR)
  model_path <- info$file_model
}

udmodel <- udpipe_load_model(model_path)
cat("  Loaded:", model_path, "\n\n")

if (file.exists(PARSED_RDS)) {
  cat("Loading cached parsed tokens...\n")
  parsed_all <- readRDS(PARSED_RDS)
  cat("  Tokens:", nrow(parsed_all), "\n\n")
} else {
  cat("Parsing with UDPipe (this takes ~5-10 minutes)...\n")
  batch_size <- 100
  n_batches  <- ceiling(nrow(df) / batch_size)
  all_parsed <- list()

  for (b in seq_len(n_batches)) {
    start <- (b - 1) * batch_size + 1
    end   <- min(b * batch_size, nrow(df))
    batch <- df[start:end, ]

    parsed <- udpipe_annotate(udmodel,
                              x      = batch$keyword_window,
                              doc_id = batch$speech_id)
    parsed_df <- as.data.frame(parsed) %>%
      left_join(batch %>% select(speech_id, topic, party_clean, year),
                by = c("doc_id" = "speech_id"))
    all_parsed[[b]] <- parsed_df

    if (b %% 10 == 0 || b == n_batches)
      cat("  Batch", b, "/", n_batches, "\n")
  }

  parsed_all <- bind_rows(all_parsed)
  saveRDS(parsed_all, PARSED_RDS)
  cat("  Cached to:", PARSED_RDS, "\n\n")
}

tokens <- parsed_all %>%
  filter(upos %in% c("NOUN","VERB","ADJ","ADV"), !is.na(lemma)) %>%
  mutate(lemma = tolower(lemma), year = as.integer(year)) %>%
  filter(nchar(lemma) > 2,
         !lemma %in% italian_stop_lemmas,
         !str_detect(lemma, "^[0-9]+$"))

cat("Content tokens:", nrow(tokens), "\n")
cat("Unique lemmas: ", n_distinct(tokens$lemma), "\n\n")

doc_counts   <- df %>% count(party_clean, topic, name = "n_docs")
valid_combos <- doc_counts %>% filter(n_docs >= MIN_DOCS)
cat("Valid party x topic cells (n >=", MIN_DOCS, "):", nrow(valid_combos), "\n\n")

lemma_counts <- tokens %>%
  filter(paste(party_clean, topic) %in%
           paste(valid_combos$party_clean, valid_combos$topic)) %>%
  count(party_clean, topic, lemma, name = "n") %>%
  group_by(party_clean, topic) %>%
  mutate(total = sum(n), tf = n / total) %>%
  ungroup()

cat("Computing keyness scores...\n")

keyness_results <- list()
for (t in unique(valid_combos$topic)) {
  parties <- valid_combos %>% filter(topic == t) %>% pull(party_clean)
  if (length(parties) < 2) next
  topic_lemmas <- lemma_counts %>% filter(topic == t)

  for (p in parties) {
    party_l <- topic_lemmas %>% filter(party_clean == p)
    other_l <- topic_lemmas %>%
      filter(party_clean != p) %>%
      group_by(lemma) %>%
      summarise(other_tf = mean(tf), .groups = "drop")

    res <- party_l %>%
      left_join(other_l, by = "lemma") %>%
      mutate(
        other_tf        = replace_na(other_tf, 0.00001),
        distinctiveness = log2((tf + 0.0001) / (other_tf + 0.0001))
      ) %>%
      filter(n >= MIN_FREQ) %>%
      arrange(desc(distinctiveness))

    keyness_results[[paste(t, p, sep = "___")]] <- res
  }
}

keyness_all <- bind_rows(keyness_results, .id = "combo") %>%
  separate(combo, into = c("topic", "party"), sep = "___")

cat("Saving outputs...\n")

write_csv(keyness_all, file.path(OUTPUT_DIR, "keyness_all.csv"))
write_csv(lemma_counts, file.path(OUTPUT_DIR, "lemma_counts_all.csv"))

keyness_all %>%
  group_by(topic, party) %>%
  slice_head(n = 15) %>%
  summarise(top_lemmas = paste(lemma, collapse = ", "), .groups = "drop") %>%
  pivot_wider(names_from = party, values_from = top_lemmas) %>%
  write_csv(file.path(OUTPUT_DIR, "keyness_top15_wide.csv"))

for (t in unique(keyness_all$topic)) {
  keyness_all %>%
    filter(topic == t) %>%
    group_by(party) %>%
    slice_head(n = 15) %>%
    summarise(lemmas = paste(lemma, collapse = ", "),
              n_total = sum(n), .groups = "drop") %>%
    write_csv(file.path(OUTPUT_DIR, paste0("keyness_", t, ".csv")))
}

MIN_DOCS_YR <- 3
MIN_FREQ_YR <- 2

doc_counts_yr <- df %>%
  filter(!is.na(year)) %>%
  count(year, party_clean, topic, name = "n_docs")
valid_yr <- doc_counts_yr %>% filter(n_docs >= MIN_DOCS_YR)

lemma_counts_yr <- tokens %>%
  filter(!is.na(year)) %>%
  filter(paste(year, party_clean, topic) %in%
           paste(valid_yr$year, valid_yr$party_clean, valid_yr$topic)) %>%
  count(year, party_clean, topic, lemma, name = "n") %>%
  group_by(year, party_clean, topic) %>%
  mutate(total = sum(n), tf = n / total) %>%
  ungroup()

yr_results <- list()
for (t in unique(valid_yr$topic)) {
  for (y in sort(unique(valid_yr$year[valid_yr$topic == t]))) {
    yr_parties <- valid_yr %>% filter(topic == t, year == y) %>% pull(party_clean)
    if (length(yr_parties) < 2) next
    yr_lemmas <- lemma_counts_yr %>% filter(topic == t, year == y)

    for (p in yr_parties) {
      party_l <- yr_lemmas %>% filter(party_clean == p)
      other_l <- yr_lemmas %>%
        filter(party_clean != p) %>%
        group_by(lemma) %>%
        summarise(other_tf = mean(tf), .groups = "drop")

      res <- party_l %>%
        left_join(other_l, by = "lemma") %>%
        mutate(other_tf = replace_na(other_tf, 0.00001),
               distinctiveness = log2((tf + 0.0001) / (other_tf + 0.0001))) %>%
        filter(n >= MIN_FREQ_YR) %>%
        arrange(desc(distinctiveness))

      yr_results[[paste(y, t, p, sep = "___")]] <- res
    }
  }
}

if (length(yr_results) > 0) {
  bind_rows(yr_results, .id = "combo") %>%
    separate(combo, into = c("year","topic","party"), sep = "___") %>%
    mutate(year = as.integer(year)) %>%
    write_csv(file.path(OUTPUT_DIR, "keyness_by_year.csv"))
}

cat("Done.\n")
