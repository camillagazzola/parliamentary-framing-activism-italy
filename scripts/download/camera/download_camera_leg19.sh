#!/bin/bash
# download_camera_transcripts.sh
# Downloads plenary stenographic transcripts (PDF) from the Camera dei Deputati
# for legislatures XVIII and XIX.
#
# Output: data/raw/camera/leg18/ and leg19/
# Missing or failed downloads logged to data/raw/camera/leg18_missing.txt etc.
#
# Author: Camilla Gazzola
# Project: Italian Parliament Activism Framing (2018-2025)

set -euo pipefail

download_leg() {
    local leg=$1
    local max_seduta=$2
    local out_dir="data/raw/camera/leg${leg}"
    local missing_log="data/raw/camera/leg${leg}_missing.txt"

    mkdir -p "$out_dir"
    : > "$missing_log"

    for n in $(seq -w 1 "$max_seduta"); do
        page_url="https://www.camera.it/leg${leg}/410?idSeduta=${n}&tipo=stenografico"
        pdf_url=$(curl -sL "$page_url" | grep -Eo 'https://documenti\.camera\.it/[^"]+\.pdf' | head -n 1 || true)

        if [ -z "$pdf_url" ]; then
            echo "$n NO_PDF_LINK" >> "$missing_log"
            continue
        fi

        out="${out_dir}/sed${n}.pdf"
        [ -s "$out" ] && continue

        if curl -L -f --retry 5 --retry-delay 2 -o "${out}.part" "$pdf_url"; then
            mv "${out}.part" "$out"
        else
            rm -f "${out}.part"
            echo "$n DOWNLOAD_FAIL $pdf_url" >> "$missing_log"
        fi
    done

    echo "Legislature ${leg} done. Missing: $(wc -l < "$missing_log") sessions."
}

download_leg 18 741
download_leg 19 590
