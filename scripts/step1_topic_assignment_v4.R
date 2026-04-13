################################################################################
# STEP 1 v4: TOPIC ASSIGNMENT WITH TF-IDF + CO-OCCURRENCE
# Italian Parliamentary Activism Corpus (2018-2025)
#
# APPROACH:
# 1. TF-IDF weighting - rare distinctive terms score higher
# 2. Co-occurrence rules - require context words to disambiguate
# 3. Negative keywords - exclude if certain words present
################################################################################

library(tidyverse)
library(tidytext)
library(readr)

# ==============================================================================
# PATHS
# ==============================================================================

CORPUS_PATH <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/activism_corpus_v11.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/topic_analysis_v4/output"

dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)

# ==============================================================================
# LOAD CORPUS
# ==============================================================================

cat("Loading corpus...\n")
corpus_df <- read_csv(CORPUS_PATH, show_col_types = FALSE)
cat("Loaded", nrow(corpus_df), "speeches\n\n")

# ==============================================================================
# BUILD TF-IDF WEIGHTS
# ==============================================================================

cat("Calculating TF-IDF weights...\n")

# Tokenize corpus
corpus_tokens <- corpus_df %>%
  select(speech_id, text) %>%
  unnest_tokens(word, text)

# Calculate TF-IDF
word_tfidf <- corpus_tokens %>%
  count(speech_id, word) %>%
  bind_tf_idf(word, speech_id, n)

# Get average IDF per word (higher = more distinctive)
word_idf <- word_tfidf %>%
  group_by(word) %>%
  summarise(idf = first(idf), .groups = "drop")

# Create lookup
word_idf_lookup <- setNames(word_idf$idf, word_idf$word)

cat("Vocabulary size:", length(word_idf_lookup), "unique words\n")
cat("Sample IDFs:\n")
sample_words <- c("manifestazione", "protesta", "cgil", "casapound", "gaza", "tav")
for (w in sample_words) {
  if (w %in% names(word_idf_lookup)) {
    cat("  ", w, ":", round(word_idf_lookup[w], 2), "\n")
  }
}
cat("\n")

# ==============================================================================
# TOPIC DEFINITIONS WITH CO-OCCURRENCE
# ==============================================================================

# Structure:
# - primary: main keywords (required - at least one must match)
# - context: context keywords (boost score if present)
# - negative: if these present, reduce score (disambiguation)

topic_definitions <- list(
  
  # 1. FAR-RIGHT - discussing fascist/neofascist groups
  far_right = list(
    primary = c("fascismo", "fascista", "fascisti", "fasciste",
                "neofascista", "neofascisti", "neofascismo",
                "forza nuova", "casapound", "blocco studentesco"),
    context = c("scioglimento", "violenza", "aggressione", "squadrismo", 
                "saluto romano", "estrema destra"),
    negative = c()
  ),
  
  # 2. ANTIFASCIST ACTIVISM - anti-fascist protests/movements (separate from far_right discussion)
  antifascist = list(
    primary = c("antifascista", "antifascisti", "antifascismo"),
    context = c("manifestazione", "corteo", "protesta", "presidio", "anpi"),
    negative = c()
  ),
  
  # 3. UNIONS
  unions = list(
    primary = c("cgil", "cisl", "uil"),
    context = c("sciopero", "sindacato", "lavoratori"),
    negative = c()
  ),
  
  # 4. WORKERS/STRIKES
  workers = list(
    primary = c("lavoratori", "lavoratrici", "sciopero", "scioperi"),
    context = c("protesta", "manifestazione", "piazza", "corteo", "diritti"),
    negative = c()
  ),
  
  # 5. STUDENTS
  students = list(
    primary = c("studenti", "studentesse", "universitari", "movimento studentesco"),
    context = c("protesta", "manifestazione", "corteo", "occupazione"),
    negative = c()
  ),
  
  # 6. MIGRANTS (merged with NGO rescue)
  migrants = list(
    primary = c("migranti", "immigrati", "sbarchi", "ong", 
                "sea watch", "open arms", "ocean viking", "mediterraneo"),
    context = c("protesta", "solidarietà", "accoglienza", "soccorso"),
    negative = c()
  ),
  
  # 7. ENVIRONMENTALISTS
  environmentalists = list(
    primary = c("ultima generazione", "extinction rebellion", "fridays for future",
                "ambientalisti", "ecologisti", "eco-vandali", "ecovandali",
                "attivisti climatici"),
    context = c("blocco stradale", "protesta", "manifestazione", "clima"),
    negative = c()
  ),
  
  # 8. SOCIAL CENTRES
  social_centres = list(
    primary = c("centro sociale", "centri sociali", "autogestito", "autogestione",
                "askatasuna"),
    context = c("occupazione", "sgombero", "anarchici"),
    negative = c()
  ),
  
  # 9. PRO-PALESTINE
  pro_palestine = list(
    primary = c("gaza", "palestina", "palestinese", "palestinesi", 
                "free palestine", "pro-palestina"),
    context = c("manifestazione", "protesta", "corteo", "solidarietà"),
    negative = c()
  ),
  
  # 10. NO-VAX
  no_vax = list(
    primary = c("no vax", "novax", "no-vax", "free vax", "obbligo vaccinale"),
    context = c("protesta", "manifestazione", "piazza"),
    negative = c()
  ),
  
  # 11. NO-TAV (expanded)
  no_tav = list(
    primary = c("no tav", "notav", "no-tav", "val di susa", "valsusa", 
                "chiomonte", "no tap", "notap", "alta velocità"),
    context = c("protesta", "manifestazione", "cantiere", "attivisti"),
    negative = c()
  ),
  
  # 12. PRISONERS' RIGHTS
  prisoners_rights = list(
    primary = c("detenuti", "detenute", "rivolta carceraria", "rivolte carcerarie",
                "diritti dei detenuti"),
    context = c("protesta", "rivolta", "sovraffollamento", "condizioni"),
    negative = c()
  ),
  
  # 13. FEMINIST
  feminist = list(
    primary = c("femminista", "femministe", "femminismo", "non una di meno",
                "transfemminista"),
    context = c("manifestazione", "corteo", "protesta"),
    negative = c()
  ),
  
  # 14. LGBTQ
  lgbtq = list(
    primary = c("lgbt", "lgbtq", "lgbtqi", "omofobia", "gay pride", "pride",
                "ddl zan"),
    context = c("manifestazione", "diritti", "discriminazione"),
    negative = c()
  ),
  
  # 15. FAR-LEFT
  far_left = list(
    primary = c("anarchici", "anarchico", "anarchia", "comunisti", "comunista",
                "estrema sinistra"),
    context = c("protesta", "manifestazione", "violenza"),
    negative = c()
  )
)

