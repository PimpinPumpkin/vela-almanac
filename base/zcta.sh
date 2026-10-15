#!/usr/bin/env bash
# Census ZIP code tabulation areas -> data/cache/census/zcta.parquet (zip, geom).
# base/address_layers.py gives a ZIP to address points from layers that carry none.
source "$(dirname "$0")/../lib/common.sh"
OUTF="$CACHE/census/zcta.parquet"
[ -s "$OUTF" ] && exit 0
TMP="$CACHE/census/zcta"; mkdir -p "$TMP"
curl -fsS -A "$UA" -o "$TMP/zcta.zip" https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip
(cd "$TMP" && unzip -o -q zcta.zip)
duck <<SQL
copy (select ZCTA5CE20 as zip, geom from st_read('$TMP/cb_2020_us_zcta520_500k.shp')) to '$OUTF.part' (format parquet);
SQL
mv "$OUTF.part" "$OUTF"
rm -rf "$TMP"
