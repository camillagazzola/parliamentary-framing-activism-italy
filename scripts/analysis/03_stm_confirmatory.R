#!/usr/bin/env Rscript
# =============================================================================
# 03_stm_confirmatory.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2026
#
# PURPOSE: Run Structural Topic Modelling (STM) for each activism topic with
#   n >= 30 speeches. STM is used in a confirmatory role: to verify that
#   meaningful latent word clusters exist within each topic before proceeding
#   to keyness analysis. Party affiliation is a prevalence covariate.
#   Applied to keyword windows, not full speech texts.
#
# INPUT:  data/corpus_with_windows.csv
# OUTPUT: data/stm_models.rds
#         data/stm_clusters_summary.csv
#         data/stm_party_effects.csv
# =============================================================================

library(tidyverse)
library(stm)
library(quanteda)

BASE       <- here::here()
INPUT_CSV  <- file.path(BASE, "data", "corpus_with_windows.csv")
OUTPUT_DIR <- file.path(BASE, "data")


MIN_SPEECHES <- 30


K_BY_TOPIC <- c(
  incarcerated_persons = 2,
  climate_activists    = 2,
  police_security      = 2,
  labor                = 2,
  far_right            = 2,
  students             = 2,
  no_vax               = 2,
  migrants             = 3,
  pro_palestine        = 3,
  antisemitism         = 3
)

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

cat("Speeches:", nrow(df), "\n")
cat("Topics:  ", n_distinct(df$topic), "\n\n")

run_stm <- function(topic_name, data, k = K_TOPICS) {
  cat("\nTopic:", toupper(topic_name), "\n")
  
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
  for (i in 1:k)
    cat("  Cluster", i, ":", paste(tw$prob[i, 1:7], collapse = ", "), "\n")
  
  party_effects <- tryCatch(
    estimateEffect(1:k ~ party_clean, model, meta = meta, uncertainty = "Global"),
    error = function(e) NULL
  )
  
  list(topic = topic_name, n = nrow(topic_df), k = k,
       model = model, top_words = tw,
       party_effects = party_effects, meta = meta)
}

topics_to_run <- df %>%
  count(topic) %>% filter(n >= MIN_SPEECHES) %>% pull(topic)

cat("Topics to model:", paste(topics_to_run, collapse = ", "), "\n")

all_results <- list()
for (t in topics_to_run) {
  k   <- K_BY_TOPIC[t]
  if (is.na(k)) k <- K_TOPICS  # fallback to default if topic not listed
  res <- run_stm(t, df, k = k)
  if (!is.null(res)) all_results[[t]] <- res
}

saveRDS(all_results, file.path(OUTPUT_DIR, "stm_models.rds"))
cat("\nstm_models.rds saved\n")

cluster_rows <- list()
for (topic in names(all_results)) {
  tw <- all_results[[topic]]$top_words
  for (i in 1:all_results[[topic]]$k)
    cluster_rows[[length(cluster_rows)+1]] <- tibble(
      topic         = topic, cluster_id = i,
      cluster_words = paste(tw$prob[i, 1:10], collapse = ", "),
      cluster_frex  = paste(tw$frex[i, 1:10], collapse = ", ")
    )
}
bind_rows(cluster_rows) %>%
  write_csv(file.path(OUTPUT_DIR, "stm_clusters_summary.csv"))

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
        topic         = topic, cluster_id = i, cluster_words = words, party = p,
        estimate      = if (!is.null(coef_row)) coef_row["Estimate"]   else NA,
        std_error     = if (!is.null(coef_row)) coef_row["Std. Error"] else NA,
        is_baseline   = (p == baseline)
      )
    }
  }
}
if (length(effect_rows) > 0) {
  bind_rows(effect_rows) %>%
    write_csv(file.path(OUTPUT_DIR, "stm_party_effects.csv"))
}

cat("Done.\n")