cat("Defined", length(topic_definitions), "topics\n\n")

# ==============================================================================
# SCORING FUNCTION
# ==============================================================================

# Helper: check if phrase exists in text
phrase_in_text <- function(phrase, text) {
  grepl(phrase, text, fixed = TRUE, ignore.case = TRUE)
}

# Helper: get IDF weight for a term (handle multi-word by using default)
get_term_weight <- function(term, idf_lookup, default_weight = 4.0) {
  # For multi-word phrases, use a high default weight (they're distinctive)
  if (grepl(" ", term) || grepl("-", term)) {
    return(default_weight)
  }
  
  term_lower <- tolower(term)
  if (term_lower %in% names(idf_lookup)) {
    return(idf_lookup[[term_lower]])
  } else {
    return(default_weight)  # Unknown words get high weight
  }
}

# Score a speech for a single topic
score_topic <- function(text, topic_def, idf_lookup) {
  text_lower <- tolower(text)
  
  # 1. Check primary keywords (required)
  primary_score <- 0
  primary_matches <- 0
  
  for (term in topic_def$primary) {
    if (phrase_in_text(term, text_lower)) {
      weight <- get_term_weight(term, idf_lookup)
      # Count occurrences
      n_matches <- str_count(text_lower, fixed(tolower(term)))
      primary_score <- primary_score + (weight * sqrt(n_matches))  # diminishing returns
      primary_matches <- primary_matches + n_matches
    }
  }
  
  # If no primary matches, score is 0
  if (primary_matches == 0) {
    return(0)
  }
  
  # 2. Context boost (optional)
  context_boost <- 1.0
  if (length(topic_def$context) > 0) {
    context_matches <- sum(sapply(topic_def$context, phrase_in_text, text = text_lower))
    if (context_matches > 0) {
      context_boost <- 1.0 + (0.2 * min(context_matches, 3))  # max 1.6x boost
    }
  }
  
  # 3. Negative penalty (optional)
  negative_penalty <- 1.0
  if (length(topic_def$negative) > 0) {
    negative_matches <- sum(sapply(topic_def$negative, phrase_in_text, text = text_lower))
    if (negative_matches > 0) {
      negative_penalty <- 0.5 ^ negative_matches  # halve score for each negative match
    }
  }
  
  final_score <- primary_score * context_boost * negative_penalty
  return(final_score)
}

# ==============================================================================
# SCORE ALL SPEECHES
# ==============================================================================

cat("Scoring topics for each speech...\n")

topic_names <- names(topic_definitions)

# Create score matrix
score_matrix <- matrix(0, nrow = nrow(corpus_df), ncol = length(topic_names))
colnames(score_matrix) <- topic_names

for (i in 1:nrow(corpus_df)) {
  if (i %% 200 == 0) cat("  Processing speech", i, "/", nrow(corpus_df), "\n")
  
  text <- corpus_df$text[i]
  
  for (j in seq_along(topic_names)) {
    topic <- topic_names[j]
    topic_def <- topic_definitions[[topic]]
    score_matrix[i, j] <- score_topic(text, topic_def, word_idf_lookup)
  }
}

score_df <- as.data.frame(score_matrix)

# ==============================================================================
# ASSIGN DOMINANT TOPIC
# ==============================================================================

cat("\nAssigning dominant topics...\n")

