#!/bin/bash
set -euo pipefail

mkdir -p data/camera/leg19
: > data/camera/leg19_missing.txt

# Leg19 sedute are currently up to ~590, but you can increase later
for n in $(seq -w 1 590); do
  page_url="https://www.camera.it/leg19/410?idSeduta=${n}&tipo=stenografico"

  pdf_url=$(curl -sL "$page_url" | grep -Eo 'https://documenti\.camera\.it/[^"]+\.pdf' | head -n 1 || true)

  if [ -z "$pdf_url" ]; then
    echo "$n NO_PDF_LINK" >> data/camera/leg19_missing.txt
    continue
  fi

  out="data/camera/leg19/sed${n}.pdf"
  [ -s "$out" ] && continue

  if curl -L -f --retry 5 --retry-delay 2 -o "${out}.part" "$pdf_url"; then
    mv "${out}.part" "$out"
  else
    rm -f "${out}.part"
    echo "$n DOWNLOAD_FAIL $pdf_url" >> data/camera/leg19_missing.txt
  fi
done
