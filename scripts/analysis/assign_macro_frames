#!/usr/bin/env Rscript
# ==============================================================================
# MACRO FRAME ASSIGNMENT AND TEMPORAL ANALYSIS
# ==============================================================================
#
# This script:
# 1. Defines the 6 macro frames from theory (Section 3.2)
# 2. Creates frame dictionaries with indicative lemmas
# 3. Assigns frames to each speech (allowing mixed frames)
# 4. Tracks frame changes over time
# 5. Outputs visualisation-ready data
#
# ==============================================================================

library(tidyverse)
library(udpipe)

# ==============================================================================
# PATHS - UPDATE THESE
# ==============================================================================

# Try different possible corpus paths
CORPUS_PATHS <- c(
  "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/keyword_window_analysis/corpus_with_window_analysis.csv",
  "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/processed/activism_corpus_v11_clean.csv",
  "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/corpus_with_frames.csv"
)

CORPUS_PATH <- NULL
for (path in CORPUS_PATHS) {
  if (file.exists(path)) {
    CORPUS_PATH <- path
    break
  }
}

if (is.null(CORPUS_PATH)) {
  stop("No corpus file found. Tried:\n", paste(CORPUS_PATHS, collapse = "\n"))
}
OUTPUT_DIR <- "/Users/camillagazzola/Desktop/git-thesis/italian-parliament-protest-framing/data/frame_analysis/"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

# ==============================================================================
# 1. MACRO FRAME DEFINITIONS (from Theory Section 3.2)
# ==============================================================================

# Each frame has:
# - Core indicative lemmas (Italian)
# - Secondary/contextual lemmas
# - Typical party associations

macro_frames <- list(
  
  security = list(
    name = "Security",
    description = "Elevates activism to existential threat; grammar of security (Buzan et al. 1998)",
    core_lemmas = c("sicurezza", "minaccia", "pericolo", "ordine", "pubblico", 
                    "emergenza", "allarme", "rischio", "terrorismo", "terrorista",
                    "estremismo", "estremista", "radicalizzazione"),
    secondary_lemmas = c("sorveglianza", "controllo", "prevenzione", "infiltrazione",
                         "cellula", "rete", "organizzazione", "criminale"),
    typical_parties = c("FDI", "LEGA", "FI")
  ),
  
  legality = list(
    name = "Legality",
    description = "Evaluates through legal validity; can legitimise or contest (Lim 2013)",
    core_lemmas = c("legge", "decreto", "reato", "norma", "illegale", "illecito",
                    "costituzione", "costituzionale", "incostituzionale", "diritto",
                    "giuridico", "penale", "sanzione", "multa", "condanna"),
    secondary_lemmas = c("tribunale", "giudice", "sentenza", "codice", "articolo",
                         "comma", "violazione", "infrazione", "denuncia"),
    typical_parties = c("all") # used across spectrum
  ),
  
  morality = list(
    name = "Morality",
    description = "Evaluates through fundamental values and right/wrong (Rozin 1999)",
    core_lemmas = c("responsabilità", "dovere", "valore", "valori", "etica", "etico",
                    "morale", "giusto", "sbagliato", "vergogna", "dignità",
                    "onore", "rispetto", "civiltà", "incivile"),
    secondary_lemmas = c("coscienza", "principio", "virtù", "integrità", "tradizione",
                         "famiglia", "educazione", "esempio"),
    typical_parties = c("all")
  ),
  
  national_identity = list(
    name = "National Identity",
    description = "Constructs national/non-national dichotomy; othering (Caiani & della Porta 2012)",
    core_lemmas = c("italia", "italiano", "italiani", "nazione", "nazionale", 
                    "patria", "patriota", "patriottico", "identità", "sovranità",
                    "popolo", "cittadino", "straniero", "nemico"),
    secondary_lemmas = c("bandiera", "tricolore", "confine", "territorio", "radice",
                         "tradizione", "cultura", "appartenenza", "comunità"),
    typical_parties = c("FDI", "LEGA")
  ),
  
  humanitarianism = list(
    name = "Humanitarianism",
    description = "Deploys moral sentiments; suffering body and compassion (Fassin 2011)",
    core_lemmas = c("umano", "umanità", "umanitario", "diritti", "solidarietà",
                    "accoglienza", "dignità", "sofferenza", "vittima", "vittime",
                    "tragedia", "tragico", "disperazione", "disperato"),
    secondary_lemmas = c("compassione", "aiuto", "soccorso", "salvataggio", "vulnerabile",
                         "bambino", "bambini", "donna", "donne", "famiglia", "madre",
                         "rifugiato", "profugo", "migrante"),
    typical_parties = c("AVS", "PD", "M5S", "LEU", "+EUROPA")
  ),
  
  delegitimisation = list(
    name = "Delegitimisation",
    description = "Severs link to shared values; labels as irrational/violent (Beetham 1991)",
    core_lemmas = c("violenza", "violento", "vandalismo", "vandalo", "teppista",
                    "ideologia", "ideologico", "estremista", "fanatismo", "fanatico",
                    "follia", "folle", "irresponsabile", "strumentalizzazione"),
    secondary_lemmas = c("provocazione", "provocatore", "infiltrato", "black bloc",
                         "anarchico", "sovversivo", "delinquente", "criminale",
                         "distruzione", "devastazione", "danneggiamento", "imbrattare"),
    typical_parties = c("FDI", "LEGA", "FI")
  )
)

