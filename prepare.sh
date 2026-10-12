#!/usr/bin/env bash
# Fetch everything that is the same for every state, once: ./prepare.sh
# The register files, the Foursquare closing dates, the AllThePlaces US file
# and the state outlines all land under data/cache. build.sh then finds them
# there. The scheduled build runs this in one job and hands the result to
# the per-state jobs.
source "$(dirname "$0")/lib/common.sh"
cd "$ROOT"
# One source being down must not stop the build. A failed adapter leaves
# last run's file in place, and the watch report says so.
mkdir -p "$CACHE/evidence" "$CACHE/watch"
rm -rf "$CACHE/evidence.prev" && cp -R "$CACHE/evidence" "$CACHE/evidence.prev"
failed=()
# a reader that writes many sources names the ones that failed here
export ALMANAC_FAILED="$CACHE/watch/failed-sources.txt"
: > "$ALMANAC_FAILED"
# read a page at a time over hours, on their own schedule (.github/workflows/crawl.yml);
# their files are already in the evidence folder
SLOW=" usafoodsafety dph_ga_inspections adph_al_food osdh_ok_food "
for adapter in adapters/*.py; do
  case "$SLOW" in *" $(basename "$adapter" .py) "*) echo "== $adapter (slow, not run here)"; continue ;; esac
  echo "== $adapter"
  python3 "$adapter" || { echo "FAILED: $adapter"; failed+=("$(basename "$adapter" .py)"); }
done
while read -r source; do [ -n "$source" ] && failed+=("$source"); done < "$ALMANAC_FAILED"
echo "== source watch"
python3 tools/source_watch.py "$CACHE/evidence" "$CACHE/evidence.prev" "$CACHE/watch/sources.txt" "$CACHE/held" ${failed[@]+"${failed[@]}"}
rm -rf "$CACHE/evidence.prev"
echo "== foursquare closing dates"; signals/fsq_closed.sh >/dev/null
echo "== alltheplaces";             base/atp.sh us >/dev/null
echo "== state outlines";           state_outlines
du -sh "$CACHE/evidence" "$CACHE/fsq" "$CACHE"/atp/us-*.parquet "$CACHE/census/states.parquet"
