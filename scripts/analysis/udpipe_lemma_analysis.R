#!/usr/bin/env Rscript
# ==============================================================================
# UDPIPE LEMMA-BASED ANALYSIS BY PARTY × TOPIC (+ YEAR OUTPUTS)
# ==============================================================================

library(tidyverse)
library(udpipe)
library(stringr)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

INPUT_CSV <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/keyword_window_analysis/corpus_with_window_analysis.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/udpipe_lemma_analysis/"
MODEL_DIR <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/udpipe_framing/"

dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

MIN_DOCS <- 5

# ==============================================================================
# LOAD DATA
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("UDPIPE LEMMA-BASED ANALYSIS\n")
cat(strrep("=", 70), "\n\n")

df <- read_csv(INPUT_CSV, show_col_types = FALSE)
cat("Total speeches:", nrow(df), "\n")

if (!"party_clean" %in% names(df)) {
  df <- df %>%
    mutate(
      party_clean = case_when(
        is.na(party) ~ "UNKNOWN",
        str_detect(party, "^PD") ~ "PD",
        str_detect(party, "^FDI") ~ "FDI",
        str_detect(party, "^LEGA") ~ "LEGA",
        str_detect(party, "^M5S") ~ "M5S",
        str_detect(party, "^FI") ~ "FI",
        str_detect(party, "MISTO-AVS|^AVS") ~ "AVS",
        str_detect(party, "^IV") ~ "IV",
        str_detect(party, "^LEU") ~ "LEU",
        str_detect(party, "^AZ|^AZIONE") ~ "AZIONE",
        str_detect(party, "EUROPA") ~ "+EUROPA",
        str_detect(party, "^MISTO") ~ "MISTO",
        TRUE ~ "OTHER"
      )
    )
}

df <- df %>%
  filter(!is.na(keyword_window), keyword_window != "", nchar(keyword_window) > 20) %>%
  filter(topic != "other_manual_review", topic != "feminist") %>%
  filter(!is.na(party_clean), party_clean != "UNKNOWN", party_clean != "OTHER", party_clean != "MISTO") %>%
  mutate(year = as.integer(year))

cat("After filtering:", nrow(df), "speeches\n")
cat("Topics:", n_distinct(df$topic), "\n")
cat("Years:", paste(sort(unique(na.omit(df$year))), collapse = ", "), "\n")
cat("Parties:", paste(sort(unique(df$party_clean)), collapse = ", "), "\n\n")

# ==============================================================================
# LOAD UDPIPE MODEL
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("LOADING UDPIPE MODEL\n")
cat(strrep("=", 70), "\n\n")

model_path <- file.path(MODEL_DIR, "italian-isdt-ud-2.5-191206.udpipe")

if (!file.exists(model_path)) {
  cat("Downloading Italian model...\n")
  udmodel_info <- udpipe_download_model(language = "italian", model_dir = MODEL_DIR)
  model_path <- udmodel_info$file_model
}

udmodel <- udpipe_load_model(model_path)
cat("Model loaded:", model_path, "\n\n")

# ==============================================================================
# PARSE ALL KEYWORD WINDOWS
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("PARSING KEYWORD WINDOWS\n")
cat(strrep("=", 70), "\n\n")

parsed_rds <- file.path(OUTPUT_DIR, "parsed_all.rds")

if (file.exists(parsed_rds)) {
  cat("Loading cached parsed data...\n")
  parsed_all <- readRDS(parsed_rds)
  cat("Loaded", nrow(parsed_all), "tokens\n")
} else {
  cat("Parsing (this takes a few minutes)...\n")
  
  batch_size <- 100
  n_batches <- ceiling(nrow(df) / batch_size)
  all_parsed <- list()
  
  for (b in 1:n_batches) {
    start_idx <- (b - 1) * batch_size + 1
    end_idx <- min(b * batch_size, nrow(df))
    
    batch_df <- df[start_idx:end_idx, ]
    
    parsed <- udpipe_annotate(
      udmodel,
      x = batch_df$keyword_window,
      doc_id = batch_df$speech_id
    )
    
    parsed_df <- as.data.frame(parsed)
    
    parsed_df <- parsed_df %>%
      left_join(
        batch_df %>% select(speech_id, topic, party_clean, year),
        by = c("doc_id" = "speech_id")
      )
    
    all_parsed[[b]] <- parsed_df
    
    if (b %% 10 == 0 || b == n_batches) {
      cat(sprintf("  Batch %d/%d (%d speeches)\n", b, n_batches, end_idx))
    }
  }
  
  parsed_all <- bind_rows(all_parsed)
  saveRDS(parsed_all, parsed_rds)
  cat("Saved parsed data to:", parsed_rds, "\n")
}

cat("Total tokens:", nrow(parsed_all), "\n\n")

# ==============================================================================
# FILTER TO CONTENT WORDS
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("FILTERING TO CONTENT WORDS\n")
cat(strrep("=", 70), "\n\n")

content_pos <- c("NOUN", "VERB", "ADJ", "ADV")

