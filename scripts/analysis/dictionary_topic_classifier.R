# ==============================================================================
# DICTIONARY-BASED TOPIC CLASSIFIER FOR ITALIAN PARLIAMENTARY ACTIVISM CORPUS
# ==============================================================================
#
# Simple, transparent, reliable approach:
# 1. Check each speech for topic keywords
# 2. Assign based on matches (with priority for specific topics)
# 3. Multi-match speeches get most specific topic
# 4. No-match speeches go to "other" for manual review
#
# ==============================================================================

library(tidyverse)
library(stringr)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

CORPUS_PATH <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/activism_corpus_v11_clean.csv"
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/dictionary_topics/"

dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

# ==============================================================================
# TOPIC DICTIONARIES
# ==============================================================================

# Priority: lower number = more specific = wins in multi-match
# Keywords use regex patterns (case insensitive)

topic_definitions <- list(
  
  # VERY SPECIFIC (priority 1) - named movements/organizations
  no_tav = list(
    priority = 1,
    keywords = c("no.?tav", "notav", "val.?susa", "valsusa", "chiomonte", "no.?tap", "notap")
  ),
  
  climate_activists = list(
    priority = 1,
    keywords = c("ultima.generazione", "extinction.rebellion", "fridays.for.future",
                 "ecoattivisti", "eco.?vandal", "imbrattato", "imbrattare",
                 "blocco.stradale", "blocchi.stradali")
  ),
  
  pro_palestine = list(
    priority = 1,
    keywords = c("palestina", "palestinese", "palestinesi", "\\bgaza\\b", 
                 "\\bhamas\\b", "intifada", "nakba", "\\bsionista\\b", "\\bsionisti\\b", "\\bsionismo\\b")
  ),
  
  no_vax = list(
    priority = 1,
    keywords = c("no.?vax", "novax", "green.?pass", "obbligo.vaccinale", "dittatura.sanitaria")
  ),
  
  lgbtq = list(
    priority = 1,
    keywords = c("\\blgbt", "\\blgbtq", "\\bglbt", "\\bglbtq", "omofobia", "transfobia", 
                 "omotransfobia", "ddl.zan", "\\bpride\\b", "unioni.civili", "omosessual")
  ),
  
  antisemitism = list(
    priority = 1,
    keywords = c("antisemit", "\\bshoah\\b", "\\bsegre\\b", "\\bebrei\\b", "\\bebreo\\b",
                 "\\bebraica\\b", "\\bebraismo\\b", "stella.di.david", "sinagog",
                 "giornata.della.memoria", "deportazione.ebrei")
  ),
  
  # SPECIFIC (priority 2) - clear movement categories
  far_right = list(
    priority = 2,
    keywords = c("casapound", "forza.nuova", "neofascist", "estrema.destra",
                 "saluto.romano", "squadrist", "squadrismo", "\\bcamerata\\b")
  ),
  
  antifascist = list(
    priority = 2,
    keywords = c("antifascist", "antifascismo", "\\banpi\\b", "partigian",
                 "25.aprile", "venticinque.aprile")
  ),
  
  far_left = list(
    priority = 2,
    keywords = c("centri.sociali", "centro.sociale", "black.bloc", 
                 "anarch", "antagonist", "\\bautonomi\\b", "\\bsquat\\b")
  ),
  
  migrants = list(
    priority = 2,
    keywords = c("migranti", "immigrat", "rifugiat", "profugh", "richiedenti.asilo",
                 "sbarchi", "sbarco", "\\bong\\b", "sea.watch", "open.arms",
                 "mediterranea", "clandestin", "accoglienza", "\\bcpr\\b", "\\bcie\\b",
                 "hotspot", "respingiment", "decreto.salvini", "decreti.salvini")
  ),
  
  prisoners_rights = list(
    priority = 2,
    keywords = c("\\bcarcere\\b", "\\bcarceri\\b", "\\bdetenu", "penitenziario", 
                 "penitenziari", "sovraffollamento", "41.bis", "ergastolo.ostativo",
                 "\\bcelle\\b", "rivolt.+carcer")
  ),
  
  feminist = list(
    priority = 2,
    keywords = c("femminism", "femminista", "femministe", "non.una.di.meno",
                 "8.marzo", "otto.marzo", "femminicidio", "femminicidi", "patriarcato")
  ),
  
  # BROADER (priority 3) - could overlap with others
  students = list(
    priority = 3,
    keywords = c("\\bstudenti\\b", "\\bstudentesse\\b", "\\buniversitari\\b",
                 "movimento.studentesco", "\\bliceo\\b", "\\blicei\\b", 
                 "occupazion.+student", "\\bcollettiv")
  ),
  
  labor = list(
    priority = 3,
    keywords = c("\\bcgil\\b", "\\bcisl\\b", "\\buil\\b", "sindacat", 
                 "scioper", "lavoratori", "lavoratrici", "\\boperai\\b", "\\boperaio\\b",
                 "fabbric", "licenziament", "disoccupat", "\\bprecar", "vertenz")
  ),
  
  police_security = list(
    priority = 3,
    keywords = c("forze.dell.ordine", "\\bpolizia\\b", "\\bcarabinieri\\b", 
                 "\\bagenti\\b", "\\bdivisa\\b", "\\bquestura\\b", "\\bquesture\\b",
                 "polizia.penitenziaria", "pubblica.sicurezza")
  )
)

# ==============================================================================
# CLASSIFIER FUNCTION
# ==============================================================================

