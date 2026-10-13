#!/usr/bin/env bash
# Build one region end to end: ./build.sh dc-box
# Imports are cached under data/. Delete a file there to refetch it.
source "$(dirname "$0")/lib/common.sh"
region "$1"
cd "$ROOT"
BUILD_DATE="${BUILD_DATE:-$(date -u +%F)}"
step() { printf '%s  %s\n' "$(date +%T)" "$*" >&2; }

[ -s "$OUT/overture.parquet" ] || { step overture; base/overture.sh "$REGION" >/dev/null; }
[ -s "$OUT/atp.parquet" ]      || { step alltheplaces; base/atp.sh "$REGION" >/dev/null; }
[ -s "$OUT/osm.parquet" ]      || { step osm; base/osm.sh "$REGION" >/dev/null; }
# Address points are optional: without them, registers that come with no
# position of their own match places as before and add none.
[ -s "$OUT/addresses.parquet" ] || { step addresses; base/addresses.sh "$REGION" >/dev/null || rm -f "$OUT/addresses.parquet" "$OUT/addresses.parquet.part"; }
ADDR_SQL="select null::varchar as number, null::varchar as street, null::varchar as postcode, null::double as lat, null::double as lng where false"
[ -s "$OUT/addresses.parquet" ] && ADDR_SQL="select number, street, postcode, lat, lng from '$OUT/addresses.parquet'"
step foursquare closing dates; FSQ_COUNTRY="$COUNTRY" signals/fsq_closed.sh >/dev/null
# Registers are per country. US files sit in data/cache/evidence, another
# country's in data/cache/evidence/<code>. prepare.sh fetches the US set.
if [ "$COUNTRY" = US ]; then
  [ -s "$CACHE/evidence/fdic.csv" ] || { step fdic; adapters/fdic.py; }
  [ -s "$CACHE/evidence/snap.csv" ] || { step snap; adapters/snap.py; }
  EVIDENCE_DIR="$CACHE/evidence"; FSQ_FILE="$CACHE/fsq/closed-${FSQ_RELEASE:-2025-02-06}.parquet"
else
  EVIDENCE_DIR="$CACHE/evidence/$(printf %s "$COUNTRY" | tr A-Z a-z)"; mkdir -p "$EVIDENCE_DIR"
  FSQ_FILE="$CACHE/fsq/closed-${FSQ_RELEASE:-2025-02-06}-$COUNTRY.parquet"
