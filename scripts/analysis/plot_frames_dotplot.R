#!/usr/bin/env Rscript
# =============================================================================
# plot_frames_dotplot.R
# (De)Legitimising Protest: Parliamentary Framing of Activism in Italy, 2018-2025
# POL30870 Thesis — Camilla Gazzola, UCD 2026
#
# PURPOSE: Produces Figure 7 — party-level frame distribution over time.
#   Each bubble represents a party x topic x year cell, sized by token count
#   and coloured by activism topic. Frame labels are assigned qualitatively
#   from top distinctive lemmas (keyness analysis).
#
# INPUT:  data/frame_coding_years.csv
# OUTPUT: data/frame_dotplot.png
# =============================================================================

library(tidyverse)

BASE        <- here::here()
INPUT_FILE  <- file.path(BASE, "data", "frame_annotation_xy.csv")
OUTPUT_FILE <- file.path(BASE, "data", "frame_dotplot.png")

topic_labels <- c(
  "antisemitism"      = "Antisemitism",
  "climate_activists" = "Climate activists",
  "far_right"         = "Far right",
  "labor"             = "Labour",
  "migrants"          = "Migrants",
  "no_vax"            = "Anti-vax",
  "police_security"   = "Police & security",
  "prisoners_rights"  = "Incarcerated people",
  "pro_palestine"     = "Pro-Palestine",
  "students"          = "Students"
)

topic_colours <- c(
  "Antisemitism"        = "#254B8C",
  "Climate activists"   = "#5DF8D8",
  "Far right"           = "#9FD9BF",
  "Labour"              = "#0F67AA",
  "Migrants"            = "#4C614F",
  "Anti-vax"            = "#77C1C2",
  "Police & security"   = "#077A7D",
  "Incarcerated people" = "#4dac26",
  "Pro-Palestine"       = "#00CAFF",
  "Students"            = "#B4C068"
)

frame_order <- c(
  "legality", "security", "humanitarianism",
  "delegitimisation", "morality", "national_identity"
)

party_order <- c("AVS", "FDI", "M5S", "PD", "LEGA", "IV")

df <- read_csv(INPUT_FILE, show_col_types = FALSE) %>%
  filter(!is.na(frame_primary), frame_primary != "") %>%
  mutate(
    year          = as.integer(year),
    n_tokens      = as.numeric(n_tokens),
    frame_primary = str_to_lower(str_trim(frame_primary)),
    frame_primary = case_when(
      str_detect(frame_primary, "legal")    ~ "legality",
      str_detect(frame_primary, "security") ~ "security",
      str_detect(frame_primary, "humanit")  ~ "humanitarianism",
      str_detect(frame_primary, "delegit")  ~ "delegitimisation",
      str_detect(frame_primary, "moral")    ~ "morality",
      str_detect(frame_primary, "national") ~ "national_identity",
      TRUE                                  ~ frame_primary
    )
  ) %>%
  filter(party_clean %in% party_order) %>%
  mutate(
    topic_label   = recode(topic, !!!topic_labels),
    frame_primary = factor(frame_primary, levels = rev(frame_order)),
    party_clean   = factor(party_clean,   levels = party_order),
    topic_label   = factor(topic_label,   levels = names(topic_colours))
  )

dodge_width <- 0.20

df_plot <- df %>%
  group_by(party_clean, year, frame_primary) %>%
  mutate(
    n_in_cell    = n(),
    rank_in_cell = row_number(),
    x_offset     = (rank_in_cell - (n_in_cell + 1) / 2) * dodge_width,
    x_pos        = year + x_offset
  ) %>%
  ungroup()

p <- ggplot(
  df_plot,
  aes(x = x_pos, y = frame_primary, size = n_tokens,
      colour = topic_label, fill = topic_label)
) +
  geom_point(alpha = 0.88, shape = 21, stroke = 0, colour = "white") +
  facet_wrap(~ party_clean, ncol = 3, scales = "fixed") +
  scale_size(
    range  = c(4, 13),
    name   = "N tokens",
    breaks = c(200, 600, 1200, 2000, 3000),
    labels = c("200", "600", "1,200", "2,000", "3,000"),
    guide  = guide_legend(override.aes = list(fill = "grey50"))
  ) +
  scale_fill_manual(
    values = topic_colours, name = "Topic",
    guide  = guide_legend(override.aes = list(size = 4))
  ) +
  scale_colour_manual(values = topic_colours, guide = "none") +
  scale_x_continuous(breaks = 2019:2025, limits = c(2018.3, 2025.7)) +
  labs(
    x       = "Year",
    y       = "Primary frame",
    caption = "Bubble size = total tokens in party × topic × year cell. Frame assigned qualitatively from top distinctive lemmas."
  ) +
  theme_minimal(base_size = 13) +
  theme(
    panel.grid.minor  = element_blank(),
    panel.grid.major  = element_line(colour = "grey92"),
    strip.text        = element_text(face = "bold", size = 13),
    axis.title        = element_text(face = "bold"),
    axis.text.y       = element_text(size = 11),
    axis.text.x       = element_text(size = 9),
    legend.position   = "right",
    legend.title      = element_text(face = "bold", size = 11),
    plot.caption      = element_text(colour = "grey50", size = 8),
    plot.margin       = margin(20, 10, 20, 10)
  )

ggsave(OUTPUT_FILE, plot = p, width = 15, height = 8, dpi = 300)
cat("Saved:", OUTPUT_FILE, "\n")
