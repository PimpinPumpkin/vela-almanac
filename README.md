# Vela Almanac

> **Not ready to use yet.** The files are published every month so the
> work can be checked, but the columns, the ids and the rules still change
> from one build to the next. Do not build on it yet.

An open table of every place in the United States a person can walk into,
rebuilt every month, that **adds new businesses on its own**: a shop, bar
or bank branch appears here when a regulator lists it, without anyone
having to draw it on a map first.

Open maps learn about a new business when a volunteer or the owner adds
it, and about a closed one when somebody notices. Regulators, licensing
boards and the chains themselves know sooner, and they publish it. Vela
Almanac reads what they publish, more than a hundred public sources each
month, and does three things with it:

1. **Adds places no map has.** A newly licensed bar, a new bank branch, a
   store newly authorized for food stamps or a new lottery retailer is in
   its register the day the regulator lists it. When that row matches
   nothing in Overture Maps, OpenStreetMap or any chain's store locator,
   and no neighbor looks like the same shop under another name, it
   becomes a place, with the register row as its proof.
2. **Says whether each place is still open**, with the dated record
   behind the answer: a license renewed, an inspection passed, a branch
   closing filed.
3. **Marks the listings nobody vouches for.** A third of the places in the
   open map datasets exist in one upstream source and nowhere else. Each
   place gets an `open_score` from 0 to 1 so a reader can dim or drop
   them.

What it reads:

- **The open map datasets**: Overture Maps, OpenStreetMap, and AllThePlaces,
  which reads every chain's own store locator.
- **Regulators and registers**: bank and credit union branch lists and
  closings, liquor license boards, restaurant inspections, the food stamp retailer list, the federal
  fuel tank registry, school, hospital and health provider registers,
  nonprofit tax filings, state lists of licensed salons, barber shops and
  repair shops, and state business licenses and sales tax permits.
- **Signs of closure**: Foursquare closing dates, closures tagged by
  OpenStreetMap mappers, and places deleted or renamed in OpenStreetMap's
  edit history.

What comes out of the build of 2026-10-12, for all 50 states and DC:

| | |
| --- | ---: |
| Places | 19.5 million |
| Added from a register because no map dataset had them | 295,000 |
| Confirmed open by a dated record from the last two years | 2.4 million |
| Marked closed, with the date and the source | 147,000 |

Which registers may add a place is decided one at a time, by reading what
each would add. Liquor licenses, bank branches and food stamp retailers
pass: they list storefronts. Restaurant inspection lists and salon
licenses do not, because they also list school kitchens, kiosks inside
supermarkets and people renting a chair, so those are used only as proof
that a known place is open. A register that gives an address and no
position adds a place only where the address is a known address point, so
nothing is dropped in the middle of a street. The numbers for each are in
[SPEC.md](SPEC.md), sections 6 and 9.

Nothing is guessed. A place is only called closed when a source says so
with a date and nothing newer says otherwise, and every rule in the build
was checked by reading its matches. The rules that failed that check are
written down with their numbers in [SPEC.md](SPEC.md).

## Coverage by state

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/coverage-dark.svg">
  <img alt="Share of places with a dated open or closed status, by state and category" src="docs/coverage-light.svg">
</picture>

Interactive version, with the numbers on hover:
https://pimpinpumpkin.github.io/vela-almanac/ . The same numbers as a table are
in [COVERAGE.md](COVERAGE.md). Both are made by `tools/coverage_map.py`.

## Coverage by category

What the Almanac lists today, how much of it has a dated open or closed
record, and which public register can close the gap. Counts are from the
2026-10-12 build of all 50 states and DC: 19.5 million places, 13.1% of them
with a dated status.