# ==============================================================================
# 2. TOPIC-SPECIFIC FRAME MODIFIERS
# ==============================================================================

# Additional lemmas that indicate frame application within specific topics
# Format: "main_frame:modifier"

topic_modifiers <- list(
  
  climate_activists = list(
    security = c("eco-terrorismo", "eco-terrorista", "blocco", "bloccare"),
    delegitimisation = c("imbrattare", "deturpare", "patrimonio", "bene culturale",
                         "monumento", "opera", "vernice", "muro", "parete"),
    humanitarianism = c("clima", "climatico", "emergenza climatica", "futuro",
                        "generazione", "pianeta", "ambiente"),
    morality = c("civile", "disobbedienza", "resistenza", "lotta")
  ),
  
  migrants = list(
    security = c("clandestino", "irregolare", "sbarco", "scafista", "trafficante",
                 "frontiera", "hotspot", "espulsione"),
    humanitarianism = c("naufragio", "annegamento", "mediterraneo", "mare", "barcone",
                        "salvataggio", "ong", "soccorso", "cpr", "rimpatrio",
                        "deportazione", "trattenimento"),
    national_identity = c("invasione", "sostituzione", "islamizzazione")
  ),
  
  pro_palestine = list(
    humanitarianism = c("gaza", "palestinese", "civile", "massacro", "bombardamento",
                        "genocidio", "sterminio", "ospedale", "bambino"),
    delegitimisation = c("antisemita", "antisemitismo", "hamas", "terrorista",
                         "coro", "slogan", "aggressione", "assalto"),
    security = c("terrorismo", "razzi", "attacco")
  ),
  
  police_security = list(
    humanitarianism = c("bodycam", "identificativo", "codice", "riconoscimento",
                        "abuso", "pestaggio", "tortura", "violenza polizia"),
    morality = c("divisa", "uniforme", "servizio", "onore", "sacrificio",
                 "tutela", "protezione", "ordine"),
    legality = c("querela", "denuncia", "indagine", "processo")
  ),
  
  prisoners_rights = list(
    humanitarianism = c("sovraffollamento", "suicidio", "carcere", "detenuto",
                        "condizione", "cella", "41bis", "ergastolo", "tortura"),
    security = c("rivolta", "evasione", "sommossa", "disordine", "incendio",
                 "sequestro", "ostaggio"),
    delegitimisation = c("mafioso", "camorrista", "boss", "criminale organizzato")
  ),
  
  far_left = list(
    security = c("centro sociale", "anarchico", "autonomo", "antifa", "black bloc"),
    delegitimisation = c("estremista", "violento", "sovversivo", "rivoluzionario")
  ),
  
  far_right = list(
    security = c("neofascista", "neonazista", "casapound", "forza nuova",
                 "squadrista", "razzista"),
    delegitimisation = c("nostalgico", "estremista", "violento")
  ),
  
  students = list(
    humanitarianism = c("giovane", "futuro", "istruzione", "università", "scuola"),
    delegitimisation = c("occupazione", "occupante", "barricata")
  ),
  
  labor = list(
    humanitarianism = c("lavoratore", "lavoratrice", "precario", "sfruttamento",
                        "salario", "stipendio", "licenziamento"),
    legality = c("sciopero", "sindacato", "contratto", "diritto")
  )
)

# ==============================================================================
# 3. LOAD AND PREPARE CORPUS
# ==============================================================================

cat("Loading corpus from:", CORPUS_PATH, "\n")
corpus <- read_csv(CORPUS_PATH, show_col_types = FALSE)

