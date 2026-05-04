#!/usr/bin/env Rscript
# =============================================================================
# 03a_stm_searchK.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2025
#
# PURPOSE: Determine the optimal number of topics (K) for STM by running
#   searchK() across K = 2:7 for each activism topic with sufficient
#   observations (n >= 30). Evaluates held-out likelihood, semantic coherence,
#   and residuals to select the best K per topic.
#
# Run BEFORE 03_stm_confirmatory.R. Once you have the results, update
#   K_TOPICS in 03_stm_confirmatory.R to the recommended value.
#
# INPUT:  /Users/camillagazzola/Desktop/thesis_test/output/corpus_with_windows.csv
# OUTPUT: /Users/camillagazzola/Desktop/thesis_test/output/searchK_results.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/searchK_plots/
#
# Run from anywhere:
#   Rscript /Users/camillagazzola/Desktop/thesis_test/03a_stm_searchK.R
# =============================================================================

library(tidyverse)
library(stm)
library(quanteda)

# ── PATHS ─────────────────────────────────────────────────────────────────────

INPUT_CSV  <- "/Users/camillagazzola/Desktop/thesis_test/output/corpus_with_windows.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/thesis_test/output"
PLOT_DIR   <- "/Users/camillagazzola/Desktop/thesis_test/output/searchK_plots"

dir.create(PLOT_DIR, recursive = TRUE, showWarnings = FALSE)

MIN_SPEECHES <- 30
K_RANGE      <- 2:7   # test K = 2, 3, 4, 5, 6, 7

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

cat("Speeches:", nrow(df), "\n\n")

topics_to_run <- df %>%
  count(topic) %>%
  filter(n >= MIN_SPEECHES) %>%
  arrange(desc(n)) %>%
  pull(topic)

cat("Topics to evaluate:", paste(topics_to_run, collapse = ", "), "\n\n")

# ── SEARCHK FUNCTION ──────────────────────────────────────────────────────────

run_searchK <- function(topic_name, data, k_range = K_RANGE) {
  cat("\n", strrep("-", 50), "\n")
  cat("Topic:", toupper(topic_name), "\n")

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
  cat("  (This takes a few minutes per topic)\n")

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

  # Extract metrics
  metrics <- result$results %>%
    mutate(topic = topic_name)

  # Print summary
  cat("\n  K | Coherence | Held-out likelihood | Residuals\n")
  for (i in seq_len(nrow(metrics))) {
    cat(sprintf("  %d |  %6.1f   |       %8.1f      |  %6.3f\n",
                metrics$K[[i]],
                metrics$semcoh[[i]],
                metrics$heldout[[i]],
                metrics$residual[[i]]))
  }

  # Save plot
  plot_path <- file.path(PLOT_DIR, paste0("searchK_", topic_name, ".pdf"))
  pdf(plot_path, width = 10, height = 6)
  plot(result, main = paste("searchK —", topic_name))
  dev.off()
  cat("  Plot saved:", plot_path, "\n")

  metrics
}

# ── RUN FOR ALL TOPICS ────────────────────────────────────────────────────────

all_metrics <- list()
for (t in topics_to_run) {
  res <- run_searchK(t, df)
  if (!is.null(res)) all_metrics[[t]] <- res
}

# ── COMBINE AND SAVE ──────────────────────────────────────────────────────────

if (length(all_metrics) > 0) {
  metrics_df <- bind_rows(all_metrics)

  # Unnest list columns
  metrics_clean <- metrics_df %>%
    mutate(
      K         = as.integer(unlist(K)),
      semcoh    = as.numeric(unlist(semcoh)),
      heldout   = as.numeric(unlist(heldout)),
      residual  = as.numeric(unlist(residual)),
      lbound    = as.numeric(unlist(lbound))
    ) %>%
    select(topic, K, semcoh, heldout, residual, lbound)

  write_csv(metrics_clean,
            file.path(OUTPUT_DIR, "searchK_results.csv"))
  cat("\n✓ searchK_results.csv\n")

  # Print recommended K per topic
  cat("\n", strrep("=", 60), "\n")
  cat("RECOMMENDED K PER TOPIC\n")
  cat("(highest held-out likelihood = best predictive fit)\n")
  cat(strrep("=", 60), "\n\n")

  recommendations <- metrics_clean %>%
    group_by(topic) %>%
    slice_max(heldout, n = 1) %>%
    ungroup() %>%
    select(topic, K, semcoh, heldout, residual) %>%
    arrange(desc(heldout))

  print(recommendations, n = 20)

  cat("\nNote: held-out likelihood is the primary criterion.\n")
  cat("If recommended K varies widely across topics, consider\n")
  cat("using a single K for consistency and comparability.\n")
}

cat("\nDone. Check searchK_plots/ for visual diagnostics.\n")
