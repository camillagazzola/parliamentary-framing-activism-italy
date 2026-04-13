#!/usr/bin/env Rscript
# =============================================================================
# KEYWORD WINDOW EXTRACTION + TARGETED SENTIMENT ANALYSIS
# Analyzes only the sentences around matched keywords
# =============================================================================

library(tidyverse)
library(stringr)

# =============================================================================
# CONFIGURATION
# =============================================================================

INPUT_CSV <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/dictionary_topics/corpus_with_dictionary_topics.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/keyword_window_analysis/"

dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

# Window size: sentences before and after keyword sentence
WINDOW_SIZE <- 1

# =============================================================================
# DICTIONARIES (focused on framing)
# =============================================================================

# LEGITIMISING language
legit_terms <- c(
  # Rights framing
  "diritto", "diritti", "libertà", "democratico", "democratica",
  "legittimo", "legittima", "costituzionale",
  # Peaceful framing  
  "pacifico", "pacifica", "pacifici", "pacifiche", "pacificamente",
  "nonviolento", "non violento",
  # Solidarity framing
  "solidarietà", "solidale", "dignità", "giustizia", "uguaglianza",
  # Victim framing (activists as victims)
  "colpiti", "vittime", "attaccati", "aggrediti", "repressi", "repressione",
  # Positive descriptors
  "coraggiosi", "giovani", "cittadini", "persone"
)

# DELEGITIMISING language  
delegit_terms <- c(
  # Criminal framing
  "criminali", "delinquenti", "teppisti", "facinorosi",
  # Violence framing (activists as perpetrators)
  "violenti", "violenza", "aggressori", "devastazione", "vandalismo", "vandali",
  # Threat framing
  "minaccia", "pericolosi", "pericoloso", "pericolo",
  # Extremism framing
  "estremisti", "estremismo", "fanatici", "radicali",
  # Disorder framing
  "caos", "disordine", "disordini", "illegalità", "illegale",
  # Negative labels
  "sedicenti", "cosiddetti", "pseudo", "finti",
  # Terrorism framing
  "terroristi", "terrorismo", "eversivi", "sovversivi"
)

# =============================================================================
# LOAD DATA
# =============================================================================

cat(strrep("=", 70), "\n")
cat("LOADING DATA\n")
cat(strrep("=", 70), "\n")

df <- read_csv(INPUT_CSV, show_col_types = FALSE)
cat("Total speeches:", nrow(df), "\n")

# Party consolidation
df <- df %>%
  mutate(
    party_group = case_when(
      str_detect(party, "^PD") ~ "PD",
      str_detect(party, "^FDI") ~ "FDI",
      str_detect(party, "^LEGA") ~ "LEGA",
      str_detect(party, "^M5S") ~ "M5S",
      str_detect(party, "^FI") ~ "FI",
      str_detect(party, "^AVS|MISTO-AVS") ~ "AVS",
      str_detect(party, "^IV") ~ "IV",
      str_detect(party, "^LEU") ~ "LEU",
      str_detect(party, "^AZ") ~ "AZIONE",
      str_detect(party, "EUROPA") ~ "+EUROPA",
      TRUE ~ "OTHER"
    )
  )

# =============================================================================
# EXTRACT KEYWORD WINDOWS
# =============================================================================

cat("\n", strrep("=", 70), "\n")
cat("EXTRACTING KEYWORD WINDOWS\n")
cat(strrep("=", 70), "\n")

extract_windows <- function(text, keywords_str, window_size = 1) {
  if(is.na(text) || is.na(keywords_str) || keywords_str == "") {
    return("")
  }
  
  # Split keywords
  keywords <- str_trim(str_split(keywords_str, ",")[[1]])
  
  # Split text into sentences
  sentences <- str_split(text, "(?<=[.!?])\\s+")[[1]]
  
  if(length(sentences) == 0) return("")
  
  matched_indices <- c()
  
  # Find sentences containing keywords
  for(i in seq_along(sentences)) {
    sent_lower <- str_to_lower(sentences[i])
    for(kw in keywords) {
      if(str_detect(sent_lower, fixed(str_to_lower(kw)))) {
        matched_indices <- c(matched_indices, i)
        break
      }
    }
  }
  
  if(length(matched_indices) == 0) return("")
  
  # Get unique indices with window
  all_indices <- c()
  for(idx in unique(matched_indices)) {
    start <- max(1, idx - window_size)
    end <- min(length(sentences), idx + window_size)
    all_indices <- c(all_indices, start:end)
  }
  all_indices <- sort(unique(all_indices))
  
  # Extract and join
  window_text <- paste(sentences[all_indices], collapse = " ")
  
  # Limit length
  if(nchar(window_text) > 2000) {
    window_text <- str_sub(window_text, 1, 2000)
  }
  
  return(window_text)
}

# Apply to all speeches
df <- df %>%
  rowwise() %>%
  mutate(
    keyword_window = extract_windows(text, matched_keywords, WINDOW_SIZE)
  ) %>%
  ungroup()

cat("Windows extracted.\n")
cat("Average window length:", round(mean(nchar(df$keyword_window), na.rm = TRUE)), "chars\n")

# =============================================================================
# SCORE WINDOWS
# =============================================================================

cat("\n", strrep("=", 70), "\n")
cat("SCORING KEYWORD WINDOWS\n")
cat(strrep("=", 70), "\n")

count_terms <- function(text, terms) {
  if(is.na(text) || text == "") return(0)
  text_lower <- str_to_lower(text)
  sum(sapply(terms, function(term) {
    str_count(text_lower, regex(paste0("\\b", term, "\\b"), ignore_case = TRUE))
  }))
}