cat("Corpus loaded:", nrow(corpus), "speeches\n")
cat("Columns:", paste(names(corpus), collapse = ", "), "\n")

# Check if topic column exists, if not we need to assign topics
if (!"topic" %in% names(corpus)) {
  cat("\nWARNING: 'topic' column not found. Assigning topics using keyword matching...\n")
  
  # Topic keywords (from your previous work)
  topic_keywords <- list(
    climate_activists = c("clima", "climatico", "ambientalista", "ecologista", "ultima generazione",
                          "extinction rebellion", "fridays for future", "greta", "eco-vandal",
                          "imbrattare", "vernice", "blocco stradale", "attivisti clima"),
    migrants = c("migrante", "migranti", "immigrato", "immigrazione", "sbarco", "sbarchi",
                 "clandestino", "rifugiato", "profugo", "ong", "frontex", "hotspot", "cpr",
                 "rimpatrio", "accoglienza", "sea watch", "mediterraneo", "salvini"),
    prisoners_rights = c("carcere", "carceri", "detenuto", "detenuti", "penitenziario",
                         "ergastolo", "41bis", "41-bis", "sovraffollamento", "suicidio carcere",
                         "rivolta carcere", "istituto penitenziario"),
    police_security = c("polizia", "carabinieri", "forze ordine", "celere", "manganello",
                        "bodycam", "identificativo", "divisa", "agente", "questore"),
    pro_palestine = c("palestina", "palestinese", "gaza", "cisgiordania", "intifada",
                      "free palestine", "genocidio gaza", "boicottaggio israele"),
    far_right = c("fascismo", "neofascismo", "casapound", "forza nuova", "skinhead",
                  "neonazi", "estrema destra", "squadrismo"),
    far_left = c("centro sociale", "centri sociali", "autonomo", "autonomi", "anarchico",
                 "antifa", "estrema sinistra", "black bloc"),
    labor = c("sciopero", "scioperare", "sindacato", "lavoratore", "lavoratori",
              "precario", "licenziamento", "cgil", "cisl", "uil"),
    students = c("studente", "studenti", "universitario", "occupazione facoltà",
                 "corteo studentesco", "movimento studentesco"),
    lgbtq = c("lgbt", "lgbtq", "gay", "pride", "omofobia", "transfobia",
              "ddl zan", "unioni civili"),
    no_vax = c("no vax", "novax", "vaccino obbligatorio", "green pass", "obbligo vaccinale",
               "libertà vaccinale"),
    antifascist = c("antifascismo", "antifascista", "25 aprile", "resistenza", "partigiano",
                    "anpi", "bella ciao"),
    antisemitism = c("antisemitismo", "antisemita", "shoah", "olocausto", "stella david",
                     "sinagoga", "comunità ebraica"),
    no_tav = c("no tav", "notav", "val susa", "tav torino", "alta velocità")
  )
  
  # Function to assign topic based on keyword matching in text
  assign_topic <- function(text) {
    text_lower <- tolower(text)
    
    scores <- sapply(names(topic_keywords), function(topic) {
      sum(sapply(topic_keywords[[topic]], function(kw) {
        str_count(text_lower, regex(paste0("\\b", kw, "\\b"), ignore_case = TRUE))
      }))
    })
    
    if (max(scores) == 0) {
      return(NA_character_)
    } else {
      return(names(which.max(scores)))
    }
  }
  
  corpus <- corpus %>%
    rowwise() %>%
    mutate(topic = assign_topic(text)) %>%
    ungroup()
  
  topic_counts <- corpus %>% count(topic, sort = TRUE)
  cat("\nTopic distribution:\n")
  print(topic_counts)
}

# Ensure we have required columns
required_cols <- c("text", "party")
missing_cols <- setdiff(required_cols, names(corpus))
if (length(missing_cols) > 0) {
  stop("Missing required columns: ", paste(missing_cols, collapse = ", "))
}

# Create year column if missing
if (!"year" %in% names(corpus) && "date" %in% names(corpus)) {
  corpus <- corpus %>%
    mutate(year = as.numeric(substr(date, 1, 4)))
}

# ==============================================================================
# 4. FRAME SCORING FUNCTION
# ==============================================================================

