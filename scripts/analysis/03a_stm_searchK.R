#!/usr/bin/env Rscript
# =============================================================================
# 03a_stm_searchK.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2026
#
# PURPOSE: Determine the optimal number of latent clusters (K) for STM by
#   running searchK() across K = 2:7 for each activism topic with n >= 30
#   speeches. Evaluates held-out likelihood and semantic coherence to select
#   the best K per topic. Run before 03_stm_confirmatory.R.
#
# INPUT:  data/corpus_with_windows.csv
# OUTPUT: data/searchK_results.csv
#         data/searchK_plots/
# =============================================================================

library(tidyverse)
library(stm)
library(quanteda)

BASE       <- here::here()
INPUT_CSV  <- file.path(BASE, "data", "corpus_with_windows.csv")
OUTPUT_DIR <- file.path(BASE, "data")
PLOT_DIR   <- file.path(BASE, "data", "searchK_plots")

dir.create(PLOT_DIR, recursive = TRUE, showWarnings = FALSE)

MIN_SPEECHES <- 30
K_RANGE      <- 2:7

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

cat("Loading corpus...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE) %>%
  filter(!is.na(keyword_window), nchar(keyword_window) > 20) %>%
  filter(!is.na(party_clean), party_clean != "MISTO") %>%
  mutate(year = as.integer(year))

cat("Speeches:", nrow(df), "\n\n")

topics_to_run <- df %>%
  count(topic) %>%
  filter(n >= MIN_SPEECHES) %>%
  arrange(desc(n)) %>%
  pull(topic)

cat("Topics to evaluate:", paste(topics_to_run, collapse = ", "), "\n\n")

run_searchK <- function(topic_name, data, k_range = K_RANGE) {
  cat("\nTopic:", toupper(topic_name), "\n")

  topic_df <- data %>% filter(topic == topic_name)
  cat("  n =", nrow(topic_df), "\n")

  corp  <- corpus(topic_df, text_field = "keyword_window")
  toks  <- tokens(corp, remove_punct = TRUE, remove_numbers = TRUE) %>%
    tokens_tolower() %>%
    tokens_remove(italian_stopwords) %>%
    tokens_wordstem(language = "italian")
  dfm_t <- dfm(toks) %>% dfm_trim(min_termfreq = 3, min_docfreq = 2)

  if (nfeat(dfm_t) < 30) {
    cat("  Skipping — too few features\n")
    return(NULL)
  }
  cat("  Features:", nfeat(dfm_t), "\n")

  stm_data <- convert(dfm_t, to = "stm")
  meta     <- topic_df %>% select(party_clean, year) %>% as.data.frame()

  cat("  Running searchK for K =", paste(k_range, collapse = ", "), "...\n")

  result <- tryCatch(
    searchK(
      documents  = stm_data$documents,
      vocab      = stm_data$vocab,
      K          = k_range,
      prevalence = ~ party_clean,
      data       = meta,
      init.type  = "Spectral",
      verbose    = FALSE
    ),
    error = function(e) {
      cat("  searchK failed:", e$message, "\n")
      NULL
    }
  )

  if (is.null(result)) return(NULL)

  metrics <- result$results %>%
    mutate(topic = topic_name)

  cat("\n  K | Coherence | Held-out likelihood | Residuals\n")
  for (i in seq_len(nrow(metrics))) {
    cat(sprintf("  %d |  %6.1f   |       %8.1f      |  %6.3f\n",
                metrics$K[[i]],
                metrics$semcoh[[i]],
                metrics$heldout[[i]],
                metrics$residual[[i]]))
  }

  plot_path <- file.path(PLOT_DIR, paste0("searchK_", topic_name, ".pdf"))
  pdf(plot_path, width = 10, height = 6)
  plot(result, main = paste("searchK —", topic_name))
  dev.off()

  metrics
}

all_metrics <- list()
for (t in topics_to_run) {
  res <- run_searchK(t, df)
  if (!is.null(res)) all_metrics[[t]] <- res
}

if (length(all_metrics) > 0) {
  metrics_clean <- bind_rows(all_metrics) %>%
    mutate(
      K        = as.integer(unlist(K)),
      semcoh   = as.numeric(unlist(semcoh)),
      heldout  = as.numeric(unlist(heldout)),
      residual = as.numeric(unlist(residual)),
      lbound   = as.numeric(unlist(lbound))
    ) %>%
    select(topic, K, semcoh, heldout, residual, lbound)

  write_csv(metrics_clean, file.path(OUTPUT_DIR, "searchK_results.csv"))

  recommendations <- metrics_clean %>%
    group_by(topic) %>%
    slice_max(heldout, n = 1) %>%
    ungroup() %>%
    select(topic, K, semcoh, heldout, residual) %>%
    arrange(desc(heldout))

  cat("\nRecommended K per topic (by held-out likelihood):\n")
  print(recommendations, n = 20)
}

cat("\nDone.\n")
