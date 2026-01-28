#!/bin/bash
set -euo pipefail

YEAR="${1:-2025}"
OUTDIR="${2:-data/senato/${YEAR}}"
INDEX_URL="https://www.senato.it/lavori/assemblea/resoconti-elenco-cronologico?year=${YEAR}"

mkdir -p "$OUTDIR"

echo "Index: $INDEX_URL"

# Get seduta numbers from the table (e.g., 259..304)
sedute=$(curl -sL "$INDEX_URL" | grep -Eo '\|[0-9]{1,4}\|' | tr -d '|' | sort -n | uniq)

# IMPORTANT: you must paste ONE real “html” seduta URL pattern here.
# Placeholder (will not work until updated):
# Example expected: https://www.senato.it/service/PDF/PDFServer/BGT/XXXXXXXX.pdf is extracted from that page.
for n in $sedute; do
  html_url="PASTE_A_REAL_SEDUTA_HTML_URL_HERE_WITH_${n}"

  pdf_url=$(curl -sL "$html_url" | grep -Eo 'https://www\.senato\.it/service/PDF/PDFServer/BGT/[0-9]+\.pdf' | head -n 1 || true)

  if [[ -z "$pdf_url" ]]; then
    echo "No PDF found for seduta $n"
    continue
  fi

  out="${OUTDIR}/seduta_${n}.pdf"
  echo "Downloading seduta $n -> $out"
  curl -L --fail --retry 5 --retry-delay 2 -o "$out" "$pdf_url"
done
