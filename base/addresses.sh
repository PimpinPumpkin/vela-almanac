#!/usr/bin/env bash
# Overture address points inside a region box -> $OUT/addresses.parquet
# Used to put a register row that has only an address on its building. Only
# points whose own source is public domain or CC0 are kept (in the United
# States that is the National Address Database), so the core layer takes on
# no new terms. A state the database does not cover yields an empty file.
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
    and sources[1].license in ('LicenseRef-Public-Domain-US', 'CC0-1.0', 'PDDL-1.0')
) to '$OUT/addresses.parquet.part' (format parquet, compression zstd);
SQL
mv "$OUT/addresses.parquet.part" "$OUT/addresses.parquet"