score_frames <- function(text, topic = NA) {
  # Lowercase text for matching
  text_lower <- tolower(text)
  
  # Score each macro frame
  scores <- sapply(names(macro_frames), function(frame_name) {
    frame <- macro_frames[[frame_name]]
    
    # Count core lemma matches (weight = 2)
    core_matches <- sum(sapply(frame$core_lemmas, function(lemma) {
      str_count(text_lower, regex(paste0("\\b", lemma, "\\w*\\b"), ignore_case = TRUE))
    }))
    
    # Count secondary lemma matches (weight = 1)
    secondary_matches <- sum(sapply(frame$secondary_lemmas, function(lemma) {
      str_count(text_lower, regex(paste0("\\b", lemma, "\\w*\\b"), ignore_case = TRUE))
    }))
    
    # Add topic-specific modifiers if topic is known
    topic_bonus <- 0
    if (!is.na(topic) && topic %in% names(topic_modifiers)) {
      topic_mods <- topic_modifiers[[topic]]
      if (frame_name %in% names(topic_mods)) {
        topic_bonus <- sum(sapply(topic_mods[[frame_name]], function(lemma) {
          str_count(text_lower, regex(paste0("\\b", lemma, "\\w*\\b"), ignore_case = TRUE))
        })) * 1.5  # topic-specific matches weighted 1.5
      }
    }
    
    return(core_matches * 2 + secondary_matches + topic_bonus)
  })
  
  return(scores)
}

# ==============================================================================
# 5. ASSIGN FRAMES TO EACH SPEECH
# ==============================================================================

cat("Assigning frames to speeches...\n")

# Apply frame scoring to each speech
frame_scores <- corpus %>%
  rowwise() %>%
  mutate(
    scores = list(score_frames(text, topic))
  ) %>%
  ungroup()

# Extract scores into columns
frame_names <- names(macro_frames)
for (fn in frame_names) {
  frame_scores[[paste0("score_", fn)]] <- sapply(frame_scores$scores, function(s) s[[fn]])
}

# Determine primary frame (highest score)
frame_scores <- frame_scores %>%
  rowwise() %>%
  mutate(
    max_score = max(c_across(starts_with("score_"))),
    primary_frame = if (max_score == 0) {
      NA_character_
    } else {
      frame_names[which.max(c_across(starts_with("score_")))]
    }
  ) %>%
  ungroup()

# Determine secondary frame (second highest, if > 0 and > 50% of primary)
frame_scores <- frame_scores %>%
  rowwise() %>%
  mutate(
    secondary_frame = {
      scores_vec <- c_across(starts_with("score_"))
      names(scores_vec) <- frame_names
      scores_sorted <- sort(scores_vec, decreasing = TRUE)
      
      if (length(scores_sorted) >= 2 && 
          scores_sorted[2] > 0 && 
          scores_sorted[2] >= scores_sorted[1] * 0.5) {
        names(scores_sorted)[2]
      } else {
        NA_character_
      }
    }
  ) %>%
  ungroup()

# Create combined frame label
frame_scores <- frame_scores %>%
  mutate(
    frame_combined = case_when(
      is.na(primary_frame) ~ "unclassified",
      is.na(secondary_frame) ~ primary_frame,
      TRUE ~ paste0(primary_frame, " + ", secondary_frame)
    )
  )

# Add topic-specific modifier where relevant
frame_scores <- frame_scores %>%
  mutate(
    frame_label = case_when(
      is.na(primary_frame) ~ "unclassified",
      # Add topic context for certain high-scoring combinations
      topic == "climate_activists" & primary_frame == "delegitimisation" ~ "delegitimisation: vandalism",
      topic == "climate_activists" & primary_frame == "security" ~ "security: eco-terrorism",
      topic == "migrants" & primary_frame == "security" ~ "security: borders",
      topic == "migrants" & primary_frame == "humanitarianism" ~ "humanitarianism: dignity",
      topic == "pro_palestine" & primary_frame == "delegitimisation" ~ "delegitimisation: antisemitism",
      topic == "prisoners_rights" & primary_frame == "security" ~ "security: riots",
      topic == "prisoners_rights" & primary_frame == "humanitarianism" ~ "humanitarianism: conditions",
      topic == "police_security" & primary_frame == "morality" ~ "morality: honour",
      topic == "police_security" & primary_frame == "humanitarianism" ~ "humanitarianism: accountability",
      topic == "far_left" & primary_frame == "security" ~ "security: centri sociali",
      TRUE ~ primary_frame
    )
  )

# ==============================================================================
# 6. SUMMARY STATISTICS
# ==============================================================================

cat("\n", strrep("=", 60), "\n")
cat("FRAME ASSIGNMENT SUMMARY\n")
cat(strrep("=", 60), "\n\n")

