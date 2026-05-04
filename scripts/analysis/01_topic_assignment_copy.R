#!/usr/bin/env Rscript
# =============================================================================
# 01_topic_assignment.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2025
#
# PURPOSE: Assign each speech to one of 14 activism topics using a two-stage
#   hybrid classification procedure:
#
#   STAGE 1 — Dictionary classification (candidate identification)
#     All matched topics, matched keywords, match counts, priority levels, and
#     a confidence score are recorded. A provisional topic is assigned using the
#     priority + count heuristic, but cases with weak or ambiguous evidence are
#     flagged rather than silently assigned.
#
#   STAGE 2 — Manual validation of flagged cases
#     Speeches are flagged for manual review when:
#       (a) more than one topic matches           [multi-match]
#       (b) only one weak keyword matches         [weak single match]
#       (c) a broad category wins (labour,
#           students, police/security)            [broad category winner]
#       (d) priority overrides a larger match
#           count from a lower-priority topic     [priority override]
#     Flagged speeches are exported to a dedicated review file.
#     Reviewer should assign a final topic (or "unassigned") in the
#     manual_topic column and re-merge before analysis.
#
#   STAGE 3 — Validation sample
#     A stratified sample (20 per category + 20 unassigned + all multi-match
#     cases up to a cap) is exported for precision reporting in the methodology.
#
#   Confidence score logic
#     High:   single match, priority 1-2, >= 2 keyword hits
#     Medium: single match, any priority, 1 keyword hit OR
#             multi-match resolved cleanly by priority
#     Low:    anything flagged for review
#
#   This hybrid procedure preserves the transparency of dictionary
#   classification while reducing misclassification in ambiguous cases.
#   See methodology note at end of script for suggested reporting text.
#
#   Priority system (unchanged from original)
#     Priority 1 — named movements / organisations (most specific)
#     Priority 2 — clear movement categories
#     Priority 3 — broader categories (can overlap)
#
#   Methodological basis: Laver, Benoit and Garry (2003); Grimmer and
#   Stewart (2013); validation approach following Benoit et al. (2016).
#
# INPUT:  /Users/camillagazzola/Desktop/thesis_test/output/activism_corpus_final.csv
# OUTPUT: /Users/camillagazzola/Desktop/thesis_test/output/corpus_with_topics.csv
#           — full corpus with provisional_topic, confidence, flags, all_matches
#         /Users/camillagazzola/Desktop/thesis_test/output/flagged_for_review.csv
#           — speeches requiring manual coding (Stage 2)
#         /Users/camillagazzola/Desktop/thesis_test/output/validation_sample.csv
#           — stratified sample for precision reporting (Stage 3)
#         /Users/camillagazzola/Desktop/thesis_test/output/topic_summary.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/topic_by_party.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/topic_by_year.csv
#
# Run from anywhere:
#   Rscript /Users/camillagazzola/Desktop/thesis_test/01_topic_assignment.R
# =============================================================================

library(tidyverse)
library(stringr)

# -----------------------------------------------------------------------------
# PATHS
# -----------------------------------------------------------------------------
INPUT_CSV  <- "/Users/camillagazzola/Desktop/thesis_test/output/activism_corpus_final.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/thesis_test/output"

# Flag control: broad-category topics that trigger a review flag even when they
# win cleanly, because they are most prone to false positives.
BROAD_CATEGORIES <- c("labor", "students", "police_security")

# Minimum keyword hits for a match to be considered "strong" (not weak).
WEAK_MATCH_THRESHOLD <- 2   # hits strictly below this → flagged as weak

# Validation sample size per category (Stage 3)
VALIDATION_N_PER_CATEGORY <- 20
VALIDATION_N_UNASSIGNED   <- 20

