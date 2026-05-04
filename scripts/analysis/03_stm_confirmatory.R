#!/usr/bin/env Rscript
# =============================================================================
# 03_stm_confirmatory.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2025
#
# PURPOSE: Run Structural Topic Modelling (STM) for each activism topic with
#   n >= 30 speeches. STM is used in a confirmatory role: to verify that
#   meaningful thematic clusters exist within each topic before proceeding to
#   keyness analysis. Party affiliation is a prevalence covariate.
#   Applied to keyword windows, not full speech texts.
#
# INPUT:  /Users/camillagazzola/Desktop/thesis_test/output/corpus_with_windows.csv
# OUTPUT: /Users/camillagazzola/Desktop/thesis_test/output/stm_frames_summary.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/stm_party_effects.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/stm_models.rds
#
# Run from anywhere:
#   Rscript /Users/camillagazzola/Desktop/thesis_test/03_stm_confirmatory.R
# =============================================================================

library(tidyverse)
library(stm)
library(quanteda)

# ── PATHS ─────────────────────────────────────────────────────────────────────

INPUT_CSV  <- "/Users/camillagazzola/Desktop/thesis_test/output/corpus_with_windows.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/thesis_test/output"

MIN_SPEECHES <- 30
K_TOPICS     <- 4

# ── STOPWORDS ─────────────────────────────────────────────────────────────────

italian_stopwords <- c(
  stopwords("it"),
  "presidente","onorevoli","colleghi","governo","ministro","commissione",
  "camera","senato","decreto","legge","articolo","emendamento","ordine",
  "giorno","perché","quindi","infatti","essere","fare","dire","vedere",
  "anno","anni","cosa","modo","parte","fatto","oggi","ieri","qui","così",
  "ancora","sempre","molto","poco","tanto","questo","quello","tutto",
  "ogni","altro","stesso","proprio","più","meno","ora","già","mai",
  "solo","anche","però","quando","come","dove","quale","quanto","chi",
  "grazie","ringrazio","onorevole","signor","signora",
  "dell","della","dello","degli","delle","nell","nella",
  "sull","sulla","dall","dalla","all","alla"
)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────

cat("Loading corpus with windows...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE) %>%
  filter(!is.na(keyword_window), nchar(keyword_window) > 20) %>%
  filter(!is.na(party_clean), party_clean != "MISTO") %>%
  mutate(year = as.integer(year))

cat("Speeches:", nrow(df), "\n")
cat("Topics:  ", n_distinct(df$topic), "\n\n")

# ── STM FUNCTION ──────────────────────────────────────────────────────────────

run_stm <- function(topic_name, data, k = K_TOPICS) {
  cat("\n", strrep("-", 50), "\n")
  cat("Topic:", toupper(topic_name), "\n")

  topic_df <- data %>% filter(topic == topic_name)
  cat("  n =", nrow(topic_df), "\n")

  if (nrow(topic_df) < MIN_SPEECHES) {
    cat("  Skipping — below minimum\n"); return(NULL)
  }

  corp  <- corpus(topic_df, text_field = "keyword_window")
  toks  <- tokens(corp, remove_punct = TRUE, remove_numbers = TRUE) %>%
    tokens_tolower() %>%
    tokens_remove(italian_stopwords) %>%
    tokens_wordstem(language = "italian")
  dfm_t <- dfm(toks) %>% dfm_trim(min_termfreq = 3, min_docfreq = 2)

  if (nfeat(dfm_t) < 30) {
    cat("  Skipping — too few features\n"); return(NULL)
  }
  cat("  Features:", nfeat(dfm_t), "\n")

  stm_data <- convert(dfm_t, to = "stm")
  meta     <- topic_df %>% select(party_clean, year) %>% as.data.frame()

  cat("  Fitting STM (K =", k, ")...\n")
  model <- tryCatch(
    stm(documents  = stm_data$documents, vocab = stm_data$vocab,
        K          = k, prevalence = ~ party_clean, data = meta,
        max.em.its = 75, init.type = "Spectral", verbose = FALSE),
    error = function(e) { cat("  Failed:", e$message, "\n"); NULL }
  )
  if (is.null(model)) return(NULL)

  tw <- labelTopics(model, n = 10)
  cat("  Frames:\n")
  for (i in 1:k)
    cat("    Frame", i, ":", paste(tw$prob[i, 1:7], collapse = ", "), "\n")

  party_effects <- tryCatch(
    estimateEffect(1:k ~ party_clean, model, meta = meta, uncertainty = "Global"),
    error = function(e) NULL
  )

  list(topic = topic_name, n = nrow(topic_df), k = k,
       model = model, top_words = tw,
       party_effects = party_effects, meta = meta)
}

# ── RUN ───────────────────────────────────────────────────────────────────────

topics_to_run <- df %>%
  count(topic) %>% filter(n >= MIN_SPEECHES) %>% pull(topic)

cat("Topics to model:", paste(topics_to_run, collapse = ", "), "\n")

all_results <- list()
for (t in topics_to_run) {
  res <- run_stm(t, df)
  if (!is.null(res)) all_results[[t]] <- res
}

# ── SAVE ──────────────────────────────────────────────────────────────────────

saveRDS(all_results, file.path(OUTPUT_DIR, "stm_models.rds"))
cat("\n✓ stm_models.rds\n")

frame_rows <- list()
for (topic in names(all_results)) {
  tw <- all_results[[topic]]$top_words
  for (i in 1:all_results[[topic]]$k)
    frame_rows[[length(frame_rows)+1]] <- tibble(
      topic      = topic, frame_id = i,
      frame_words = paste(tw$prob[i, 1:10], collapse = ", "),
      frex_words  = paste(tw$frex[i, 1:10], collapse = ", ")
    )
}
bind_rows(frame_rows) %>%
  write_csv(file.path(OUTPUT_DIR, "stm_frames_summary.csv"))
cat("✓ stm_frames_summary.csv\n")

effect_rows <- list()
for (topic in names(all_results)) {
  res     <- all_results[[topic]]
  if (is.null(res$party_effects)) next
  parties  <- unique(res$meta$party_clean)
  baseline <- parties[1]

  for (i in 1:res$k) {
    words <- paste(res$top_words$prob[i, 1:10], collapse = ", ")
    for (p in parties) {
      s        <- summary(res$party_effects, topics = i,
                          covariate = "party_clean", model = res$model)
      coef_row <- tryCatch(s$tables[[1]][paste0("party_clean", p), ], error = function(e) NULL)
      effect_rows[[length(effect_rows)+1]] <- tibble(
        topic       = topic, frame_id = i, frame_words = words, party = p,
        estimate    = if (!is.null(coef_row)) coef_row["Estimate"]   else NA,
        std_error   = if (!is.null(coef_row)) coef_row["Std. Error"] else NA,
        is_baseline = (p == baseline)
      )
    }
  }
}
if (length(effect_rows) > 0) {
  bind_rows(effect_rows) %>%
    write_csv(file.path(OUTPUT_DIR, "stm_party_effects.csv"))
  cat("✓ stm_party_effects.csv\n")
}

cat("\nDone.\n")