| Category | Listed | Has a dated status | What it comes from, and what comes next | Can it be complete? |
| --- | ---: | ---: | --- | --- |
| Banks and credit unions | 214,274 | 66% | FDIC branches and closings, NCUA credit union offices (built) | Yes |
| Fast food and chain restaurants | 128,095 | 61% | Chain store locators (built) | Yes, for chains with a locator |
| Gas stations | 137,349 | 57% | Chain locators, EPA fuel tank registry (built) | Mostly |
| Grocery and convenience stores | 236,711 | 49% | SNAP authorized stores, chain locators (built) | Mostly |
| Pharmacies | 63,325 | 41% | Chain locators, NPPES, pharmacy boards in California, Texas and Ohio, Connecticut licenses (built) | Mostly |
| Schools | 433,837 | 24% | NCES public schools (built). The category also holds preschools, private and trade schools, which NCES public data does not cover | Public schools yes |
| Restaurants and cafes, independent | 1,199,172 | 35% | Foursquare closing dates, OSM, alcohol licenses in 21 states and DC, inspections or food licenses statewide in Florida, Michigan, New York, North Carolina and South Carolina and in a dozen cities, and eight more states read from their search pages on a slower schedule (built) | State by state, never everywhere |
| Hotels | 114,830 | 21% | Chain locators (built). Next: state lodging licenses where published | Chains yes, independents patchy |
| Hospitals | 53,943 | 14% | CMS hospitals, NPPES (built). The category also holds departments and clinics listed as hospitals | Real hospitals yes |
| Museums | 37,095 | 13% | IRS exempt organizations (built) | Partly |
| Bars | 160,280 | 28% | Foursquare, OSM, alcohol licenses in 21 states and DC (built), four of them read through a search form or the state's own export | Where the state publishes its list, about half today. See below |
| Everything else | 16,414,406 | 9% | Salons, repair shops, offices, clinics, churches. NPPES, IRS exempt organizations, sales tax and business licenses in four states and a dozen cities, salon and repair shop licenses in five states, child care centers in twelve (built) | No. This is the long tail |
| EV chargers | | | Not handled yet. The federal station list needs a free API key | Yes, if a key is allowed |
| Parks | | | OSM. Parks rarely close, so a listing is most of the job | Listing yes, status not needed |

The split by state is in [COVERAGE.md](COVERAGE.md).

Bars and restaurants depend on whether the state publishes a license
list or inspections. Where it does, it helps but does not finish the job:
bars with a status are 51% in the District of Columbia, 49% in Nebraska,
41% in New York, North Carolina, Washington and Idaho, 36% in Texas and
33% in California, against 27% nationally. Most of the rest are bar listings that
match no license at all. In DC and New York those get a low `open_score`
and a `missing_license` flag, not a closed status (SPEC.md section 7).

A third of all places (34%) have no evidence and exist in one upstream
source only. They stay `unknown`, with a low `open_score` set by where the
listing came from, so a reader can dim them.

