#!/bin/bash
set -euo pipefail

YEAR="${1:?Usage: ./senato_download_year_fast.sh YEAR [JOBS] [LEG]}"
JOBS="${2:-20}"
LEG="${3:-19}"   # 18 for 2018-2022, 19 for 2023+ (and 2025 you tested)
OUTDIR="${4:-data/senato/leg${LEG}/${YEAR}}"

# Pick the right index URL depending on legislature
if [ "$LEG" = "18" ]; then
  INDEX_URL="https://www.senato.it/legislature/18/lavori/assemblea/resoconti-elenco-cronologico?year=${YEAR}"
else
  INDEX_URL="https://www.senato.it/lavori/assemblea/resoconti-elenco-cronologico?year=${YEAR}"
fi

mkdir -p "$OUTDIR"
echo "Index: $INDEX_URL"

# Extract BGT IDs from index page (HTML contains show-doc links with id=....)
ids=$(curl -sL "$INDEX_URL" \
  | grep -Eo 'show-doc\?leg=[0-9]+&amp;tipodoc=Resaula&amp;id=[0-9]+&amp;idoggetto=0' \
  | sed 's/&amp;/\&/g' \
  | grep -Eo 'id=[0-9]+' | cut -d= -f2 \
  | sort -n | uniq)

echo "Found $(echo "$ids" | wc -l | tr -d " ") PDFs"

export OUTDIR
printf "%s\n" $ids | xargs -n 1 -P "$JOBS" -I {} bash -c '
  id="{}"
  pdf="https://www.senato.it/service/PDF/PDFServer/BGT/${id}.pdf"
  out="${OUTDIR}/BGT_${id}.pdf"
  curl -L --fail --retry 5 --retry-delay 2 -o "$out" "$pdf"
'
