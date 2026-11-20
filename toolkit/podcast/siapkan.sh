#!/bin/bash
# Menyiapkan folder kerja podcast: bash toolkit/podcast/siapkan.sh /tmp/pod
# Hasil: folder berisi sh/ env2.jpg mic.jpg norm.json cells/ cells.json + skrip render. Episode ditaruh di ep3/ (lihat STUDIO_NABILA.md).
set -e
R="$(cd "$(dirname "$0")/../.." && pwd)"; W="${1:?folder kerja}"
mkdir -p "$W" "$W/ep3"
ln -sfn "$R/assets/podcast/sheets" "$W/sh"
cp "$R/assets/podcast/bg_olive.jpg" "$W/env2.jpg"
cp "$R/assets/podcast/bg_navy_rusdi.jpg" "$W/env_navy.jpg"
cp "$R/assets/podcast/mic_sheet.jpg" "$W/mic.jpg"
cp "$R"/toolkit/podcast/*.py "$R"/toolkit/podcast/norm.json "$W/"
cp -r "$R"/toolkit/podcast/contoh "$W/"
cd "$W" && python3 cut.py >/dev/null && echo "siap: $W ($(ls cells | wc -l) sel)"