# -----------------------------------------------------------------------------
# TOPIC DEFINITIONS
# (unchanged from original — only the classifier logic changes)
# -----------------------------------------------------------------------------
topic_definitions <- list(

  # PRIORITY 1: named movements / organisations
  no_tav = list(priority = 1,
    keywords = c("no.?tav","notav","val.?susa","valsusa","chiomonte","no.?tap","notap")),

  climate_activists = list(priority = 1,
    keywords = c("ultima.generazione","extinction.rebellion","fridays.for.future",
                 "ecoattivisti","eco.?vandal","imbrattato","imbrattare",
                 "blocco.stradale","blocchi.stradali")),

  pro_palestine = list(priority = 1,
    keywords = c("palestina","palestinese","palestinesi","\\bgaza\\b",
                 "\\bhamas\\b","intifada","nakba",
                 "\\bsionista\\b","\\bsionisti\\b","\\bsionismo\\b")),

  no_vax = list(priority = 1,
    keywords = c("no.?vax","novax","green.?pass","obbligo.vaccinale","dittatura.sanitaria")),

  lgbtq = list(priority = 1,
    keywords = c("\\blgbt","\\blgbtq","\\bglbt","\\bglbtq","omofobia","transfobia",
                 "omotransfobia","ddl.zan","\\bpride\\b","unioni.civili","omosessual")),

  antisemitism = list(priority = 1,
    keywords = c("antisemit","\\bshoah\\b","\\bsegre\\b","\\bebrei\\b","\\bebreo\\b",
                 "\\bebraica\\b","\\bebraismo\\b","stella.di.david","sinagog",
                 "giornata.della.memoria","deportazione.ebrei")),

  # PRIORITY 2: clear movement categories
  far_right = list(priority = 2,
    keywords = c("casapound","forza.nuova","neofascist","estrema.destra",
                 "saluto.romano","squadrist","squadrismo","\\bcamerata\\b")),

  antifascist = list(priority = 2,
    keywords = c("antifascist","antifascismo","\\banpi\\b","partigian",
                 "25.aprile","venticinque.aprile")),

  far_left = list(priority = 2,
    keywords = c("centri.sociali","centro.sociale","black.bloc",
                 "anarch","antagonist","\\bautonomi\\b","\\bsquat\\b")),

  migrants = list(priority = 2,
    keywords = c("migranti","immigrat","rifugiat","profugh","richiedenti.asilo",
                 "sbarchi","sbarco","\\bong\\b","sea.watch","open.arms",
                 "mediterranea","clandestin","accoglienza","\\bcpr\\b","\\bcie\\b",
                 "hotspot","respingiment","decreto.salvini","decreti.salvini")),

  prisoners_rights = list(priority = 2,
    keywords = c("\\bcarcere\\b","\\bcarceri\\b","\\bdetenu","penitenziario",
                 "penitenziari","sovraffollamento","41.bis","ergastolo.ostativo",
                 "\\bcelle\\b","rivolt.+carcer")),

  # PRIORITY 3: broader categories
  students = list(priority = 3,
    keywords = c("\\bstudenti\\b","\\bstudentesse\\b","\\buniversitari\\b",
                 "movimento.studentesco","\\bliceo\\b","\\blicei\\b",
                 "occupazion.+student","\\bcollettiv")),

  labor = list(priority = 3,
    keywords = c("\\bcgil\\b","\\bcisl\\b","\\buil\\b","sindacat","scioper",
                 "lavoratori","lavoratrici","\\boperai\\b","\\boperaio\\b",
                 "fabbric","licenziament","disoccupat","\\bprecar","vertenz")),

  police_security = list(priority = 3,
    keywords = c("forze.dell.ordine","\\bpolizia\\b","\\bcarabinieri\\b",
                 "\\bagenti\\b","\\bdivisa\\b","\\bquestura\\b","\\bquesture\\b",
                 "polizia.penitenziaria","pubblica.sicurezza"))
)

cat("Topics defined:", length(topic_definitions), "\n\n")