# Overall frame distribution
cat("Primary Frame Distribution:\n")
frame_scores %>%
  count(primary_frame, sort = TRUE) %>%
  mutate(pct = round(n / sum(n) * 100, 1)) %>%
  print()

cat("\nCombined Frame Distribution (top 15):\n")
frame_scores %>%
  count(frame_combined, sort = TRUE) %>%
  head(15) %>%
  mutate(pct = round(n / sum(n) * 100, 1)) %>%
  print()

cat("\nFrame by Party:\n")
frame_scores %>%
  filter(!is.na(primary_frame)) %>%
  count(party, primary_frame) %>%
  pivot_wider(names_from = primary_frame, values_from = n, values_fill = 0) %>%
  print()

cat("\nFrame by Topic (top 10 topics):\n")
top_topics <- frame_scores %>%
  count(topic, sort = TRUE) %>%
  head(10) %>%
  pull(topic)

frame_scores %>%
  filter(topic %in% top_topics, !is.na(primary_frame)) %>%
  count(topic, primary_frame) %>%
  pivot_wider(names_from = primary_frame, values_from = n, values_fill = 0) %>%
  print()

# ==============================================================================
# 7. TEMPORAL ANALYSIS
# ==============================================================================

cat("\n", strrep("=", 60), "\n")
cat("TEMPORAL FRAME ANALYSIS\n")
cat(strrep("=", 60), "\n\n")

# Frame distribution by year
frame_by_year <- frame_scores %>%
  filter(!is.na(primary_frame)) %>%
  count(year, primary_frame) %>%
  group_by(year) %>%
  mutate(
    total = sum(n),
    pct = round(n / total * 100, 1)
  ) %>%
  ungroup()

cat("Frame Distribution by Year:\n")
frame_by_year %>%
  select(year, primary_frame, n, pct) %>%
  pivot_wider(names_from = primary_frame, values_from = c(n, pct), values_fill = 0) %>%
  print()

# Frame by year and party (for major parties)
major_parties <- c("FDI", "LEGA", "FI", "PD", "M5S", "AVS")

frame_by_year_party <- frame_scores %>%
  filter(!is.na(primary_frame), party %in% major_parties) %>%
  count(year, party, primary_frame) %>%
  group_by(year, party) %>%
  mutate(pct = round(n / sum(n) * 100, 1)) %>%
  ungroup()

# ==============================================================================
# 8. LEGISLATIVE MILESTONE ANALYSIS
# ==============================================================================

# Define legislative milestones
milestones <- tribble(
  ~year, ~event, ~description,
  2018, "Decreti Salvini", "Migration security decrees",
  2022, "Rave Decree", "Anti-gathering legislation",
  2024, "Eco-vandali", "Climate activist criminalization",
  2025, "DDL Sicurezza", "Comprehensive security decree"
)

cat("\nFrame Distribution Around Legislative Milestones:\n")
for (i in 1:nrow(milestones)) {
  ms <- milestones[i, ]
  cat("\n---", ms$year, ms$event, "---\n")
  
  frame_scores %>%
    filter(year == ms$year, !is.na(primary_frame)) %>%
    count(primary_frame, sort = TRUE) %>%
    mutate(pct = round(n / sum(n) * 100, 1)) %>%
    print()
}

# ==============================================================================
# 9. SAVE OUTPUTS
# ==============================================================================

# Main corpus with frame assignments
output_corpus <- frame_scores %>%
  select(-scores) %>%
  select(
    # Original columns
    any_of(c("speech_id", "text", "party", "year", "date", "chamber", "topic")),
    # Frame scores
    starts_with("score_"),
    # Frame assignments
    primary_frame, secondary_frame, frame_combined, frame_label,
    max_score,
    # Everything else
    everything()
  )

write_csv(output_corpus, file.path(OUTPUT_DIR, "corpus_with_macro_frames.csv"))
cat("\n✓ corpus_with_macro_frames.csv\n")

# Frame by year (for temporal visualization)
write_csv(frame_by_year, file.path(OUTPUT_DIR, "frames_by_year.csv"))
cat("✓ frames_by_year.csv\n")

# Frame by year and party
write_csv(frame_by_year_party, file.path(OUTPUT_DIR, "frames_by_year_party.csv"))
cat("✓ frames_by_year_party.csv\n")

