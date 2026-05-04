#!/bin/bash
# download_senato_transcripts.sh
# Downloads Senato della Repubblica plenary stenographic transcripts (PDF)
# for a given year, using parallel downloads.
#
# Usage: ./download_senato_transcripts.sh YEAR [JOBS] [LEG]
#   YEAR: target year (e.g. 2023)
#   JOBS: parallel download jobs (default: 20)
#   LEG:  legislature number, 18 or 19 (default: 19)
#
# Output: data/raw/senato/<YEAR>/
#
# Author: Camilla Gazzola
# Project: Italian Parliament Activism Framing (2018-2025)

set -euo pipefail

YEAR="${1:?Usage: ./download_senato_transcripts.sh YEAR [JOBS] [LEG]}"
JOBS="${2:-20}"
LEG="${3:-19}"
OUTDIR="${4:-data/raw/senato/${YEAR}}"

if [ "$LEG" = "18" ]; then
  INDEX_BASE="https://www.senato.it/legislature/18/lavori/assemblea/resoconti-elenco-cronologico"
else
  INDEX_BASE="https://www.senato.it/lavori/assemblea/resoconti-elenco-cronologico"
fi

INDEX_URLS=(
  "${INDEX_BASE}?anno=${YEAR}"
  "${INDEX_BASE}?year=${YEAR}"
  "${INDEX_BASE}"
)

mkdir -p "$OUTDIR"
: > "${OUTDIR}/missing_ids.txt"

pick_index() {
  for u in "${INDEX_URLS[@]}"; do
    html=$(curl -sL "$u" || true)
    if echo "$html" | grep -q "tipodoc=Resaula"; then
      echo "$u"
      return 0
    fi
  done
  return 1
}

INDEX_URL=$(pick_index) || { echo "Could not fetch an index page"; exit 1; }
echo "Index: $INDEX_URL"

ids=$(curl -sL "$INDEX_URL" \
  | grep -Eo 'show-doc\?leg=[0-9]+&amp;tipodoc=Resaula&amp;id=[0-9]+&amp;idoggetto=0' \
  | sed 's/&amp;/\&/g' \
  | grep -Eo 'id=[0-9]+' | cut -d= -f2 \
  | sort -n | uniq)

count=$(echo "$ids" | sed '/^\s*$/d' | wc -l | tr -d " ")
echo "Found ${count} IDs (before year filtering)"

filtered_ids=$(
  printf "%s\n" $ids | xargs -n 1 -P "$JOBS" -I {} bash -c '
    id="{}"
    year="'"$YEAR"'"
    leg="'"$LEG"'"
    url="https://www.senato.it/show-doc?leg=${leg}&tipodoc=Resaula&id=${id}&idoggetto=0"
    html=$(curl -sL "$url" || true)
    echo "$html" | grep -q "${year}" && echo "$id" || true
  '
)

count2=$(echo "$filtered_ids" | sed '/^\s*$/d' | wc -l | tr -d " ")
echo "After filtering to YEAR=${YEAR}: ${count2} IDs"

export OUTDIR
printf "%s\n" $filtered_ids | sed '/^\s*$/d' | xargs -n 1 -P "$JOBS" -I {} bash -c '
  id="{}"
  pdf="https://www.senato.it/service/PDF/PDFServer/BGT/${id}.pdf"
  out="${OUTDIR}/BGT_${id}.pdf"
  [ -s "$out" ] && exit 0
  if ! curl -L --fail --retry 5 --retry-delay 2 -o "$out" "$pdf"; then
    echo "$id" >> "${OUTDIR}/missing_ids.txt"
    exit 0
  fi
'

echo "Done. Missing ids (if any): ${OUTDIR}/missing_ids.txt"