df <- df %>%
  rowwise() %>%
  mutate(
    window_legit = count_terms(keyword_window, legit_terms),
    window_delegit = count_terms(keyword_window, delegit_terms),
    window_score = window_legit - window_delegit,
    window_framing = case_when(
      window_legit > window_delegit ~ "legitimising",
      window_delegit > window_legit ~ "delegitimising",
      window_legit == 0 & window_delegit == 0 ~ "neutral",
      TRUE ~ "mixed"
    )
  ) %>%
  ungroup()

cat("Scoring complete.\n")

# =============================================================================
# RESULTS
# =============================================================================

cat("\n", strrep("=", 70), "\n")
cat("FRAMING DISTRIBUTION (from keyword windows)\n")
cat(strrep("=", 70), "\n")

print(table(df$window_framing))

cat("\n", strrep("=", 70), "\n")
cat("BY TOPIC\n")
cat(strrep("=", 70), "\n")

topic_results <- df %>%
  filter(topic != "other_manual_review") %>%
  group_by(topic) %>%
  summarise(
    n = n(),
    avg_score = mean(window_score, na.rm = TRUE),
    pct_legit = mean(window_framing == "legitimising", na.rm = TRUE) * 100,
    pct_delegit = mean(window_framing == "delegitimising", na.rm = TRUE) * 100,
    pct_neutral = mean(window_framing == "neutral", na.rm = TRUE) * 100,
    .groups = "drop"
  ) %>%
  arrange(avg_score)

print(topic_results, n = 20)

cat("\n", strrep("=", 70), "\n")
cat("BY PARTY\n")
cat(strrep("=", 70), "\n")

party_results <- df %>%
  filter(party_group != "OTHER") %>%
  group_by(party_group) %>%
  summarise(
    n = n(),
    avg_score = mean(window_score, na.rm = TRUE),
    pct_legit = mean(window_framing == "legitimising", na.rm = TRUE) * 100,
    pct_delegit = mean(window_framing == "delegitimising", na.rm = TRUE) * 100,
    .groups = "drop"
  ) %>%
  arrange(avg_score)

print(party_results)

cat("\n", strrep("=", 70), "\n")
cat("PARTY × TOPIC\n")
cat(strrep("=", 70), "\n")

party_topic <- df %>%
  filter(topic != "other_manual_review", party_group != "OTHER") %>%
  group_by(party_group, topic) %>%
  summarise(
    n = n(),
    avg_score = mean(window_score, na.rm = TRUE),
    pct_legit = mean(window_framing == "legitimising", na.rm = TRUE) * 100,
    pct_delegit = mean(window_framing == "delegitimising", na.rm = TRUE) * 100,
    .groups = "drop"
  ) %>%
  filter(n >= 3)

cat("\nMost DELEGITIMISING:\n")
party_topic %>% arrange(avg_score) %>% head(15) %>% print()

cat("\nMost LEGITIMISING:\n")
party_topic %>% arrange(desc(avg_score)) %>% head(15) %>% print()

# =============================================================================
# LEFT vs RIGHT
# =============================================================================

cat("\n", strrep("=", 70), "\n")
cat("LEFT vs RIGHT COMPARISON\n")
cat(strrep("=", 70), "\n")

left_parties <- c("PD", "AVS", "M5S", "LEU")
right_parties <- c("FDI", "LEGA", "FI")

key_topics <- c("climate_activists", "migrants", "far_right", "far_left", 
                "pro_palestine", "prisoners_rights", "police_security", "labor")

comparison <- data.frame()

for(t in key_topics) {
  topic_df <- df %>% filter(topic == t)
  
  left_df <- topic_df %>% filter(party_group %in% left_parties)
  right_df <- topic_df %>% filter(party_group %in% right_parties)
  
  if(nrow(left_df) >= 3 && nrow(right_df) >= 3) {
    comparison <- rbind(comparison, data.frame(
      topic = t,
      left_n = nrow(left_df),
      left_score = round(mean(left_df$window_score, na.rm = TRUE), 2),
      left_pct_legit = round(mean(left_df$window_framing == "legitimising") * 100, 1),
      right_n = nrow(right_df),
      right_score = round(mean(right_df$window_score, na.rm = TRUE), 2),
      right_pct_legit = round(mean(right_df$window_framing == "legitimising") * 100, 1),
      diff = round(mean(left_df$window_score) - mean(right_df$window_score), 2)
    ))
  }
}

print(comparison %>% arrange(diff))

# =============================================================================
# SAVE
# =============================================================================

cat("\n", strrep("=", 70), "\n")
cat("SAVING\n")
cat(strrep("=", 70), "\n")

write_csv(df, file.path(OUTPUT_DIR, "corpus_with_window_analysis.csv"))
write_csv(topic_results, file.path(OUTPUT_DIR, "window_results_by_topic.csv"))
write_csv(party_results, file.path(OUTPUT_DIR, "window_results_by_party.csv"))
write_csv(party_topic, file.path(OUTPUT_DIR, "window_results_by_party_topic.csv"))
write_csv(comparison, file.path(OUTPUT_DIR, "window_left_vs_right.csv"))

# Datawrapper heatmap
pivot <- party_topic %>%
  select(party_group, topic, avg_score) %>%
  pivot_wider(names_from = topic, values_from = avg_score)
write_csv(pivot, file.path(OUTPUT_DIR, "datawrapper_window_heatmap.csv"))

cat("All files saved to:", OUTPUT_DIR, "\n")

cat("\n", strrep("=", 70), "\n")
cat("DONE!\n")
cat(strrep("=", 70), "\n")