italian_stop_lemmas <- c(
  "essere", "avere", "fare", "dire", "potere", "dovere", "volere", "andare",
  "venire", "stare", "dare", "vedere", "sapere", "parlare", "pensare", "credere",
  "mettere", "prendere", "trovare", "lasciare", "passare", "portare", "tenere",
  "sentire", "rimanere", "sembrare", "diventare", "tornare", "entrare", "uscire",
  "cosa", "modo", "parte", "tempo", "anno", "giorno", "volta", "caso", "fatto",
  "punto", "momento", "luogo", "paese", "mondo", "vita", "ora", "oggi",
  "molto", "poco", "tanto", "tutto", "altro", "stesso", "proprio", "grande",
  "piccolo", "nuovo", "vecchio", "buono", "bello", "primo", "ultimo",
  "presidente", "ministro", "governo", "parlamento", "camera", "senato",
  "onorevole", "collega", "signore", "signora",
  "italia", "italiano", "europea", "europeo", "nazionale"
)

tokens <- parsed_all %>%
  filter(upos %in% content_pos) %>%
  filter(!is.na(lemma)) %>%
  mutate(
    lemma = tolower(lemma),
    year = as.integer(year)
  ) %>%
  filter(nchar(lemma) > 2) %>%
  filter(!lemma %in% italian_stop_lemmas) %>%
  filter(!str_detect(lemma, "^[0-9]+$"))

cat("Content tokens:", nrow(tokens), "\n")
cat("Unique lemmas:", n_distinct(tokens$lemma), "\n\n")

# ==============================================================================
# COUNT LEMMAS BY PARTY × TOPIC
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("COUNTING LEMMAS BY PARTY × TOPIC\n")
cat(strrep("=", 70), "\n\n")

doc_counts <- df %>%
  count(party_clean, topic, name = "n_docs")

valid_combos <- doc_counts %>%
  filter(n_docs >= MIN_DOCS)

cat("Valid party × topic combinations:", nrow(valid_combos), "\n\n")

lemma_counts <- tokens %>%
  filter(paste(party_clean, topic) %in% paste(valid_combos$party_clean, valid_combos$topic)) %>%
  count(party_clean, topic, lemma, name = "n") %>%
  group_by(party_clean, topic) %>%
  mutate(
    total = sum(n),
    tf = n / total
  ) %>%
  ungroup()

# ==============================================================================
# COUNT LEMMAS BY YEAR × PARTY × TOPIC
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("COUNTING LEMMAS BY YEAR × PARTY × TOPIC\n")
cat(strrep("=", 70), "\n\n")

doc_counts_year <- df %>%
  filter(!is.na(year)) %>%
  count(year, party_clean, topic, name = "n_docs")

valid_combos_year <- doc_counts_year %>%
  filter(n_docs >= MIN_DOCS)

cat("Valid year × party × topic combinations:", nrow(valid_combos_year), "\n\n")

lemma_counts_year <- tokens %>%
  filter(!is.na(year)) %>%
  filter(
    paste(year, party_clean, topic) %in%
      paste(valid_combos_year$year, valid_combos_year$party_clean, valid_combos_year$topic)
  ) %>%
  count(year, party_clean, topic, lemma, name = "n") %>%
  group_by(year, party_clean, topic) %>%
  mutate(
    total = sum(n),
    tf = n / total
  ) %>%
  ungroup()

# ==============================================================================
# FIND DISTINCTIVE LEMMAS PER PARTY WITHIN EACH TOPIC
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("FINDING DISTINCTIVE LEMMAS\n")
cat(strrep("=", 70), "\n\n")

distinctive_lemmas <- list()

for (t in unique(valid_combos$topic)) {
  topic_parties <- valid_combos %>% filter(topic == t) %>% pull(party_clean)
  if (length(topic_parties) < 2) next
  
  topic_lemmas <- lemma_counts %>% filter(topic == t)
  
  for (p in topic_parties) {
    party_lemmas <- topic_lemmas %>% filter(party_clean == p)
    
    other_lemmas <- topic_lemmas %>%
      filter(party_clean != p) %>%
      group_by(lemma) %>%
      summarise(other_tf = mean(tf), .groups = "drop")
    
    distinctive <- party_lemmas %>%
      left_join(other_lemmas, by = "lemma") %>%
      mutate(other_tf = replace_na(other_tf, 0.00001)) %>%
      mutate(distinctiveness = log2((tf + 0.0001) / (other_tf + 0.0001))) %>%
      filter(n >= 3) %>%
      arrange(desc(distinctiveness))
    
    distinctive_lemmas[[paste(t, p, sep = "___")]] <- distinctive
  }
}

all_distinctive <- bind_rows(distinctive_lemmas, .id = "combo") %>%
  separate(combo, into = c("topic", "party"), sep = "___")

# ==============================================================================
# FIND DISTINCTIVE LEMMAS PER YEAR × PARTY WITHIN EACH TOPIC
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("FINDING DISTINCTIVE LEMMAS BY YEAR\n")
cat(strrep("=", 70), "\n\n")

distinctive_lemmas_year <- list()