fi
# Evidence comes as CSV from the Python adapters and as parquet from the SQL ones.
EV_COLS="source, source_id, name, address, lat, lng, state, date"
EV_SQL="select null::varchar as source, null::varchar as source_id, null::varchar as name, null::varchar as address, null::double as lat, null::double as lng, null::varchar as state, null::date as date where false"
if ls "$EVIDENCE_DIR"/*.csv >/dev/null 2>&1; then
  EV_SQL="$EV_SQL union all select $EV_COLS from read_csv('$EVIDENCE_DIR/*.csv', header = true, auto_detect = false, delim = ',', quote = '\"', escape = '\"', columns = {source: 'varchar', source_id: 'varchar', name: 'varchar', address: 'varchar', lat: 'double', lng: 'double', state: 'varchar', date: 'date'})"
fi
if ls "$EVIDENCE_DIR"/*.parquet >/dev/null 2>&1; then
  EV_SQL="$EV_SQL union all select $EV_COLS from read_parquet('$EVIDENCE_DIR/*.parquet')"
fi

# Pins: positions some registers get from a second public layer, by record id. A row may add
# a place from its pin; see sql/core.sql.
PINS_SQL="select null::varchar as source, null::varchar as source_id, null::double as lat, null::double as lng where false"
if ls "$EVIDENCE_DIR"/pins/*.csv >/dev/null 2>&1; then
  PINS_SQL="select source, source_id, lat, lng from read_csv('$EVIDENCE_DIR/pins/*.csv', header = true, auto_detect = false, columns = {source: 'varchar', source_id: 'varchar', lat: 'double', lng: 'double'})"
fi

# OpenPOIs covers the US only. A failed read leaves the build without it.
if [ "$COUNTRY" = US ] && [ ! -s "$OUT/openpois.parquet" ]; then
  step openpois; signals/openpois.sh "$REGION" >/dev/null || rm -f "$OUT/openpois.parquet"
fi
OPENPOIS_SQL="select null::varchar as overture_id, null::varchar as osm_type, null::bigint as osm_id, null::double as conf_mean, null::varchar as osm_name, null::varchar as overture_name, null::varchar as event, null::date as event_date where false"
[ -s "$OUT/openpois.parquet" ] && OPENPOIS_SQL="select overture_id, osm_type, osm_id, conf_mean, osm_name, overture_name, event, event_date from '$OUT/openpois.parquet'"

step wikidata
duckdb -noheader -csv -c "select distinct wikidata from '$OUT/osm.parquet' where wikidata is not null" \
  | python3 signals/wikidata_p576.py > "$OUT/p576.csv"

# A state region is clipped to the state's outline. The outline is
# generalized, so a row just outside it (a pier, a shoreline shop) is kept
# when its own address names the state and it is within about 5 km.
CLIP=""
if [ -n "${STATE:-}" ]; then
  state_outlines
  CLIP="create table outline as select st_geomfromwkb(wkb) as g from '$CACHE/census/states.parquet' where state = '$STATE';
create table outlines as select state, st_geomfromwkb(wkb) as g from '$CACHE/census/states.parquet';"
  for t in ovt atp osm; do
    CLIP="$CLIP
delete from $t where not (
  st_contains((select g from outline), st_point(lng, lat))
  or (region = '$STATE' and st_dwithin((select g from outline), st_point(lng, lat), 0.05)));
-- The other side of that allowance: a row inside this outline whose address names a
-- neighbor, and which the neighbor's build keeps under the same rule, is the neighbor's.
-- Without this a shop on a state line was in both files.
delete from $t where region <> '$STATE' and region in (select state from outlines)
  and st_dwithin((select g from outlines o where o.state = $t.region), st_point(lng, lat), 0.05);"
  done
  # Register rows too: a state's box reaches into its neighbors (New Jersey's covers Manhattan),
  # and a neighbor's licensed shop that matches nothing here would be added to this state as new.
  # A row whose own address names another state goes too, wherever its point falls: Delaware's
  # outline takes in the river up to the New Jersey shore.
  REG_CLIP="delete from register where
  coalesce(nullif(regexp_extract(address, ', ([A-Z]{2})( [0-9]{5})?(-[0-9]{4})?\\s*\$', 1), ''), '$STATE') <> '$STATE'
  or (lat is not null and not (st_contains((select g from outline), st_point(lng, lat))
          or (regexp_matches(address, ', $STATE( [0-9]{5})?(-[0-9]{4})?\\s*\$') and st_dwithin((select g from outline), st_point(lng, lat), 0.05))));"
fi

DB="$OUT/build.duckdb"; rm -f "$DB"
step merge and match
duck "$DB" >/dev/null <<SQL
.bail on
.read sql/lib.sql
.read sql/groups.sql
.read sql/status.sql
create table params as select date '$BUILD_DATE' as build_date, 730 as recent_days,
  $S as s, $W as w, $N as n, $E as e;
create table ovt as select * from '$OUT/overture.parquet';
-- imports cached before the category group was kept
alter table ovt add column if not exists category_group varchar;
alter table ovt add column if not exists category_subgroup varchar;
create table atp as select * from '$OUT/atp.parquet';
create table osm as select * from '$OUT/osm.parquet';
create table addr as $ADDR_SQL;
create table pins as $PINS_SQL;
-- extracts cached before the SIRET column existed
alter table osm add column if not exists siret varchar;
-- files cached before opening hours were kept
alter table osm add column if not exists opening_hours varchar;
alter table atp add column if not exists opening_hours varchar;
$CLIP
create table p576 as select qid, date from read_csv('$OUT/p576.csv', header = true, auto_detect = false,
  columns = {qid: 'varchar', date: 'date'});
create table openpois as $OPENPOIS_SQL;
create table fsq_closed as
  select * from '$FSQ_FILE'
  where lat between $S and $N and lng between $W and $E;
create table register as
  select * from ($EV_SQL)
  where date between date '1900-01-01' and date '$BUILD_DATE'
    and ((lat between $S and $N and lng between $W and $E)
     -- records with an address but no position: keep the ones in a postal code the region has
     or (lat is null and zip5(address) in (select distinct zip5(postcode) from ovt)));
${REG_CLIP:-}
.read sql/core.sql
.read sql/full.sql
.read sql/publish.sql
SQL

# Publish: two GeoParquet files per region and one manifest.
#   core-REGION.parquet    Overture + AllThePlaces + non-OSM evidence
#   places-REGION.parquet  the same places plus OpenStreetMap
#   status-REGION.parquet  id, status and score only, from the places file
# Both are released under the ODbL.
# Rows are in Hilbert order with small row groups, and lat/lng are plain
# columns, so a reader can prune on their statistics over HTTP range requests.
PUB="$DATA/out"; mkdir -p "$PUB"
step publish
for layer in core full; do
  [ "$layer" = core ] && f="$PUB/core-$REGION.parquet" || f="$PUB/places-$REGION.parquet"
  duck -readonly "$DB" >/dev/null <<SQL
copy (
  select * from out_$layer
  order by st_hilbert(geometry, st_makebox2d(st_point($W, $S), st_point($E, $N)))
) to '$f' (format parquet, compression zstd, row_group_size 20000);
SQL
done
# A small file for readers that only join on id, and for the monthly change file.
duck -readonly "$DB" >/dev/null <<SQL
copy (
  select id, status, status_date, status_source, open_score, missing_license
  from out_full order by id
) to '$PUB/status-$REGION.parquet' (format parquet, compression zstd);
SQL

entry() {  # entry FILE LAYER LICENSE
  jq -n --arg name "$(basename "$1")" --arg layer "$2" --arg license "$3" \
    --argjson rows "$(duckdb -noheader -csv -c "select count(*) from '$1'")" \
    --argjson bytes "$(wc -c < "$1")" --arg sha256 "$(shasum -a 256 "$1" | cut -d' ' -f1)" \
    '{name: $name, layer: $layer, license: $license, rows: $rows, bytes: $bytes, sha256: $sha256}'
}
jq -n --arg region "$REGION" --arg build_date "$BUILD_DATE" \
  --argjson bbox "[$W, $S, $E, $N]" \
  --arg country "${COUNTRY:-US}" --arg state "$STATE" --arg extracts "$OSM_EXTRACTS" \
  --arg overture "$(cat "$OUT/overture.release")" --arg atp "$(cat "$OUT/atp.run")" \
  --arg osm "$(cat "$OUT/osm.date")" --arg fsq "${FSQ_RELEASE:-2025-02-06}" \
  --arg openpois "$(cat "$OUT/openpois.version" 2>/dev/null || true)" \
  --argjson core "$(entry "$PUB/core-$REGION.parquet" core "ODbL-1.0")" \
  --argjson full "$(entry "$PUB/places-$REGION.parquet" full "ODbL-1.0")" \
  --argjson status "$(entry "$PUB/status-$REGION.parquet" status "ODbL-1.0")" \
  '{dataset: "Vela Almanac", license: "ODbL-1.0",
    credit: "Vela Almanac, (c) its contributors. Open Database License 1.0. https://github.com/PimpinPumpkin/vela-almanac",
    notice: "https://github.com/PimpinPumpkin/vela-almanac/blob/main/NOTICE",
    region: $region, build_date: $build_date, bbox: $bbox,
    country: $country,
    iso_3166_2: (if ($state | test("^[A-Z]{2}$")) then "\($country)-\($state)" else null end),
    osm_extracts: ($extracts | split(",")),
    sources: {overture: $overture, alltheplaces: $atp, openstreetmap: $osm, foursquare_os_places: $fsq, openpois: $openpois},
    files: [$core, $full, $status]}' > "$PUB/manifest-$REGION.json"
step done
