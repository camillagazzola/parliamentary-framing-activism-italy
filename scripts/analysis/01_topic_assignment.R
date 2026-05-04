#!/usr/bin/env Rscript
# =============================================================================
# 01_topic_assignment.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2025
#
# PURPOSE: Assign each speech to one of 14 activism topics using a
#   dictionary-based classifier with a priority system. Topics are defined
#   by regex keyword patterns. When multiple topics match, the most specific
#   topic wins (lower priority number = more specific).
#
#   Priority 1 — named movements / organisations (most specific)
#   Priority 2 — clear movement categories
#   Priority 3 — broader categories (can overlap)
#
#   Within the same priority level, the topic with the most keyword matches
#   wins. This approach follows dictionary-based classification methods
#   established for political text analysis (Laver, Benoit and Garry 2003;
#   Grimmer and Stewart 2013).
#
# INPUT:  /Users/camillagazzola/Desktop/thesis_test/output/activism_corpus_final.csv
# OUTPUT: /Users/camillagazzola/Desktop/thesis_test/output/corpus_with_topics.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/topic_summary.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/topic_by_party.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/topic_by_year.csv
#         /Users/camillagazzola/Desktop/thesis_test/output/quality_review_sample.csv
#
# Run from anywhere:
#   Rscript /Users/camillagazzola/Desktop/thesis_test/01_topic_assignment.R
# =============================================================================

library(tidyverse)
library(stringr)

# PATHS
INPUT_CSV  <- "/Users/camillagazzola/Desktop/thesis_test/output/activism_corpus_final.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/thesis_test/output"

# TOPIC DEFINITIONS
# Priority: lower = more specific = wins in multi-match
# Keywords use regex patterns (case insensitive)

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

# CLASSIFIER
classify_speech <- function(text, topic_defs) {
  if (is.na(text) || text == "")
    return(list(topic="unassigned", matched_keywords="", match_note="no text"))

  text_lower <- tolower(text)
  matches    <- list()

  for (topic_name in names(topic_defs)) {
    config     <- topic_defs[[topic_name]]
    matched_kw <- c()
    for (pattern in config$keywords) {
      if (str_detect(text_lower, regex(pattern, ignore_case = TRUE))) {
        found      <- str_extract_all(text_lower, regex(pattern, ignore_case = TRUE))[[1]]
        matched_kw <- c(matched_kw, found)
      }
    }
    if (length(matched_kw) > 0)
      matches[[topic_name]] <- list(count=length(matched_kw),
                                    keywords=unique(matched_kw),
                                    priority=config$priority)
  }

  if (length(matches) == 0)
    return(list(topic="unassigned", matched_keywords="", match_note="no keyword matches"))

  if (length(matches) == 1) {
    topic <- names(matches)[1]
    return(list(topic=topic,
                matched_keywords=paste(matches[[topic]]$keywords, collapse=", "),
                match_note="single match"))
  }

  match_df <- tibble(topic=names(matches),
                     priority=sapply(matches, function(x) x$priority),
                     count=sapply(matches, function(x) x$count)) %>%
    arrange(priority, desc(count))

  winner <- match_df$topic[1]
  list(topic=winner,
       matched_keywords=paste(matches[[winner]]$keywords, collapse=", "),
       match_note=paste0("multi-match: ", paste(match_df$topic, collapse=", ")))
}

# LOAD
cat("Loading corpus...\n")
df <- read_csv(INPUT_CSV, show_col_types = FALSE)
cat("Speeches:", nrow(df), "\n")
cat("Parties: ", paste(sort(unique(df$party_clean)), collapse=", "), "\n\n")

# CLASSIFY
cat("Classifying speeches...\n")
results <- lapply(df$text, function(txt) classify_speech(txt, topic_definitions))
df$topic            <- sapply(results, function(x) x$topic)
df$matched_keywords <- sapply(results, function(x) x$matched_keywords)
df$match_note       <- sapply(results, function(x) x$match_note)

# SUMMARY
cat("\n", strrep("=",60), "\nTOPIC DISTRIBUTION\n", strrep("=",60), "\n\n")
topic_dist <- df %>% count(topic, name="n") %>%
  mutate(pct=round(100*n/nrow(df),1)) %>% arrange(desc(n))
print(topic_dist, n=20)
cat("\nAssigned:  ", sum(df$topic!="unassigned"),
    sprintf("(%.1f%%)", 100*mean(df$topic!="unassigned")), "\n")
cat("Unassigned:", sum(df$topic=="unassigned"), "\n")
cat("\nMatch types:\n")
df %>% mutate(match_type=case_when(
  str_detect(match_note,"single match")~"single match",
  str_detect(match_note,"multi-match")~"multi-match",
  TRUE~match_note)) %>% count(match_type) %>% print()

# SAVE
cat("\nSaving outputs...\n")
write_csv(df, file.path(OUTPUT_DIR,"corpus_with_topics.csv"))
cat("✓ corpus_with_topics.csv\n")
write_csv(topic_dist, file.path(OUTPUT_DIR,"topic_summary.csv"))
cat("✓ topic_summary.csv\n")
df %>% count(topic,party_clean) %>%
  pivot_wider(names_from=party_clean,values_from=n,values_fill=0) %>%
  write_csv(file.path(OUTPUT_DIR,"topic_by_party.csv"))
cat("✓ topic_by_party.csv\n")
df %>% mutate(year=as.integer(year)) %>% count(topic,year) %>%
  pivot_wider(names_from=year,values_from=n,values_fill=0) %>%
  write_csv(file.path(OUTPUT_DIR,"topic_by_year.csv"))
cat("✓ topic_by_year.csv\n")
set.seed(42)
df %>% filter(topic!="unassigned") %>%
  group_by(topic) %>% slice_sample(n=10,replace=FALSE) %>% ungroup() %>%
  mutate(text_preview=substr(text,1,300)) %>%
  select(speech_id,date,chamber,party_clean,topic,matched_keywords,match_note,text_preview) %>%
  arrange(topic) %>%
  write_csv(file.path(OUTPUT_DIR,"quality_review_sample.csv"))
cat("✓ quality_review_sample.csv\n")
cat("\nDone.\n")