for (t in unique(valid_combos_year$topic)) {
  for (y in sort(unique(valid_combos_year$year[valid_combos_year$topic == t]))) {
    
    topic_year_parties <- valid_combos_year %>%
      filter(topic == t, year == y) %>%
      pull(party_clean)
    
    if (length(topic_year_parties) < 2) next
    
    topic_year_lemmas <- lemma_counts_year %>%
      filter(topic == t, year == y)
    
    for (p in topic_year_parties) {
      party_lemmas <- topic_year_lemmas %>%
        filter(party_clean == p)
      
      other_lemmas <- topic_year_lemmas %>%
        filter(party_clean != p) %>%
        group_by(lemma) %>%
        summarise(other_tf = mean(tf), .groups = "drop")
      
      distinctive <- party_lemmas %>%
        left_join(other_lemmas, by = "lemma") %>%
        mutate(other_tf = replace_na(other_tf, 0.00001)) %>%
        mutate(distinctiveness = log2((tf + 0.0001) / (other_tf + 0.0001))) %>%
        filter(n >= 3) %>%
        arrange(desc(distinctiveness))
      
      distinctive_lemmas_year[[paste(y, t, p, sep = "___")]] <- distinctive
    }
  }
}

all_distinctive_year <- bind_rows(distinctive_lemmas_year, .id = "combo") %>%
  separate(combo, into = c("year", "topic", "party"), sep = "___") %>%
  mutate(year = as.integer(year))

# ==============================================================================
# RESULTS BY TOPIC
# ==============================================================================

cat(strrep("=", 70), "\n")
cat("DISTINCTIVE LEMMAS BY PARTY × TOPIC\n")
cat(strrep("=", 70), "\n\n")

for (t in unique(all_distinctive$topic)) {
  cat("\n", strrep("-", 60), "\n")
  cat("TOPIC:", toupper(t), "\n")
  cat(strrep("-", 60), "\n")
  
  topic_data <- all_distinctive %>% filter(topic == t)
  
  for (p in unique(topic_data$party)) {
    party_data <- topic_data %>%
      filter(party == p) %>%
      head(12)
    
    if (nrow(party_data) > 0) {
      cat("\n", p, ":\n")
      cat("  ", paste(party_data$lemma, collapse = ", "), "\n")
    }
  }
}

# ==============================================================================
# TOP LEMMAS PER PARTY × TOPIC (wide format)
# ==============================================================================

cat("\n", strrep("=", 70), "\n")
cat("TOP 10 LEMMAS PER PARTY × TOPIC\n")
cat(strrep("=", 70), "\n\n")

top_lemmas_wide <- all_distinctive %>%
  group_by(topic, party) %>%
  slice_head(n = 10) %>%
  summarise(top_lemmas = paste(lemma, collapse = ", "), .groups = "drop") %>%
  pivot_wider(names_from = party, values_from = top_lemmas)

print(top_lemmas_wide, width = 200)

# ==============================================================================
# SAVE OUTPUTS
# ==============================================================================

cat("\n", strrep("=", 70), "\n")
cat("SAVING OUTPUTS\n")
cat(strrep("=", 70), "\n\n")

write_csv(all_distinctive, file.path(OUTPUT_DIR, "distinctive_lemmas_all.csv"))
cat("✓ distinctive_lemmas_all.csv\n")

write_csv(all_distinctive_year, file.path(OUTPUT_DIR, "distinctive_lemmas_all_by_year.csv"))
cat("✓ distinctive_lemmas_all_by_year.csv\n")

write_csv(top_lemmas_wide, file.path(OUTPUT_DIR, "top_lemmas_by_party_topic.csv"))
cat("✓ top_lemmas_by_party_topic.csv\n")

write_csv(lemma_counts, file.path(OUTPUT_DIR, "lemma_counts_all.csv"))
cat("✓ lemma_counts_all.csv\n")

write_csv(lemma_counts_year, file.path(OUTPUT_DIR, "lemma_counts_all_by_year.csv"))
cat("✓ lemma_counts_all_by_year.csv\n")

write_csv(doc_counts, file.path(OUTPUT_DIR, "doc_counts_party_topic.csv"))
cat("✓ doc_counts_party_topic.csv\n")

write_csv(doc_counts_year, file.path(OUTPUT_DIR, "doc_counts_party_topic_year.csv"))
cat("✓ doc_counts_party_topic_year.csv\n")

for (t in unique(top_lemmas_wide$topic)) {
  topic_wide <- all_distinctive %>%
    filter(topic == t) %>%
    group_by(party) %>%
    slice_head(n = 15) %>%
    summarise(
      lemmas = paste(lemma, collapse = ", "),
      n_total = sum(n),
      .groups = "drop"
    )
  
  write_csv(topic_wide, file.path(OUTPUT_DIR, paste0("topic_", t, ".csv")))
}
cat("✓ topic_[name].csv files\n")

cat("\nAll files saved to:", OUTPUT_DIR, "\n")

cat("\n", strrep("=", 70), "\n")
cat("DONE!\n")
cat(strrep("=", 70), "\n")