Status: early. Every state builds each month and the files are published
as [releases](https://github.com/PimpinPumpkin/vela-almanac/releases).

## What it is

- **Base layer**, imported: Overture Maps places, OpenStreetMap named
  businesses and landmarks, AllThePlaces chain locations.
- **Evidence layer**: public records that say a specific place was open or
  closed on a specific date. Today: Foursquare closing dates, OSM lifecycle
  tags and survey dates, OSM edit history (through OpenPOIs), Wikidata
  dissolution dates, FDIC bank branches and branch closings, NCUA credit
  union offices, USDA SNAP authorized stores, the EPA fuel tank registry,
  CMS hospitals, NCES public schools, NPPES health care organizations, IRS
  exempt organizations, alcohol licenses in California, Colorado, Florida,
  Missouri, New York, Oregon, Texas and the District of Columbia, restaurant inspections in Florida,
  New York City, Chicago and King County (Seattle), and presence in a chain's own store locator.
- **New places from registers**: a bank branch, SNAP store or licensed
  premises that none of the three base datasets lists is added as a place.
- **Output**: one row per place with a stable id, merged attributes, every
  source id it was built from, a status of open, closed or unknown with
  the date and source of the evidence that decided it, and an `open_score`
  from 0 to 1 for every place.

France is the first country after the US: a Paris test box builds with the
global signals plus SIRENE, the French business register (SPEC.md
section 10). It is not in the monthly release yet.

## What it is not

- Not a new survey. Every fact comes from a source listed in `SOURCES.md`.
- Not complete on status. Most places have no dated evidence and are
  `unknown`. Nationally 13.1% of places get a status. `unknown` means nobody
  has said, not "probably open".
- Maintained by the Vela Maps project (github.com/PimpinPumpkin/Vela).
  Anyone can use it, and nothing in it depends on Vela: readers fetch the
  published files.

## Layout

```
build.sh            build one region end to end
stats.sh            print the numbers for a built region
review.sh           print a fixed sample of matches for a person to read
regions.tsv         region boxes and which OSM extracts cover them
base/               importers: overture.sh, addresses.sh, atp.sh + atp.py, osm.sh + osm.jq
signals/            closing signals joined by id: fsq_closed.sh, wikidata_p576.py
adapters/           one file per register. Federal: fdic, ncua, snap, epa_ust,
                    cms, nces, nppes, irs. State and city: abc_ca, abca_dc, bbl_dc,
                    sla_ny, tabc_tx, cpa_tx, tdlr_tx, biz_de, rev_pa, abt_fl, led_co, atc_mo, olcc_or, dbpr_fl_food,
                    kc_wa_food, dmv_ny, dos_ny_salons, dohmh_nyc,
                    cdph_chicago, bacp_chicago, agm_ny, dcwp_nyc, dph_de,
                    moco_md, bot_sac, emd_sac, lou_food, abc_ky_jefferson,
                    li_phl, biz_seattle, biz_denver, tax_ny_tobacco,
                    rev_pa_tobacco, cpa_tx_tobacco, elicense_ct, dmv_ct,
                    biz_nola, dol_wa, childcare_wa, childcare_co,
                    dbpr_fl_licenses, ocm_ny, doh_ny_food, boston_ma,
                    lcb_wa, abc_nj, dor_wi_liquor, lcc_ne, bablo_me, isp_id_liquor,
                    abc_ar, able_ok, biz_lasvegas, dchd_omaha_food, minneapolis_mn,
                    llb_baltimore, cph_columbus_food, mdard_mi_food, dph_sc_food,
                    mda_mn_food, dca_ca, dpor_va, pharmacy_boards, hrsa,
                    childcare_centers, city_layers, abc_nc, abc_ky,
                    abc_ks, plcb_pa, tda_tn_food, dhhs_nc_inspections,
                    msdh_ms_food, achd_pa_food, biz_sandiego, open_data_tables,
                    and four that are
                    slow and run on their own schedule:
                    usafoodsafety, dph_ga_inspections, adph_al_food,
                    osdh_ok_food. France: sirene.sh
sql/                lib.sql (matcher), core.sql, full.sql, status.sql, publish.sql
tests/              matcher threshold tests
reports/            numbers from the last build of each region
FOLLOWUPS.md        sources to ask about, retry or test later
tools/              coverage_map.py, which draws the by-state map and table
docs/               the map, and the interactive page served by GitHub Pages
build_all.sh        build every state in regions.tsv, on one machine
prepare.sh          fetch the files every state shares
```

## Build

Needs `duckdb` (built and tested with 1.5.4, with the httpfs and spatial extensions),
`osmium`, `jq`, `curl` and Python 3. No keys, no accounts.

```
duckdb -c "install httpfs; install spatial;"
duckdb < tests/match_test.sql
./build.sh dc-box
./stats.sh dc-box
./review.sh dc-box evidence fdic_history closed number
```

Downloads are cached under `data/`, which is not in git. The first build
fetches about 5 GB (AllThePlaces is 2.6 GB and NPPES 1.2 GB of that). After that a region
the size of Kentucky builds in about 35 seconds.

Every fetch sends
`User-Agent: VelaAlmanac/0.1 (open US places dataset build; https://github.com/PimpinPumpkin/vela-almanac)`.
Set `ALMANAC_CONTACT` to a URL or address to append a way to reach you.

## Scheduled build

`.github/workflows/build.yml` runs on the first of each month and can be
started by hand from the Actions tab. One job fetches the national files
(`prepare.sh`), one job per state runs `build.sh`, and a last job publishes
every state's files as a GitHub release named for the build date, then
redraws the coverage map. A run started by hand with a list of regions is a
test and publishes nothing.

One source being down does not stop a build. A register whose fetch fails,
or whose file comes back less than half the size it was, keeps last
month's file, and the release notes and `source-watch.txt` say which. A
state that fails twice is left out and named in the notes.
`keep-caches.yml` reads the build's caches once a week so GitHub keeps
them between monthly runs.

`crawl.yml` runs on the 24th. It reads the registers that only offer a
search page and take hours (state food inspection lookups, one state a
job) and leaves their files in the same cache, where the build on the 1st
picks them up.

## Output

`data/out/core-<region>.parquet`, `data/out/places-<region>.parquet` and
`data/out/manifest-<region>.json`. See `SPEC.md` for the columns, the
matching rules and their measured accuracy, the status rules, and the rules
that were tried and thrown out.

Reading a box out of a published file:

```sql
select id, name, status, status_date, status_source
from 'places-kentucky.parquet'
where lat between 38.0 and 38.1 and lng between -84.6 and -84.4;
```

## Licenses

Copyleft throughout.

- **Code**: GNU Affero General Public License, version 3 or later. See
  `LICENSE`.
- **Data**: both published files are under the Open Database License 1.0.
  If you publish a database built from them, it has to be under the ODbL
  too. The full file has to be, because it contains OpenStreetMap data. The
  core file is built from permissive inputs only and is placed under the
  ODbL by choice.

Credit it as:

    Vela Almanac, (c) its contributors. Open Database License 1.0.
    https://github.com/PimpinPumpkin/vela-almanac

That line and the source notices in `NOTICE` must accompany any copy of the
data or any database built from it. Each manifest carries the same credit. Per-source terms are in
`SOURCES.md` and `SPEC.md` section 8.