# -----------------------------------------------------------------------------
# STAGE 1 CLASSIFIER
# Returns a named list with:
#   provisional_topic   — best candidate by priority + count heuristic
#   all_matches         — semicolon-separated "topic(p=X,n=Y)" for all matches
#   matched_keywords    — keywords that fired for the winner
#   match_count         — number of keyword hits for the winner
#   n_topics_matched    — how many topics matched at all
#   confidence          — high / medium / low
#   review_flag         — logical: needs manual validation?
#   flag_reason         — why it was flagged (empty string if not flagged)
# -----------------------------------------------------------------------------
classify_speech <- function(text, topic_defs,
                             broad_cats = BROAD_CATEGORIES,
                             weak_threshold = WEAK_MATCH_THRESHOLD) {

  # Empty / NA text
  if (is.na(text) || nchar(trimws(text)) == 0) {
    return(list(
      provisional_topic  = "unassigned",
      all_matches        = "",
      matched_keywords   = "",
      match_count        = 0L,
      n_topics_matched   = 0L,
      confidence         = "none",
      review_flag        = FALSE,
      flag_reason        = "no text"
    ))
  }

  text_lower <- tolower(text)
  matches    <- list()

  # Collect all matching topics
  for (topic_name in names(topic_defs)) {
    config     <- topic_defs[[topic_name]]
    matched_kw <- character(0)
    for (pattern in config$keywords) {
      if (str_detect(text_lower, regex(pattern, ignore_case = TRUE))) {
        found      <- str_extract_all(text_lower,
                                      regex(pattern, ignore_case = TRUE))[[1]]
        matched_kw <- c(matched_kw, found)
      }
    }
    if (length(matched_kw) > 0) {
      matches[[topic_name]] <- list(
        count    = length(matched_kw),
        keywords = unique(matched_kw),
        priority = config$priority
      )
    }
  }

  # No match at all
  if (length(matches) == 0) {
    return(list(
      provisional_topic  = "unassigned",
      all_matches        = "",
      matched_keywords   = "",
      match_count        = 0L,
      n_topics_matched   = 0L,
      confidence         = "none",
      review_flag        = FALSE,
      flag_reason        = "no keyword matches"
    ))
  }

  # Build ranked data frame (priority ASC, count DESC)
  match_df <- tibble(
    topic    = names(matches),
    priority = sapply(matches, `[[`, "priority"),
    count    = sapply(matches, `[[`, "count")
  ) %>% arrange(priority, desc(count))

  winner        <- match_df$topic[1]
  winner_priority <- match_df$priority[1]
  winner_count  <- match_df$count[1]
  n_matched     <- nrow(match_df)

  # Compact all_matches string: "no_tav(p=1,n=3); labor(p=3,n=1)"
  all_matches_str <- paste(
    sprintf("%s(p=%d,n=%d)", match_df$topic, match_df$priority, match_df$count),
    collapse = "; "
  )

  # ------------------------------------------------------------------
  # FLAG LOGIC
  # ------------------------------------------------------------------
  flag_reasons <- character(0)

  # (a) Multiple topics matched
  if (n_matched > 1) {
    flag_reasons <- c(flag_reasons, "multi-match")
  }

  # (b) Weak single match (fewer than threshold keyword hits)
  if (winner_count < weak_threshold) {
    flag_reasons <- c(flag_reasons, "weak match")
  }

  # (c) Broad category winner
  if (winner %in% broad_cats) {
    flag_reasons <- c(flag_reasons, "broad category winner")
  }

  # (d) Priority override: winner has lower count than a lower-priority match
  if (n_matched > 1) {
    runner_up_count <- match_df$count[2]
    runner_up_prio  <- match_df$priority[2]
    if (winner_priority < runner_up_prio && runner_up_count > winner_count) {
      flag_reasons <- c(flag_reasons, "priority override of higher-count topic")
    }
  }

  review_flag <- length(flag_reasons) > 0
  flag_reason <- paste(flag_reasons, collapse = "; ")

  # ------------------------------------------------------------------
  # CONFIDENCE SCORE
  # ------------------------------------------------------------------
  confidence <- dplyr::case_when(
    review_flag                                        ~ "low",
    n_matched == 1 & winner_priority <= 2 &
      winner_count >= weak_threshold                   ~ "high",
    TRUE                                               ~ "medium"
  )

  list(
    provisional_topic  = winner,
    all_matches        = all_matches_str,
    matched_keywords   = paste(matches[[winner]]$keywords, collapse = ", "),
    match_count        = as.integer(winner_count),
    n_topics_matched   = as.integer(n_matched),
    confidence         = confidence,
    review_flag        = review_flag,
    flag_reason        = flag_reason
  )
}

