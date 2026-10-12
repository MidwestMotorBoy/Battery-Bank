#!/usr/bin/env bash
# Download every datasheet listed in datasheets/sources.csv into datasheets/.
# Run from the repo root on a machine with normal internet access:
#   bash tools/fetch_datasheets.sh
# Files that come back as something other than a PDF (e.g. a web page asking
# for JavaScript) are deleted and listed at the end; grab those by hand.
set -u
cd "$(dirname "$0")/.."
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
tail -n +2 datasheets/sources.csv | while IFS=, read -r file part role url; do
  [ -z "$file" ] && continue
  case "$url" in http*) ;; *) echo "SKIP  $file ($url)"; echo "$file" >> /tmp/ds_failed.$$; continue;; esac
  out="datasheets/$file"
  if [ -s "$out" ] && head -c 4 "$out" | grep -q '%PDF'; then echo "HAVE  $file"; continue; fi
  if curl -sSL -A "$UA" -m 120 -o "$out" "$url" && head -c 4 "$out" | grep -q '%PDF'; then
    echo "OK    $file"
  else
    rm -f "$out"; echo "FAIL  $file  <- $url"; echo "$file" >> /tmp/ds_failed.$$
  fi
done
if [ -f /tmp/ds_failed.$$ ]; then
  echo; echo "Download these by hand into datasheets/:"; cat /tmp/ds_failed.$$; rm -f /tmp/ds_failed.$$
fi
