#!/bin/bash
set -euo pipefail

YEAR="${1:-2025}"
OUTDIR="${2:-data/senato/${YEAR}}"
BASE_YEAR_URL="https://www.senato.it/lavori/assemblea/resoconti-elenco-cronologico?year=${YEAR}"

mkdir -p "$OUTDIR"

echo "Fetching index: $BASE_YEAR_URL"

# Extract seduta numbers from the year page (e.g., 259..304) [page:2]
sedute=$(curl -sL "$BASE_YEAR_URL" | grep -Eo '\|[0-9]{1,4}\|' | tr -d '|' | sort -n | uniq)

for n in $sedute; do
  # This is the usual pattern for the “resoconto” page of that seduta (HTML)
  # If your Senato site uses a slightly different per-seduta URL, paste one example and it can be adjusted.
  html_url="https://www.senato.it/lavori/assemblea/resoconto-stenografico?seduta=${n}&year=${YEAR}"

  echo "Seduta $n -> $html_url"

  # Grab the first BGT PDF link on that page
  pdf_url=$(curl -sL "$html_url" | grep -Eo 'https://www\.senato\.it/service/PDF/PDFServer/BGT/[0-9]+\.pdf' | head -n 1 || true)

  if [[ -z "$pdf_url" ]]; then
    echo "  !! No PDF found for seduta $n (skip)"
    continue
  fi

  out="${OUTDIR}/seduta_${n}.pdf"
  echo "  Downloading: $pdf_url"
  curl -L --fail --retry 5 --retry-delay 2 -o "$out" "$pdf_url"
done

echo "Done: $OUTDIR"