# -----------------------------------------------------------------------------
# LOAD
# -----------------------------------------------------------------------------
cat("Loading corpus...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE)
cat("Speeches:", nrow(df), "\n")
cat("Parties: ", paste(sort(unique(df$party_clean)), collapse = ", "), "\n\n")

# -----------------------------------------------------------------------------
# CLASSIFY (Stage 1)
# -----------------------------------------------------------------------------
cat("Classifying speeches (Stage 1 — dictionary)...\n")
results <- lapply(df$text, classify_speech, topic_defs = topic_definitions)

df$provisional_topic <- sapply(results, `[[`, "provisional_topic")
df$all_matches       <- sapply(results, `[[`, "all_matches")
df$matched_keywords  <- sapply(results, `[[`, "matched_keywords")
df$match_count       <- sapply(results, `[[`, "match_count")
df$n_topics_matched  <- sapply(results, `[[`, "n_topics_matched")
df$confidence        <- sapply(results, `[[`, "confidence")
df$review_flag       <- sapply(results, `[[`, "review_flag")
df$flag_reason       <- sapply(results, `[[`, "flag_reason")

# Placeholder for Stage 2 manual coding — reviewer fills this column
df$manual_topic <- NA_character_

# Final topic: manual_topic if provided, else provisional_topic
# (After manual review, re-run only this line or merge back in.)
df$final_topic <- ifelse(!is.na(df$manual_topic),
                         df$manual_topic,
                         df$provisional_topic)

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------
cat("\n", strrep("=", 60), "\n")
cat("STAGE 1 — PROVISIONAL TOPIC DISTRIBUTION\n")
cat(strrep("=", 60), "\n\n")

topic_dist <- df %>%
  count(provisional_topic, name = "n") %>%
  mutate(pct = round(100 * n / nrow(df), 1)) %>%
  arrange(desc(n))
print(topic_dist, n = 20)

cat("\nAssigned (provisional):  ",
    sum(df$provisional_topic != "unassigned"),
    sprintf("(%.1f%%)", 100 * mean(df$provisional_topic != "unassigned")), "\n")
cat("Unassigned:              ",
    sum(df$provisional_topic == "unassigned"), "\n")

cat("\nConfidence distribution:\n")
df %>% count(confidence) %>% print()

cat("\nFlagged for manual review:", sum(df$review_flag),
    sprintf("(%.1f%%)", 100 * mean(df$review_flag)), "\n")

cat("\nFlag reasons (speeches can have multiple):\n")
df %>%
  filter(review_flag) %>%
  separate_rows(flag_reason, sep = "; ") %>%
  count(flag_reason, sort = TRUE) %>%
  print()

# -----------------------------------------------------------------------------
# SAVE — main corpus
# -----------------------------------------------------------------------------
cat("\nSaving outputs...\n")

write_csv(df, file.path(OUTPUT_DIR, "corpus_with_topics.csv"))
cat("✓ corpus_with_topics.csv  (full corpus, all classifier fields)\n")

write_csv(topic_dist, file.path(OUTPUT_DIR, "topic_summary.csv"))
cat("✓ topic_summary.csv\n")

df %>%
  count(provisional_topic, party_clean) %>%
  pivot_wider(names_from = party_clean, values_from = n, values_fill = 0) %>%
  write_csv(file.path(OUTPUT_DIR, "topic_by_party.csv"))
cat("✓ topic_by_party.csv\n")

df %>%
  mutate(year = as.integer(year)) %>%
  count(provisional_topic, year) %>%
  pivot_wider(names_from = year, values_from = n, values_fill = 0) %>%
  write_csv(file.path(OUTPUT_DIR, "topic_by_year.csv"))
cat("✓ topic_by_year.csv\n")

# -----------------------------------------------------------------------------
# STAGE 2 — flagged cases for manual review
# -----------------------------------------------------------------------------
flagged <- df %>%
  filter(review_flag) %>%
  mutate(text_preview = substr(text, 1, 500)) %>%
  select(speech_id, date, chamber, party_clean,
         provisional_topic, confidence, flag_reason,
         all_matches, matched_keywords, match_count,
         manual_topic,          # leave blank — reviewer fills this
         text_preview) %>%
  arrange(flag_reason, provisional_topic)

write_csv(flagged, file.path(OUTPUT_DIR, "flagged_for_review.csv"))
cat("✓ flagged_for_review.csv  (", nrow(flagged), " speeches for Stage 2 manual review)\n",
    sep = "")

# -----------------------------------------------------------------------------
# STAGE 3 — validation sample for precision reporting
# Includes: 20 per category (stratified) + 20 unassigned + all multi-match
# (capped at 200 if very large)
# -----------------------------------------------------------------------------
set.seed(42)

# Stratified assigned sample
assigned_sample <- df %>%
  filter(provisional_topic != "unassigned") %>%
  group_by(provisional_topic) %>%
  slice_sample(n = VALIDATION_N_PER_CATEGORY, replace = FALSE) %>%
  ungroup() %>%
  mutate(sample_stratum = "assigned_stratified")

# Unassigned sample
unassigned_sample <- df %>%
  filter(provisional_topic == "unassigned") %>%
  slice_sample(n = min(VALIDATION_N_UNASSIGNED, nrow(.)), replace = FALSE) %>%
  mutate(sample_stratum = "unassigned")

# All multi-match cases (up to 200)
multi_sample <- df %>%
  filter(n_topics_matched > 1) %>%
  slice_sample(n = min(200, nrow(.)), replace = FALSE) %>%
  mutate(sample_stratum = "multi_match")

validation_sample <- bind_rows(assigned_sample, unassigned_sample, multi_sample) %>%
  distinct(speech_id, .keep_all = TRUE) %>%
  mutate(
    text_preview   = substr(text, 1, 400),
    coder_decision = NA_character_    # reviewer fills: correct / incorrect / unclear
  ) %>%
  select(speech_id, date, chamber, party_clean,
         provisional_topic, confidence, flag_reason,
         all_matches, matched_keywords, match_count,
         sample_stratum, coder_decision,
         text_preview) %>%
  arrange(sample_stratum, provisional_topic)

write_csv(validation_sample, file.path(OUTPUT_DIR, "validation_sample.csv"))
cat("✓ validation_sample.csv   (", nrow(validation_sample),
    " speeches for Stage 3 precision check)\n", sep = "")

# -----------------------------------------------------------------------------
# DIAGNOSTIC: priority override cases (useful to inspect before manual review)
# -----------------------------------------------------------------------------
override_cases <- df %>%
  filter(str_detect(flag_reason, "priority override")) %>%
  mutate(text_preview = substr(text, 1, 300)) %>%
  select(speech_id, provisional_topic, confidence, all_matches,
         matched_keywords, match_count, text_preview)

if (nrow(override_cases) > 0) {
  write_csv(override_cases,
            file.path(OUTPUT_DIR, "priority_override_cases.csv"))
  cat("✓ priority_override_cases.csv (", nrow(override_cases),
      " cases where priority overrode match count)\n", sep = "")
}

cat("\n", strrep("=", 60), "\n")
cat("DONE.\n\n")
cat("Next steps:\n")
cat("  1. Open flagged_for_review.csv and fill the manual_topic column.\n")
cat("  2. Re-merge: update corpus_with_topics.csv final_topic column.\n")
cat("  3. Code validation_sample.csv (coder_decision column) for precision reporting.\n")
cat("  4. Report: 'X% of assigned speeches correctly identified the dominant\n")
cat("     activism referent (manual validation, n = Y).'\n")
cat(strrep("=", 60), "\n")

# =============================================================================
# METHODOLOGY NOTE (for thesis write-up)
# =============================================================================
# Topic assignment was conducted through a two-stage hybrid procedure.
# In Stage 1, a rule-based dictionary classifier was applied to all speeches,
# generating provisional topic labels based on keyword matching across 14
# activism categories. Speeches were assigned using a priority-and-count
# heuristic (most specific category first; ties broken by keyword frequency).
# For each speech, all matched topics, matched keywords, match counts, and a
# confidence score were recorded. Speeches were flagged for manual review when
# they exhibited multiple matched categories, only weak keyword evidence,
# priority-level overrides of higher-count matches, or wins by broad categories
# (labour, students, police/security) prone to false positives. In Stage 2,
# flagged speeches were manually reviewed to identify the dominant activism
# referent, producing a final_topic assignment that supersedes the provisional
# label where the reviewer introduced a correction. Stage 3 involved a
# stratified validation sample (20 speeches per category, 20 unassigned, and
# a sample of all multi-match cases) coded by the researcher to estimate
# classifier precision. This hybrid procedure preserves the transparency and
# replicability of dictionary classification while reducing misclassification
# in ambiguous parliamentary speeches.
# =============================================================================
