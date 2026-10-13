#!/usr/bin/env bash
# Overture address points inside a region box -> $OUT/addresses.parquet
# Used to put a register row that has only an address on its building.
# Every address point Overture carries is read, whatever license Overture
# attaches to its source: the National Address Database and county files
# that are public domain, Ada County, Idaho (CC BY), and the files Overture
# marks proprietary (Colorado, Oregon, Mississippi, New York City, Los
# Angeles County). The owner decided on 2026-10-12 to use them all; see
# SOURCES.md. Only a position is taken, for a register row that adds a
# place; no address is published from here.
source "$(dirname "$0")/../lib/common.sh"
region "$1"

BUCKET=https://overturemaps-us-west-2.s3.amazonaws.com
RELEASE="${OVERTURE_RELEASE:-$(cat "$OUT/overture.release" 2>/dev/null)}"
[ -n "$RELEASE" ] || { echo "no Overture release named" >&2; exit 1; }
FILES="$(curl -fsS -A "$UA" "$BUCKET/?list-type=2&prefix=release/$RELEASE/theme=addresses/type=address/" \
  | tr '<' '\n' | sed -n "s|^Key>\(.*parquet\)$|'$BUCKET/\1'|p" | paste -sd, -)"
[ -n "$FILES" ] || { echo "no Overture address files for $RELEASE" >&2; exit 1; }

duck <<SQL
copy (
  select number, street, postcode, st_y(geometry) as lat, st_x(geometry) as lng
  from read_parquet([$FILES])
  where bbox.xmin >= $W and bbox.xmax <= $E and bbox.ymin >= $S and bbox.ymax <= $N
    and country = '$COUNTRY' and number is not null and street is not null and postcode is not null
) to '$OUT/addresses.parquet.part' (format parquet, compression zstd);
SQL
mv "$OUT/addresses.parquet.part" "$OUT/addresses.parquet"