get_dominant <- function(row) {
  scores <- as.numeric(row)
  if (max(scores) == 0) {
    return("other_general")
  } else {
    return(topic_names[which.max(scores)])
  }
}

score_df$dominant_topic <- apply(score_df[, topic_names], 1, get_dominant)
score_df$max_score <- apply(score_df[, topic_names], 1, max)

# Get second-best topic for close calls
get_second <- function(row) {
  scores <- as.numeric(row[topic_names])
  if (max(scores) == 0) return(NA)
  sorted_idx <- order(scores, decreasing = TRUE)
  if (scores[sorted_idx[2]] > 0) {
    return(topic_names[sorted_idx[2]])
  }
  return(NA)
}

score_df$second_topic <- apply(score_df, 1, get_second)

# Combine with original data
results_df <- bind_cols(corpus_df, score_df)

# ==============================================================================
# SUMMARY
# ==============================================================================

cat("\n==============================================\n")
cat("TOPIC DISTRIBUTION (v4 - TF-IDF + Co-occurrence)\n")
cat("==============================================\n\n")

topic_dist <- table(results_df$dominant_topic)
topic_dist_sorted <- sort(topic_dist, decreasing = TRUE)

for (topic in names(topic_dist_sorted)) {
  cat(sprintf("%-20s %4d (%5.1f%%)\n", 
              topic, 
              topic_dist_sorted[topic],
              100 * topic_dist_sorted[topic] / nrow(results_df)))
}

cat("\n")
assigned <- sum(results_df$dominant_topic != "other_general")
cat("Speeches with topic assigned:", assigned, "\n")
cat("Speeches with NO topic (other_general):", nrow(results_df) - assigned, "\n")
cat("Coverage:", round(100 * assigned / nrow(results_df), 1), "%\n")

# ==============================================================================
# CONFIDENCE ANALYSIS
# ==============================================================================

cat("\n==============================================\n")
cat("SCORE DISTRIBUTION (confidence proxy)\n")
cat("==============================================\n\n")

assigned_df <- results_df %>% filter(dominant_topic != "other_general")

cat("Max scores for assigned topics:\n")
cat("  Min:", round(min(assigned_df$max_score), 2), "\n")
cat("  Median:", round(median(assigned_df$max_score), 2), "\n")
cat("  Mean:", round(mean(assigned_df$max_score), 2), "\n")
cat("  Max:", round(max(assigned_df$max_score), 2), "\n")

# Low confidence assignments (might need review)
low_conf <- assigned_df %>% 
  filter(max_score < quantile(max_score, 0.25))
cat("\nLow confidence assignments (<25th percentile):", nrow(low_conf), "\n")

# ==============================================================================
# TOPICS BY PARTY
# ==============================================================================

cat("\n==============================================\n")
cat("TOPICS BY PARTY (top 8 parties)\n")
cat("==============================================\n\n")

top_parties <- results_df %>%
  count(party) %>%
  arrange(desc(n)) %>%
  head(8) %>%
  pull(party)

topics_by_party <- results_df %>%
  filter(party %in% top_parties) %>%
  count(party, dominant_topic) %>%
  pivot_wider(names_from = dominant_topic, values_from = n, values_fill = 0)

print(topics_by_party)

# ==============================================================================
# SAVE OUTPUTS
# ==============================================================================

cat("\n==============================================\n")
cat("SAVING OUTPUTS\n")
cat("==============================================\n\n")

write_csv(results_df, file.path(OUTPUT_DIR, "corpus_with_topics_v4.csv"))
cat("Saved: corpus_with_topics_v4.csv\n")

# Save topic summary
topic_summary <- results_df %>%
  group_by(dominant_topic) %>%
  summarise(
    n = n(),
    pct = round(100 * n() / nrow(results_df), 1),
    avg_score = round(mean(max_score), 2),
    .groups = "drop"
  ) %>%
  arrange(desc(n))

write_csv(topic_summary, file.path(OUTPUT_DIR, "topic_summary_v4.csv"))
cat("Saved: topic_summary_v4.csv\n")

# ==============================================================================
# EXPORT FOR QUALITY REVIEW
# ==============================================================================

cat("\n==============================================\n")
cat("EXPORTING SAMPLES FOR QUALITY REVIEW\n")
cat("==============================================\n\n")

set.seed(42)

review_samples <- results_df %>%
  filter(dominant_topic != "other_general") %>%
  group_by(dominant_topic) %>%
  slice_sample(n = 10, replace = FALSE) %>%
  ungroup() %>%
  mutate(
    text_preview = substr(text, 1, 500)
  ) %>%
  select(speech_id, year, party, dominant_topic, second_topic, max_score, text_preview) %>%
  arrange(dominant_topic, desc(max_score))

write_csv(review_samples, file.path(OUTPUT_DIR, "quality_review_samples_v4.csv"))
cat("Saved: quality_review_samples_v4.csv\n")
cat("Total samples:", nrow(review_samples), "\n")

cat("\n==============================================\n")
cat("STEP 1 v4 COMPLETE!\n")
cat("==============================================\n")
cat("\nOutput files in:", OUTPUT_DIR, "\n")