# Frame by topic
frame_by_topic <- frame_scores %>%
  filter(!is.na(primary_frame), !is.na(topic)) %>%
  count(topic, primary_frame) %>%
  group_by(topic) %>%
  mutate(pct = round(n / sum(n) * 100, 1)) %>%
  ungroup()

write_csv(frame_by_topic, file.path(OUTPUT_DIR, "frames_by_topic.csv"))
cat("✓ frames_by_topic.csv\n")

# Frame by topic and party
frame_by_topic_party <- frame_scores %>%
  filter(!is.na(primary_frame), !is.na(topic), party %in% major_parties) %>%
  count(topic, party, primary_frame) %>%
  group_by(topic, party) %>%
  mutate(pct = round(n / sum(n) * 100, 1)) %>%
  ungroup()

write_csv(frame_by_topic_party, file.path(OUTPUT_DIR, "frames_by_topic_party.csv"))
cat("✓ frames_by_topic_party.csv\n")

# Summary table for thesis
frame_summary <- frame_scores %>%
  filter(!is.na(primary_frame)) %>%
  group_by(topic, party) %>%
  summarise(
    n_speeches = n(),
    dominant_frame = names(which.max(table(primary_frame))),
    security_pct = round(mean(primary_frame == "security") * 100, 1),
    humanitarianism_pct = round(mean(primary_frame == "humanitarianism") * 100, 1),
    delegitimisation_pct = round(mean(primary_frame == "delegitimisation") * 100, 1),
    legality_pct = round(mean(primary_frame == "legality") * 100, 1),
    morality_pct = round(mean(primary_frame == "morality") * 100, 1),
    national_identity_pct = round(mean(primary_frame == "national_identity") * 100, 1),
    .groups = "drop"
  ) %>%
  filter(n_speeches >= 5) # Only include cells with sufficient data

write_csv(frame_summary, file.path(OUTPUT_DIR, "frame_summary_topic_party.csv"))
cat("✓ frame_summary_topic_party.csv\n")

# ==============================================================================
# 10. DATAWRAPPER-READY OUTPUTS
# ==============================================================================

# Temporal heatmap: frame × year
temporal_heatmap <- frame_by_year %>%
  select(year, primary_frame, pct) %>%
  pivot_wider(names_from = year, values_from = pct, values_fill = 0)

write_csv(temporal_heatmap, file.path(OUTPUT_DIR, "datawrapper_frames_temporal.csv"))
cat("✓ datawrapper_frames_temporal.csv\n")

# Party × frame heatmap
party_frame_heatmap <- frame_scores %>%
  filter(!is.na(primary_frame), party %in% major_parties) %>%
  count(party, primary_frame) %>%
  group_by(party) %>%
  mutate(pct = round(n / sum(n) * 100, 1)) %>%
  select(-n) %>%
  pivot_wider(names_from = primary_frame, values_from = pct, values_fill = 0)

write_csv(party_frame_heatmap, file.path(OUTPUT_DIR, "datawrapper_party_frames.csv"))
cat("✓ datawrapper_party_frames.csv\n")

# Topic × frame heatmap
topic_frame_heatmap <- frame_by_topic %>%
  filter(topic %in% top_topics) %>%
  select(topic, primary_frame, pct) %>%
  pivot_wider(names_from = primary_frame, values_from = pct, values_fill = 0)

write_csv(topic_frame_heatmap, file.path(OUTPUT_DIR, "datawrapper_topic_frames.csv"))
cat("✓ datawrapper_topic_frames.csv\n")

# ==============================================================================
# COMPLETION
# ==============================================================================

cat("\n", strrep("=", 60), "\n")
cat("MACRO FRAME ANALYSIS COMPLETE\n")
cat(strrep("=", 60), "\n\n")

cat("Output directory:", OUTPUT_DIR, "\n\n")

cat("Key outputs:\n")
cat("  - corpus_with_macro_frames.csv : Full corpus with frame assignments\n")
cat("  - frames_by_year.csv           : Temporal frame distribution\n")
cat("  - frames_by_topic.csv          : Frame distribution per topic\n")
cat("  - frame_summary_topic_party.csv: Summary for thesis tables\n")
cat("  - datawrapper_*.csv            : Ready for Datawrapper visualization\n")

cat("\nFrame assignment approach:\n")
cat("  - Primary frame: highest scoring macro frame\n")
cat("  - Secondary frame: second highest if >= 50% of primary\n")
cat("  - Combined: 'primary + secondary' or just 'primary'\n")
cat("  - Label: includes topic-specific modifier where relevant\n")

cat("\n")