classify_speech <- function(text, topic_defs) {
  
  if (is.na(text) || text == "") {
    return(list(topic = "other_no_text", keywords = "", note = "no text"))
  }
  
  text_lower <- tolower(text)
  matches <- list()
  
  for (topic_name in names(topic_defs)) {
    config <- topic_defs[[topic_name]]
    matched_kw <- c()
    
    for (pattern in config$keywords) {
      if (str_detect(text_lower, regex(pattern, ignore_case = TRUE))) {
        # Extract what matched
        found <- str_extract_all(text_lower, regex(pattern, ignore_case = TRUE))[[1]]
        matched_kw <- c(matched_kw, found)
      }
    }
    
    if (length(matched_kw) > 0) {
      matches[[topic_name]] <- list(
        count = length(matched_kw),
        keywords = unique(matched_kw),
        priority = config$priority
      )
    }
  }
  
  # No matches
  if (length(matches) == 0) {
    return(list(topic = "other_manual_review", keywords = "", note = "no keyword matches"))
  }
  
  # Single match
  if (length(matches) == 1) {
    topic <- names(matches)[1]
    return(list(
      topic = topic, 
      keywords = paste(matches[[topic]]$keywords, collapse = ", "),
      note = "single match"
    ))
  }
  
  # Multiple matches - sort by priority (lower wins), then by count (higher wins)
  match_df <- tibble(
    topic = names(matches),
    priority = sapply(matches, function(x) x$priority),
    count = sapply(matches, function(x) x$count)
  ) %>%
    arrange(priority, desc(count))
  
  winner <- match_df$topic[1]
  all_topics <- paste(match_df$topic, collapse = ", ")
  
  return(list(
    topic = winner,
    keywords = paste(matches[[winner]]$keywords, collapse = ", "),
    note = paste0("multi-match: ", all_topics)
  ))
}

# ==============================================================================
# MAIN
# ==============================================================================

cat(strrep("=", 60), "\n")
cat("DICTIONARY-BASED TOPIC CLASSIFIER\n")
cat(strrep("=", 60), "\n\n")

# Load corpus
cat("Loading corpus...\n")
corpus_df <- read_csv(CORPUS_PATH, show_col_types = FALSE)
cat("Loaded", nrow(corpus_df), "speeches\n")

# Use text_compounds if available
text_col <- if ("text_compounds" %in% names(corpus_df)) "text_compounds" else "text"
cat("Using column:", text_col, "\n\n")

# Classify each speech
cat("Classifying speeches...\n")

results <- lapply(corpus_df[[text_col]], function(txt) {
  classify_speech(txt, topic_definitions)
})

corpus_df$topic <- sapply(results, function(x) x$topic)
corpus_df$matched_keywords <- sapply(results, function(x) x$keywords)
corpus_df$match_note <- sapply(results, function(x) x$note)

# Summary
cat("\n")
cat(strrep("=", 60), "\n")
cat("TOPIC DISTRIBUTION\n")
cat(strrep("=", 60), "\n\n")

topic_counts <- corpus_df %>%
  count(topic) %>%
  arrange(desc(n)) %>%
  mutate(pct = round(n / sum(n) * 100, 1))

for (i in 1:nrow(topic_counts)) {
  cat(sprintf("%-25s %4d  (%5.1f%%)\n", 
              topic_counts$topic[i], 
              topic_counts$n[i],
              topic_counts$pct[i]))
}

# Match types
cat("\n")
cat(strrep("=", 60), "\n")
cat("MATCH TYPES\n")
cat(strrep("=", 60), "\n\n")

match_types <- corpus_df %>%
  mutate(match_type = case_when(
    str_detect(match_note, "single match") ~ "single match",
    str_detect(match_note, "multi-match") ~ "multi-match",
    TRUE ~ match_note
  )) %>%
  count(match_type)

print(match_types)

# ==============================================================================
# SAVE OUTPUTS
# ==============================================================================

cat("\n")
cat(strrep("=", 60), "\n")
cat("SAVING OUTPUTS\n")
cat(strrep("=", 60), "\n\n")

# Full corpus with topics
output_path <- file.path(OUTPUT_DIR, "corpus_with_dictionary_topics.csv")
write_csv(corpus_df, output_path)
cat("✓ Saved:", output_path, "\n")

# Manual review file
other_df <- corpus_df %>%
  filter(topic == "other_manual_review") %>%
  select(speech_id, year, party, chamber, topic, match_note, all_of(text_col)) %>%
  mutate(
    manual_label = "",
    text_preview = str_sub(.data[[text_col]], 1, 500)
  )

review_path <- file.path(OUTPUT_DIR, "other_for_manual_review.csv")
write_csv(other_df, review_path)
cat("✓ Saved:", review_path, "\n")
cat("  →", nrow(other_df), "speeches for manual review\n")

# Topic by party crosstab
topic_party <- corpus_df %>%
  count(topic, party) %>%
  pivot_wider(names_from = party, values_from = n, values_fill = 0)

crosstab_path <- file.path(OUTPUT_DIR, "topic_by_party.csv")
write_csv(topic_party, crosstab_path)
cat("✓ Saved:", crosstab_path, "\n")

# Topic by year crosstab
topic_year <- corpus_df %>%
  count(topic, year) %>%
  pivot_wider(names_from = year, values_from = n, values_fill = 0)

crosstab_year_path <- file.path(OUTPUT_DIR, "topic_by_year.csv")
write_csv(topic_year, crosstab_year_path)
cat("✓ Saved:", crosstab_year_path, "\n")

cat("\n")
cat(strrep("=", 60), "\n")
cat("DONE!\n")
cat(strrep("=", 60), "\n")