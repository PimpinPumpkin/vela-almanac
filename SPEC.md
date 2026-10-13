# Vela Almanac spec

Version 0.1. This describes what the code in this repo does today. Where a
choice is still open it says so.

## 1. What a place is

One row per physical place a person could walk into or stand in front of: a
shop, a restaurant, a bank branch, a school, a park, a monument. Not a
machine or a box (ATMs, bike share docks, parcel lockers, charging points,
bus stops), and not an agent counter inside another store.

## 2. Layers and build order

The build order is fixed by licensing (section 8), not by convenience.

1. **Overture places** is the spine. Duplicate listings inside Overture are
   merged first (section 6), then every remaining row is a place.
2. **AllThePlaces** rows (brand lineage only) join the Overture place they
   match, or become new places.
3. Evidence that does not come from OSM is attached. The result is the
   **core layer**.
   Open storefront rows from registers that matched nothing are added as
   places here too (section 6).
4. **OpenStreetMap** named features join the core place they match, or become
   new places. OSM evidence is attached. The result is the **full layer**.

Nothing made in steps 1 to 3 reads OSM data. A place keeps the same id in
both layers.

## 3. Place schema

Both layers have the same columns.

| column | type | notes |
| --- | --- | --- |
| id | string | stable id, section 4 |
| name | string | from the anchor source |
| category | string | The source's own term: an Overture taxonomy term, an OSM style `key=value` for AllThePlaces and OSM rows, or a coarse word for places minted from registers. |
| category_group | string | One of Overture's thirteen top-level groups (food_and_drink, shopping, health_care, services_and_business, and so on), for every row whatever its source. `sql/groups.sql` maps OSM tags and register categories onto them. Null when the source gave no category. |
| category_subgroup | string | the second level of the same vocabulary, about 110 values such as `restaurant`, `casual_eatery`, `financial_service`, `personal_or_beauty_service`, `vehicle_service`. Overture's own for Overture rows, mapped from the commonest tags for the rest (`sql/groups.sql`). Null where neither gives one: 8% of rows in the DC box |
| brand, brand_wikidata | string | |
| address, city, region, postcode | string | address is the street line |
| phone, website | string | |
| opening_hours | string | in OpenStreetMap's `opening_hours` syntax, null when no source has them |
| hours_source | string | `atp` (read from the brand's own store page by AllThePlaces) or `osm` (full layer only) |
| hours_date | date | when that source last collected or edited the record |
| status | string | open, closed or unknown, section 7 |
| status_date | date | date of the evidence that decided the status |
| status_source | string | source of that evidence |
| opened_date | date | the day this business opened at this address, where a register matched to the place says so: a certificate of occupancy, a license's first issue, a first day of sales. The earliest among the matched records. Never inferred, and null for most places. A shop older than its current license shows the license's day; a January 1 date is read as "year only" and left out |
| opened_source | string | the register that gave that day |
| open_score | double | rough chance the place is open on the build date, 0 to 1, section 7 |
| overture_sources | list of string | the sources Overture itself took the place from (`meta`, `microsoft`, `foursquare`, `brightquery`, ...), null for a place Overture does not have |
| openpois_conf | double | OpenPOIs' confidence that the place exists and is open, full layer only, null when OpenPOIs does not list it |
| missing_license | boolean | true for a bar in a state with a complete license list when no active license matched it. Null where the question does not apply. Section 7. |
| overture_status | string | Overture's own operating_status, carried as is. It has no date and does not feed status. |
| sources | list of {source, id} | every source row this place was built from |
| licenses | list of string | licenses of the inputs that touched the row, for credit. It is not the row's own license: every row is part of this database and is under the ODbL, whatever its inputs were |
| evidence | list of {source, source_id, state, date, rule, dist_m} | every evidence record, newest first |
| lat, lng | double | plain columns so row group statistics work |
| geometry | point | GeoParquet, WGS 84 |

Attributes come from the anchor source. Gaps (phone, website, brand, address)
are filled from one matched AllThePlaces row, then one matched OSM row.

## 4. Stable ids

An id is the id of the source row the place is anchored on, with a prefix:

- `ovt:<Overture id>` for every place with an Overture row. Overture ids
  (GERS) are stable across Overture releases.
- `atp:<spider>/<ref>` for a place only AllThePlaces has. `ref` is the
  chain's own store number.
- `osm:<n|w|r><OSM id>` for a place only OSM has.
- `alm:<source>/<source_id>` for a place minted from a register row
  (section 6).

Nothing is renumbered between builds, so a reader can diff two monthly files
on `id`. When Overture listings are merged as duplicates, the smallest id of
the group is the place id and the others stay in `sources`.

Measured on Overture alone, District of Columbia box, release 2026-08-19.0
against 2026-09-23.1: 76,147 of 78,098 ids carried over (97.5%), 1,951
disappeared, 18,041 were new.

Known gap: when a place that was `atp:` or `osm:` last month gains an
Overture match this month, its id becomes the `ovt:` one. The old id is
still in the row's `sources`, so a reader can follow the change. If this
churn turns out to matter, the fix is for the build to read the previous
file and keep the old id. It is not built because the churn has not been
measured; the second monthly build will measure it.

## 5. Evidence format

Every adapter writes one CSV with exactly these columns:

| column | meaning |
| --- | --- |
| source | adapter and list, for example `fdic_history` |
| source_id | the register's own id for the record |
| name | the name the public would see on the building |
| address | street line, city, state and ZIP in one string, street number first |
| lat, lng | WGS 84. May be blank when the address ends in a ZIP code; the record is then matched by address. |
| state | `open` or `closed` |
| date | ISO date. For open: the day the source says the place was operating. For closed: the day it closed. |

Rules for adapters:

- One file per source in `adapters/`, no shared state, standard library only.
- One current state per `source_id`. If the register has a history, emit the
  newest state.
- Rows with no date or no name, or with neither a position nor a ZIP code,
  are dropped and counted.
- A US register with addresses but no positions can ask for them:
  `out.close(geocode=True)` sends the addresses to the Census Bureau's
  batch geocoder and caches every answer. It places about 9 in 10. A
  geocoded point sits on the street, often 50 to 100 m from the door, so
  these registers match by house number but do not mint places or drive
  the missing-license flag.
- A register that says when a business opened (a certificate of occupancy,
  a license's first issue, a first day of sales) passes it as
  `out.row(..., since=day)`. It is written to a file of its own,
  `since/<source>.csv` (source, source_id, since), and becomes the place's
  `opened_date`. It never changes what the row itself says. Read so far:
  Fort Worth certificates, Texas sales tax outlets, Texas and New York
  liquor licenses, New Orleans, New York City, Los Angeles and San
  Francisco business rolls.
- If the register uses a legal name the public never sees, the adapter maps
  it (see `TRADE_NAMES` in `adapters/fdic.py`). The matcher stays generic.
- A register that only publishes its last few weeks can be held instead of
  used: `Writer(name, held=True)` writes to `data/cache/held/` and keeps
  the rows from earlier runs. The build does not read held files. The
  scheduled build carries them from one release to the next as
  `held.tar.gz`.
- The same held folder gets `vanished.csv`: every open record that was in a
  register file last run and is not in it this run, dated the day it was
  first missed (`tools/source_watch.py`). Held until it has been tested
  like any other closure signal.
- Some registers offer a search form and no file. An adapter may page
  through such a form when the form can list the whole register in a
  bounded number of requests (by county or by license type), and only
  under these rules, which `lib/crawl.py` enforces where it can: read the
  site's robots.txt first and stay out of anything it disallows; send the
  project User-Agent; wait at least two seconds between requests; never
  work around a block, a challenge page or a CAPTCHA; read only what the
  form shows the public. A site that says no is written down in
  FOLLOWUPS.md and left alone. One exception exists: the owner may decide,
  one site at a time, to read a public register whose robots.txt says
  otherwise (`Site(..., robots=False)`), and the decision and its reason
  go in SOURCES.md. A 403 or a CAPTCHA is never worked around.
- A record is evidence only if it says something about the premises. A
  record that only says something about paperwork is not (see SNAP end dates
  in section 9).

Signals that arrive by id rather than by position (Foursquare closing dates,
OSM tags, AllThePlaces rows) use the same evidence shape inside the build
but skip the matcher.

## 6. Entity matching

One matcher, `match_pairs` in `sql/lib.sql`, is used for AllThePlaces to
Overture, OSM to core, and evidence to places.

**Name.** Lowercase, strip accents and punctuation, `&` becomes `and`. Then
drop text in brackets, legal words (the, inc, llc, llp, pllc, ltd, corp,
company, co, national association, na, branch; pc and apc at the end of a
name) and trailing store numbers. Every spelling of
"credit union" (FCU, Federal Credit Union) becomes one word, so a credit
union matches itself and not the agency it is named after.

**House number.** The leading digits of the street line.

**Name similarity.**

| value | when |
| --- | --- |
| 1.0 | normalized names are identical |
| 0.9 | the shorter name, at least 4 letters, is the leading words of the longer: "giant" and "giant food" |
| Jaro-Winkler | otherwise, on the names with spaces removed. Counts only at 0.95 or more. |
| 0 | one side is an ATM and the other is not |

**Rules.** A pair matches under the first rule it passes.

| rule | house numbers | distance | name |
| --- | --- | --- | --- |
| number | equal | up to 250 m | 1.0, 0.9, or Jaro-Winkler from 0.95 |
| near | missing on one or both sides | up to 60 m | same |
| spot | present and different | up to 30 m | 1.0 only |

| address | equal | none: same ZIP code and same first word of the street name | same as number |

The `address` rule is only for records that have no position (CMS, NPPES,
IRS). Chains repeat names, so the name alone never matches. Two branches of a
chain across the street from each other have different house numbers and
fail `number`; they are more than 30 m apart or fail `spot`.

**Who gets the match.**

- Base merge: each incoming row joins the single best place (rule order
  number, near, spot; then similarity; then distance). A place can absorb
  several rows.
- Evidence: a `number` match applies to every place that passes, because
  the base has duplicate listings of the same shop. Without a `number`
  match, only the best single place gets the record.

**Duplicates inside Overture.** Two cases merge. The smallest id of a
group is the place id; the member table lists the others with the rule
that merged them.

- `duplicate`: the matcher run on Overture against itself, strictest case
  only: same house number, within 250 m, identical normalized name. In the
  District of Columbia box that merges 319 of 94,188 rows; 40 merged pairs
  were read and all 40 are the same business (often a store and the money
  transfer counter inside it). Looser name rules are rejected, section 9.
- `fuel lot`: two fuel stations with the same house number within 60 m,
  whatever they are called. Overture keeps a row for each brand a
  forecourt has had ("Shell", "BP" and "Bladensburg Amoco" at one
  address). 40 pairs were read in each of the DC, Sacramento and Houston
  boxes: 38, 40 and 40 are one lot, the rest a repair shop listed as a
  station on the same lot. It merges 137 of 440 fuel rows in the DC box,
  114 of 494 in Sacramento and 402 of 1,598 in Houston, and the share of
  fuel stations with a status goes from 49% to 65%, 53% to 62% and 50% to
  62%.

A merged fuel lot takes the name of one listing: not one named by its
street address, then the one the brand's own locator (AllThePlaces) lists
there, then the one Overture is surest of. A locator decides about half the
lots. Checked against OSM, which the core layer may not read: where OSM
names the station, the kept name agrees on 240 lots and a dropped name
would have on 61, and 31 of those 61 are the locator disagreeing with OSM.
In the full layer, a lot that no locator spoke for takes OSM's name and
brand when an OSM fuel feature on it goes by one of the lot's other names
(8 of 105 merged lots in the DC box, 18 of 335 in Houston).
The other names stay as aliases for matching, so a register or locator
that still uses one finds the place and does not mint a second. A
Foursquare closing date or an OSM history event recorded under a dropped
name does not close the place.

**Places added from a register.** Some registers list the storefront
itself: FDIC branches, SNAP authorized stores, DC and New York licensed
premises, New York City and Chicago inspected food businesses, New York
food stores, Delaware and
Sacramento County inspected food establishments, Jefferson County,
Kentucky licensed premises, New York lottery retailers, Florida lottery
retailers (41 added in the Jacksonville box, 39 of 40 read a store of its
own: fuel stations, supermarkets and corner stores), the liquor
license lists of Nashville, Detroit, Baltimore, Minneapolis and
Montgomery County, Maryland (each read in its own city: 36 of 40, 38 of
40, 38 of 40, 23 of 25 and 22 of 23 a storefront of its own; 26 of the
154 Baltimore adds then found an OSM feature), the retail license kinds
of Phoenix and Anchorage (38 of 40 and 28 of 31, once producers,
wholesalers, clubs and event licenses were split into sources of their
own that never add a place), and Colorado
tobacco retailers (held to the stricter duplicate tests below, because a
station's shop is often licensed under a name the map does not use: 82
added in the Denver box, 34 of 40 read before those tests were a
storefront of its own and 4 of the 6 misses were a fuel station already
listed under its brand, which the tests now catch). A row from one
of them becomes a new place when it is open, has a position, matched no
place, and no listed place within 80 m has a similar name (leading words,
Jaro-Winkler 0.7 or more, or same house number and same first word), and
no place within 200 m has the same name. A register name that ends in a
legal form (Inc, Corp, LLC) is a company, not a sign, and does not become
a place; the trade name after "dba" is used when there is one. A lottery
agent licensed in a person's name is never added: only a name that reads
as a shop is, and newsstands, which carry their holder's name, are left
out (of 40 read after that rule, the rest were delis, groceries,
pharmacies and liquor stores). The place gets the register's name in title case, the
register row as its first evidence, and a category: the kind its name
states in plain words ("Richards Liquors" is `shop=alcohol`, "Murphy
Chevron" `amenity=fuel`, "Last Call Sports Bar" `amenity=bar`), or else
the register's coarse kind (bank, grocery_or_convenience_store,
licensed_premises). In the Houston box 774 of 1,358 added places get a
kind from their name.

A certificate of occupancy is a different kind of register: a city issues
one when a business moves into a space, so it is a list of openings, each
with its day, and the freshest source here. Its occupant field is free
text. A place is added only from an occupancy certificate (not from one
that closes a building permit) whose name carries a word a shop puts on
its sign and something besides (`reads_as_shop` in `sql/lib.sql`):
"Cowser Tire" and "Las Tequileras Cantina", not "Restaurant Taqueria",
"Tobias Place Bldg 7" or a person's name. The register's coarse kind is
`commercial_premises`, and the name is read for a trade more widely than
for a license (salon, tires, car lot, dentist, clinic, gym, laundry).

The same test opens a second kind of register: a city's business license
or business tax roll. Every one tried without the test failed, because a
roll lists every registered business and most have no door (section 9).
Behind the test, and with apartments, machines inside a store ("Cardtronics
@ Target"), mobile businesses and unit numbers written as "#1" left out,
eight rolls pass a reading of 40.

Most rolls still fail it: a jeweler, a baker or a barber working from a
house has a shop's name. Those are held to more (`commercial_roll`): no
unit or suite in the address, no name of one person's trade ("Nails by
Roni", pet sitting, detailing, rentals), and a listed business that is not
itself a home trade within 40 m, since a house has no shop beside it. That
halves what a roll adds and twelve more pass; nine fail both ways
(section 9). The table below has each reading.

Food permit lists are held to the same and to one thing more
(`food_roll`). A food permit names kitchens, counters and outlets as well
as shops, so a name with an outlet or department in it ("Pittsburgh Zoo /
Jambo Grill", "Safeway #2968 - Grocery"), a snack bar, a prep or banquet
kitchen, a cafeteria, a cart, or a King County food truck's plate number
("KC112") adds nothing, nor does a row at the door of a supermarket,
stadium, campus or hospital. Any roll row with no house number is left
out, and so are two or more new permits at one door: those are trucks
at their commissary, stalls in a market hall or the departments of one
store. Twelve food lists pass and eight do not.

In the District of Columbia box this adds about 450 places to 94,000.
Forty were read against their most similar neighbor: 39 were new, 1 was a
second listing of a place under a longer name (that case is now caught).
About one in five then picked up an OSM feature in the full layer, which
is independent confirmation that the place exists.

**State files.** A state's build is cut to the state's outline, places
and register rows alike, and a register row whose own address names
another state is dropped wherever its point falls. Until 2026-10-12 only
places were cut, so a shop in Manhattan that a New York register listed
was added to New Jersey's file as well (New Jersey's box covers
Manhattan): 67,000 added places were in more than one state's file in
the build of that day. A place within about 5 km of a state line whose
address names the neighboring state belongs to that neighbor only; 13,000
such places were in both files until the same day.

**Registers that give only an address.** A geocoder's guess along the
street is good enough to match a place and not good enough to make one.
A row from an address-only register is added only when its house number,
street and ZIP are an address point (see below), and it is placed on
that point. Such a register is held to more: no neighbor within
80 m may share a real word with it or be its initials ("Airport Rd
Chevron" beside "Chevron", "Kentucky Fried Chicken" beside "KFC"); it may
not sit at the door of a fuel station, supermarket, stadium, campus or
hospital; and names of counters inside stores, institutions, food service
contractors and businesses at an apartment are left out. Seventeen state registers
are allowed: liquor licenses, because a licensed premises is a storefront
by definition, and one list each of tobacco retailers, child care
centers, pharmacies and lodging:

| register | box | added | read | then found in OSM |
| --- | --- | --- | --- | --- |
| Texas TABC | Houston | 562 | 38 of 40 a storefront of its own | 40 |
| Texas tobacco retailers (Comptroller) | Houston | 514 | 38 of 40: food marts, smoke shops and liquor stores | 37 |
| Washington LCB | Seattle | 128 | 37 of 40; the others are wineries at a home address | 42 |
| North Carolina ABC | Charlotte | 94 | 35 of 40 after contractors and home addresses were filtered out; the misses are a wine distributor's office and second listings under a shorter name | 24 |
| Kentucky ABC | whole state | 383 | 36 of 40: rural groceries, smoke shops, bars; the misses are second listings under a respelled name (now caught) and a lodge listed under its order's name | 25 |
| California ABC | Sacramento | 133 | 36 of 40 before rows with no trade name were split off; the misses were a license in its holder's own name (those rows are now a separate source that never adds a place), a contractor at an auditorium, a fuel station's operating company and two home wineries | 11 |
| Florida ABT | Jacksonville | 153 | 38 of 40: food stores, smoke shops, lounges; the others are a delivery warehouse and a retirement community | 5 |
| Texas licensed child care centers (HHSC) | Houston | 42 | 38 of 40; the others are after-school programs run inside a school | 2 |
| Texas pharmacies (Board of Pharmacy) | Houston | 40 | 37 of 40: independent, specialty and in-store pharmacies | 3 |
| Fort Worth certificates of occupancy, occupancy kind, names that read as a shop | Fort Worth | 215 | 40 of 40 were a business with a door, each with the day it moved in: taquerias, food marts, barbers, smoke shops, auto lots, a laundry. Two stand where an older listing under another name is likely the shop they replaced. 65 were certified in 2026 | 3 |
| Miami-Dade local business tax receipts, names that read as a shop | Miami | 410 | First reading 35 of 40: the misses were two cash machines inside a store, a lawyer named Grill, a shop registered at an apartment and one name that says nothing. Machines, in-store counters, apartments and unit numbers written as "#1" are now left out; of the 36 that remain 34 were a shop | 3 |
| Long Beach business licenses (not home based, inside the city), names that read as a shop | Long Beach | 240 | 37 of 40: markets, liquor stores, barbers, car lots, repair shops; two are fuel stations listed under the brand on the canopy and the operator's name on the license | 3 |
| Denver business licenses (shop-front license kinds only), names that read as a shop | Denver | 115 | 38 of 40: liquor stores, taverns, taquerias, smoke shops, cleaners; one steakhouse is listed twice under two spellings | 10 |
| Las Vegas business licenses, names that read as a shop | Las Vegas | 494 | 38 of 40: barbers, nail salons, diners, auto lots, mall stores; the others are a resort's water park desk and a pharmacy counter | 10 |
| Chicago business licenses, names that read as a shop | Chicago | 516 | 37 of 40: cleaners, cafes, food marts, tattoo shops, taverns; the others are two food trucks at their commissary ("on wheels" is now left out) and a drug counter inside a supermarket | 56 |
| District of Columbia basic business licenses, names that read as a shop | District of Columbia | 224 | 35 of 38 after vending decals were left out: markets, smoke shops, car lots, salons, liquor stores; the others are a bakery listed twice and a jeweler's studio | 30 |
| New York City consumer licenses, names that read as a shop | New York City | 34 | 31 of the 34: delis, jewelers, repair shops, a pharmacy; three carry a store number where the name should be | 6 |
| Detroit business licenses, names that read as a shop | Detroit | 15 | 16 of the 17 first added: repair shops, a liquor store, a smoke shop; the other was a parking lot's plate number (now left out) | 0 |
| Seattle business licenses, held to more (a listed business within 40 m) | Seattle | 265 | 38 of 40: barbers, cafes, mini marts, a tire shop, taverns; the others are a parking lot and a trainer. Without the neighbor test 28 of 40 | 55 |
| Sacramento business operations tax, held to more | Sacramento | 241 | 37 of 40: smoke shops, salons, car lots, bakeries, mall stores | 10 |
| Sacramento County business licenses, held to more | Sacramento | 276 | 37 of 40: markets, tire shops, barbers, a pharmacy; the others are barbers renting a chair in a salon suite | 7 |
| Anaheim business licenses, held to more | Anaheim | 166 | 37 of 40: salons, cafes, repair shops; the others are a pension fund's properties, a store number with no name and a fuel station under its operator's name | 5 |
| Broward County business tax receipts, held to more | Fort Lauderdale | 237 | 37 of 40; the others are a home kitchen and a sushi counter inside a grocery | 5 |
| Tucson business licenses (no home occupations), held to more | Tucson | 333 | 37 of 40; the others are a nail technician and a supermarket that changed banner | 12 |
| New Orleans occupational licenses, held to more | New Orleans | 191 | 37 of 40; the others are a mall listed as a shop and a vending account | 11 |
| Baton Rouge business licenses, held to more | Baton Rouge | 226 | 36 of 40: tire shops, salons, smoke shops, mall stores; the others are a store number with no name, a sushi counter inside a grocery and two shops on residential streets | 8 |
| Delaware business licenses, held to more | whole state | 299 | 37 of 40: pizzerias, liquor stores, barbers, markets; the others are a car dealer's number and two home businesses | 4 |
| Los Angeles County business licenses (unincorporated areas), held to more | Los Angeles | 49 | 37 of 40: mini markets, body shops, bars; the others are one bar listed twice and a taco stand at a house | 0 |
| Glendale, Arizona, business licenses, held to more | Phoenix | 45 | 37 of 40: barbers, smoke shops, carnicerias, auto shops | 4 |
| Texas sales tax outlets (Comptroller), held to more, placed on address points | Houston | 1,402 | 72 of 80 in two readings: food marts, taquerias, tire shops, smoke shops, salons, car lots. The misses are chain stores under a store number ("HEB Food Store #439"), a stadium stand, a person and two shops on residential streets. Refused on 2026-10-12 without these tests: 11,073 would have been added, 22 of 50 a storefront | 42 |
| California salon and repair shop licenses (DCA), held to more | Sacramento | 26 and 28 | 24 of the 26 salons and 27 of the 28 repair shops | 1 |
| New York repair shops and dealers (DMV), held to more | Buffalo | 23 | all 23: body shops, repair shops, used car lots. Turned off on 2026-10-12 when rows in a person's name became places; none can now | 2 |
| Florida salon licenses (DBPR), held to more | Miami | 17 | 16 of the 17 | 0 |
| Texas salon licenses (TDLR) and New York salon licenses, held to more | Houston, Buffalo | 153 and 30 | 38 of 40 and 27 of 30, counting a stylist's own salon inside a salon-suites building as a place. The owner's rule of 2026-10-13: where it is unclear whether something is a place, do what Google Maps does, and Google lists suite salons one by one. Counted the other way they were 33 and 25 and stayed off | 1 and 4 |
| Los Angeles County restaurant and market inventory, held to more as a food list | Los Angeles | 469 | 37 of 40: mini markets, liquor stores, cafes, karaoke bars; the others are two courthouse snack bars (now left out) and a nutrition club | 16 |
| Alameda County restaurant inspections, as a food list | Oakland | 67 | 36 of 40: cafes, markets, groceries; the others are a recreation center stand, a studio's staff cafe and a shared kitchen | 24 |
| King County food facilities, as a food list | Seattle | 82 | 37 of 40 once food trucks, listed by plate number, were left out | 16 |
| Detroit restaurant establishments, as a food list | Detroit | 218 | 36 of 40: bars, pizzerias, taquerias, soul food; two were a KFC under its long name beside "KFC" (now caught) | 11 |
| Allegheny County food facilities, as a food list | Pittsburgh | 66 | 37 of 40 once "venue / outlet" names were left out: corner markets, cafes, smoke shops | 8 |
| Columbus food licenses, as a food list | Columbus | 87 | 36 of 40: markets, bars, cafes; the others are airport stands and two company cafeterias (cafeterias now left out) | 7 |
| Riverside County food facilities, as a food list | Riverside | 33 | 34 of the 37 that remain after snack bars were left out | 8 |
| San Diego County food permits, as a food list, placed on address points | San Diego | 43 | 34 of 36 once hotel outlets and prep kitchens were left out | 4 |
| Michigan food establishments (MDARD), as a food list | Detroit | 61 | 36 of 40: chicken and fish shops, pizzerias, coffee houses; the others are two hospital cafes, a call center's cafe and a gym | 4 |
| Milwaukee food licenses, as a food list | Milwaukee | 95 | 36 of 40 once doors with two new permits were left out: taquerias, mini marts, cafes | 13 |
| Minneapolis food licenses, as a food list | Minneapolis | 30 | 28 of the 30; a mall's 13 numbered stalls went with the one-door rule | 5 |
| South Carolina food permits, as a food list | Charleston | about 43 | 35 of 40 before store departments written with a slash were left out, 34 of 36 after | 5 |
| Texas dry cleaner registrations (TCEQ) | Houston | 16 | 17 of the 19 first added were a cleaner the map lacked; the other two were a listed cleaner under a new name at the same door, and a dry cleaner registered at the door of a listed dry cleaner or laundry is now taken to be that shop. Too few to read 40 | 3 |
| Florida lodging licenses (DBPR) | Jacksonville and Miami | 19 | 16 of the 19 the two boxes hold: hotels and motels; too few to read 40 | 3 |
| Colorado liquor licenses, placed by the state's alcohol outlet points | Denver | 160 | 37 of 40: restaurants, bars, liquor stores; the others are big-box stores the map may hold under a far-off point, and a members' club | 17 |
| Nebraska LCC, premises classes only | Omaha | 47 | 38 of 40: bars, markets, liquor stores; the others are an event hall and a delivery warehouse | 3 |
| Oregon OLCC | Portland | 43 | 38 of 40: restaurants, bars, bottle shops; 13 then found an OSM feature | 13 |
| Idaho State Police ABC | Boise | 43 | 37 of 40; the misses are wineries at a home address | 14 |
| Texas lottery retailers | Houston | 41 | 40 of 40: food marts and corner stores | 5 |
| Kansas ABC | Wichita | 26 | 24 of 26; the others are a lodge already listed under its order's name and a one-day event license | 1 |
| New Jersey ABC | Newark | 25 | 29 of 31 read before placeholder names ("NONE", "Not Available") and double listings were removed | 2 |
| Maine BABLO | Portland | 29 | 27 of 29; the others are a delivery warehouse and a hotel | 1 |

A row can also take the point a second public layer gives the very
same record (a pin): Colorado's health department publishes a point for
each liquor license by license number, and only those it marks as placed
on the address are used.

Address points are every point in Overture's address theme: the National
Address Database, county files public domain under California and
Florida law, Ada County, Idaho (CC BY), and files Overture marks
proprietary (Colorado, Oregon, Mississippi, New York City, Los Angeles
County), which the owner decided on 2026-10-12 to use for positions.
Oklahoma and Wisconsin have few points, so registers there add little. What was tried and refused is in section 9.

**Join shape.** Candidates come from a grid hash join: cells are 0.004
degrees of latitude by 0.008 of longitude, one side is copied into its nine
neighbor cells, and the join is an equality on the cell. No distance
predicate, OR, or correlated subquery is used to find candidates.

**Tests.** `tests/match_test.sql` holds 25 invented pairs, plus 5 for the address rule, one per case the
rules are meant to accept or refuse. Run `duckdb < tests/match_test.sql`.

**Measured.** 40 matched pairs per rule were read in the District of
Columbia box, fewer where a rule has fewer than 40. "Right" means the two
rows are the same place.

| match | rule | right | notes |
| --- | --- | --- | --- |
| AllThePlaces to Overture | number | 39 of 40 | the miss joined a hospital department to its parent listing |
| | near | 38 of 40 | both misses are library rows listed under the parent institution's name |
| | spot | 12 of 14 | one store that moved across the street, one doubtful pair |
| OSM to core | number | 40 of 40 | |
| | near | 38 of 40 | both misses are part and whole (a dog park in a park, a clinic in a health department) |
| | spot | 40 of 40 | |
| FDIC closings to places | number | 40 of 40 (DC), 38 of 40 (Sacramento) | Sacramento misses: an office tower named after the bank, and a wealth advisor listing |
| | near, spot | 6 of 6 | |
| FDIC open branches | number | 39 of 40 | the miss is a loan officer's listing at the branch |
| | near, spot | 12 of 12 | |
| SNAP authorized stores | number | 40 of 40 | |
| | near, spot | 19 of 19 | |
| NCES schools | number | 39 of 40 | the miss is a school's aquatic center |
| | near | 12 of 12 | |
| CMS hospitals | address | 10 of 15 | all 10 hospitals are right; the other 5 rows are the hospital's gift shop, emergency room or a department sharing its name and address |
| NPPES organizations | address | 37 of 40 | the 3 misses are hospital departments |
| IRS exempt organizations | address | 36 of 40 | the 4 misses are a related body at the same address, such as a foundation arm |
| California alcohol licenses | number | 25 of 25 (Sacramento) | positions from the Census geocoder; finds a place for 61% of licenses, up from 25% by address alone |
| Texas alcohol licenses | number | 40 of 40 (Houston) | geocoded; finds a place for 40% of licenses |
| DC alcohol licenses, active | number | 40 of 40 | finds a place for 77% of licenses |
| | spot | 20 of 20 | |
| DC alcohol license cancellations | number | 40 of 40 | |
| NCUA credit union offices | address | 38 of 40 | both misses are a church's credit union landing on the church |
| EPA fuel tank sites | all | 30 of 30 (Kentucky) | |
| New York alcohol licenses | number | 40 of 40 (New York City) | |
| | spot | 20 of 20 | mostly Queens addresses, where "30-08" and "3008" are the same door |
| | near | 11 of 12 | the miss is a hotel landing on a place named only "New York" |
| New York retail food store inspections | number | 15 of 15 (New York City) | |
| New York City DCWP licensed businesses | number | 15 of 15 | |
| Delaware food inspections | number | 14 of 15 (Delaware) | the miss is a school's wellness center taking the school's inspection |
| Montgomery County food inspections | number | 15 of 15 (the Maryland part of the DC box) | geocoded |
| Sacramento business tax accounts | number | 15 of 15 (Sacramento) | geocoded |
| Sacramento County food inspections | number | 15 of 15 (Sacramento) | |
| Louisville food inspections | number | 15 of 15 (Kentucky) | geocoded |
| Jefferson County, Kentucky alcohol licenses | number | 15 of 15 (Kentucky) | |
| DC Basic Business Licenses | number | 25 of 25 | geocoded; only the licenses that carry a trade name and are not housing |
| Chicago business licenses, live and cancelled | number | 40 of 40 | live licenses matched 10,100 places in the box |
| Philadelphia business licenses | number | 20 of 20 | company-held food, vehicle and child care licenses only |
| Seattle business licenses | number | 40 of 40 | storefront industry codes only; 6,200 places in a Seattle box gained a status |
| Denver business licenses | number | 40 of 40 | food, liquor, tobacco, marijuana, repair and lodging licenses, geocoded |
| New York tobacco retailers | number | 40 of 40 | registrant names, so only a quarter find a place |
| Pennsylvania tobacco licenses | number | 39 of 40 | the miss is a pharmacy counter taking the store's license |
| Texas tobacco retailers | number | 40 of 40 (Houston) | geocoded |
| Connecticut state licenses | number | 40 of 40 (Bridgeport) | liquor, bakeries, pharmacies, lottery agents and similar, geocoded |
| Connecticut dealers and repairers | number | 40 of 40 (Bridgeport) | one row per trading name of a license |
| New Orleans occupational licenses | number | 40 of 40 | home, driver and street vendor trades left out |
| Washington vehicle dealers | number | 40 of 40 (Seattle) | geocoded |
| Washington child care centers | number | 40 of 40 (Seattle) | geocoded |
| Colorado child care centers | number | 40 of 40 (Denver) | family homes left out, geocoded |
| Florida salons and barbershops | number | 39 of 40 (Jacksonville) | a third of licenses find a place; geocoded |
| Florida veterinary premises | number | 40 of 40 (Jacksonville) | |
| Florida hotels and motels | number | 40 of 40 (Jacksonville) | |
| Florida restaurant licenses | number | 40 of 40 (Jacksonville) | |
| New York dispensaries | number | 40 of 40 | only shops the state marks as operating |
| New York State food inspections | number | 39 of 40 (Buffalo box, Niagara County rows) | the miss is a place whose own name is only the city's |
| Boston food establishment licenses | number | 29 of 30 | the miss is a coffee kiosk taking the department store around it |
| Boston food inspections | number | 30 of 30 | |
| Boston Licensing Board licenses | number | 30 of 30 | geocoded |
| Washington liquor licenses | number | 30 of 30 (Seattle) | geocoded |
| New Jersey retail liquor licenses | number | 30 of 30 (Newark) | unused licenses left out; geocoded |
| Wisconsin retail alcohol licenses | number | 30 of 30 (Milwaukee) | dated by each record's own update; geocoded |
| Nebraska liquor licenses | number | 30 of 30 (Omaha) | geocoded |
| Maine liquor licenses | number | 30 of 30 (Portland) | geocoded |
| Idaho retail alcohol licenses | number | 30 of 30 (Boise) | geocoded |
| Arkansas alcohol permits | number | 30 of 30 (Little Rock) | geocoded |
| Oklahoma alcohol licenses | number | 30 of 30 (Oklahoma City) | geocoded |
| Las Vegas business licenses | number | 30 of 30 | home, mobile and office-only trades left out; geocoded |
| Omaha restaurant inspections | number | 30 of 30 |  |
| Minneapolis food inspections | number | 30 of 30 |  |
| Minneapolis liquor licenses | number | 30 of 30 |  |
| Baltimore liquor licenses | number | 30 of 30 | dated by the start of the license year; geocoded |
| Columbus restaurant and market inspections | number | 30 of 30 |  |
| Michigan food service licenses | number | 30 of 30 (Detroit) | |
| South Carolina food inspections | number | 29 of 30 (Charleston) | the miss has the same number on the cross street |
| Minnesota retail food handlers | number | 30 of 30 (Minneapolis) | geocoded |
| California salons and barber shops | number | 30 of 30 (Sacramento) | geocoded |
| California auto repair and smog stations | number | 30 of 30 (Sacramento) | geocoded |
| California retail pharmacies | number | 30 of 30 (Sacramento) | geocoded |
| Virginia salons, barber shops and parlors | number | 29 of 30 (DC box, Virginia side) | the miss is a salon inside a retirement home taking the home; geocoded |
| Texas community pharmacies | number | 30 of 30 (Houston) | geocoded |
| Ohio pharmacies | number | 30 of 30 (Columbus) | geocoded |
| HRSA health center sites | number | 25 of 25 (DC box) |  |
| Child care centers, ten states | number | 20 of 20 in each of AZ, CA, DE, MA, MI, MN, NJ, TN, VT, WI | a program inside a school matches the school |
| Phoenix, Nashville, Anchorage and Huntsville alcohol licenses; Detroit business and liquor licenses; Sioux Falls food sites | number | 25 of 25 each | |
| Milwaukee food and alcohol licenses | number | 49 of 50 | the miss is a campus library taking the college's bakery license |
| North Carolina alcohol permits (search form) | number | 29 of 30 (Charlotte) | the miss is a pharmacy counter taking the grocery's permit; geocoded |
| Kentucky alcohol licenses (report page) | number | 29 of 30 (Kentucky) | geocoded |
| Kansas alcohol licenses (search form) | number | 30 of 30 (Wichita) | geocoded |
| Pennsylvania liquor licenses | number | 30 of 30 (Philadelphia) | premises names are often the company's, so a third find a place; geocoded |
| Tennessee retail food stores (paged list) | number | 29 of 30 (Nashville) | geocoded |
| Vermont and Kansas food inspections (shared Food Safety system) | number | 30 of 30 each (Burlington, Wichita) | the same reader serves six more states, 112,000 establishments in all; geocoded |
| North Carolina inspections (county search pages) | number | 30 of 30 (Charlotte) | 38,000 establishments; geocoded |
| Mississippi food facility inspections (date export) | number, address | 42 of 45 (Jackson) | the doubtful three share a first word with a neighbor at the address ("Twilight" and "Twilight Kristylz"); 15,000 establishments; geocoded; independent food places in the box with a status went from 5% to 24% |
| Alabama food establishment scores (search form) | number, address | 40 of 42 (Huntsville) | the other two are a store's bakery or meat counter landing on the store's pharmacy; geocoded; independent food places in the box with a status went from 12% to 30% |
| Cambridge food establishment permits | number | 40 of 40 (Boston box) | two are a cafe inside a company or hospital landing on it |
| Montgomery County, Maryland, alcohol licensees | number, near | 40 of 40 (DC box) | 223 of the 285 licensees in the box find a place |
| New York City child care programs | number, spot | 40 of 40 (New York City) | |
| New York State child care programs | number | 39 of 40 (New York City) | the doubtful one is an after-school program landing on the same body's adult day care |
| Pennsylvania child care centers | number | 40 of 40 (Philadelphia) | geocoded |
| Texas licensed child care centers | number | 39 of 40 (Houston) | geocoded |
| Florida lottery retailers | number, near | 40 of 40 (Jacksonville) | 464 of the 738 retailers in the box find a place |
| New York lottery retailers | number, spot, near | 40 of 40 (New York City) | delis, pharmacies and newsstands; 412 of the 1,032 in the box find a place |
| New York City weights and measures tests | number | 40 of 40 (New York City) | grocers, laundromats, cleaners and fuel stations, dated by the test |
| Fort Worth certificates of occupancy | number, spot, near | 22 of 22 read (Fort Worth) | 1,337 of the 2,186 certificates in the box find a place, each with the day the business moved in |
| Southern Nevada Health District food permits | number | 40 of 40 (Las Vegas) | a casino's kitchens and bars each hold a permit and land on the restaurant or the hotel they belong to; 5,256 of the 13,783 permits in the box find a place. Never adds a place for that reason |
| Los Angeles County restaurant and market inventory | number, near | 40 of 40 (Los Angeles) | 6,133 of the 10,165 facilities in the box find a place |
| Los Angeles active businesses | number | 40 of 40 (Los Angeles) | 24,700 of the 263,000 accounts in the box find a place; places in the box with a status went from 9% to 21% |
| San Francisco registered business locations | number | 40 of 40 (San Francisco) | 19,500 of the 100,600 locations in the box find a place; places in the box with a status went from 13% to 27% |
| Miami-Dade business tax receipts | number | 40 of 40 (Miami) | places in the box with a status went from 8% to 20% |
| Broward County business tax receipts | number | 40 of 40 (Fort Lauderdale) | 8% to 20% |
| Tucson business licenses | number | 40 of 40 (Tucson) | 9% to 26% |
| Bellevue business licenses | number | 40 of 40 (Bellevue) | 11% to 21% |
| Chesapeake business licenses | number | 40 of 40 (Chesapeake) | 9% to 21% |
| Long Beach business licenses | number | 40 of 40 (Long Beach) | 12% to 17% |
| Anaheim business licenses | number | 40 of 40 (Anaheim) | 13% to 17% |
| Sacramento County business licenses | number | 40 of 40 (Sacramento) | 21% to 23%; the box already had the city's own list |
| Detroit restaurant establishments, Alameda County restaurant inspections | number | 40 of 40 each (Detroit, Oakland) | |
| Allegheny County food facility inspections | number, address | 40 of 40 (Pittsburgh) | geocoded; independent food places in the box with a status went from 33% to 42% |
| Riverside County food facilities, California licensed health facilities, Colorado tobacco retailers, Los Angeles County business licenses | number | 40 of 40 each (Riverside, Los Angeles, Denver, Los Angeles) | a store inside a fuel station finds the station through the lot's other names |
| San Diego business tax certificates | number | 40 of 40 (San Diego) | places in the box with a status went from 11% to 18% |
| Maricopa County food permits | number | 40 of 40 (Phoenix) | independent food places in the box with a status went from 15% to 36% |
| Virginia Beach business licenses | number, address | 40 of 40 (Virginia Beach) | geocoded; dated by the day each license began, so older licenses do not count as recent |
| East Baton Rouge businesses | number | 40 of 40 (Baton Rouge) | geocoded; places in the box with a status went from 8% to 24% |
| Norfolk business licenses | number | 40 of 40 (Norfolk) | places in the box with a status went from 9% to 14% |
| Berkeley business licenses | number, spot | 40 of 40 (Berkeley) | half geocoded; 15% to 20% |
| Austin, Cincinnati, Boulder County and Marin County food inspections | number | 40 of 40 each, in their own cities | stadium and hotel kitchens land on the stadium or hotel |
| Texas lottery retailers | number, address | 40 of 40 (Houston) | geocoded; a store inside a fuel station finds the station through the lot's other names |
| New Jersey private inspection facilities | number | 17 of 17 (Newark) | repair shops; one finds its fuel station through the lot's other name |
| Georgia environmental health inspections (permit feed) | number, address | 38 of 40 (Atlanta) | the other two are a kitchen inside an office or campus landing on the organization; geocoded; independent food places in the box with a status went from 14% to 26% |
| Oklahoma food service establishments (county search pages) | number, address | 40 of 40 (Oklahoma City) | the list has no dates, so rows are dated the day they are read; the detail pages of 40 establishments drawn at random showed a newest inspection within a year for 32 and within two for 38; geocoded; independent food places in the box with a status went from 6% to 33% |
| Pennsylvania retail sales licenses | number | 28 of 30 (Philadelphia) | both misses are a hospital department taking the hospital's license |
| Delaware business licenses | number | 30 of 30 (Delaware) | geocoded; took the state from 8% of places with a status to 19% |
| Texas salon and barber establishments | number | 20 of 20 (Houston) | geocoded; nail salons in the box went from 7% with a status to 52% |
| Texas sales tax locations | number | 30 of 30 (Houston) | geocoded; live permits matched 14,000 places in the box |
| New York salons and barber shops | number | 25 of 25 (New York City) | finds a place for about half |
| New York DMV repair shops and dealers | number | 20 of 20 (New York City) | finds a place for about 4 in 10; the register uses company names |
| King County (Seattle) food inspections | number | 25 of 25 | geocoded; finds a place for 61% of businesses |
| New York City restaurant inspections | number | 25 of 25 | finds a place for 75% of restaurants |
| Chicago food inspections, out of business | number | 30 of 30 | |
| Chicago food inspections, open | number | 20 of 20 | finds a place for 68% of businesses |
| Colorado alcohol licenses | number | 25 of 25 (Denver) | positions with the data or geocoded; finds a place for 67% of licenses |
| Oregon alcohol licenses | number | 20 of 20 (Portland) | geocoded; finds a place for 71% of licenses |
| Missouri alcohol licenses | number | 25 of 25 (Kansas City) | geocoded; finds a place for 55% of licenses |
| Florida alcohol licenses | number | 25 of 25 (Jacksonville) | geocoded; finds a place for 53% of licenses |
| Florida restaurant inspections | number | 30 of 30 (Jacksonville) | geocoded; finds a place for 54% of inspected restaurants |
| OSM lifecycle features to places | all | 40 of 40 (DC), 36 of 36 (Sacramento) | |

## 7. Status rules

Evidence is a list of dated open and closed records per place.

- **closed**: the place has a closed record with a date, and no open record
  dated after it. Any open record counts, whatever its source. The newest
  closed record supplies `status_date` and `status_source`.
- **open**: the newest record is open and is dated within 730 days of the
  build date.
- **unknown**: everything else. That includes places with no evidence, which
  is most of them, and places whose only evidence is an old open record.

Closed does not expire. A place closed in 2014 with nothing newer stays
closed.

A closed record that a newer open record overrode stays in `evidence`, so
the conflict is visible. Overture's confidence, update_time and
operating_status are never evidence: none carries a date of observation.

### Open score

`open_score` puts every place on one scale, including the ones with no
evidence. It is a rule of thumb with stated parts, not a fitted model.

| case | score |
| --- | --- |
| status is closed | 0.10 |
| newest evidence is open | 0.97 x 0.90 ^ years since that date, never below 0.75 |
| newest evidence is open but it overrode an older closing record | 0.80 x 0.90 ^ years, never below 0.50 |
| no evidence, Overture says permanently_closed | 0.30 |
| no evidence, `missing_license` is true | 0.30 |
| no evidence, OpenPOIs confidence 0.80 or more (full layer) | that confidence |
| no evidence otherwise | 0.75, or less for a place only Overture has: 0.60, 0.40 or 0.25 by the source Overture took it from ("Listings nobody vouches for" below) |

The 0.90 a year assumes about one business in ten closes each year. The
0.30 comes from this build: of places Overture marks permanently_closed that
OSM can speak to, 7 were surveyed open and 20 were tagged closed.

Check, all four test regions: the score from the core layer, which has seen
no OSM data, against what OSM says about the same place.

| OSM says | places | mean core score | scored 0.30 or less | scored 0.80 or more |
| --- | ---: | ---: | ---: | ---: |
| closed (lifecycle tag) | 338 | 0.64 | 65 | 12 |
| open (surveyed in the last 2 years) | 2,771 | 0.82 | 11 | 861 |

So a low score is rarely wrong about an open place (11 of 2,771), but the
core layer only catches 65 of 338 known closures. The score is honest about
what the evidence says and no better than the evidence. The 0.75 for no
evidence is likely low: among places with no core evidence that OSM can
speak to, 1,899 were surveyed open and 261 tagged closed (88% open), though
mappers survey open places more readily than they tag closed ones.

### OpenPOIs

OpenPOIs publishes two things this build does not compute: events from
OSM's edit history matched to Overture places, and a calibrated confidence
per place. Both were checked in the District of Columbia box against the
core layer, which uses no OSM data.

History events as closures: 390 places. Independent evidence said open
after the event 7 times and closed 99 times, the best ratio of any closing
signal here. It adds about 280 closures to the box's 2,150. A sample of 36
that no other source had flagged read as real closures.

Confidence, against places this build knows about:

| OpenPOIs confidence | places | known open | known closed |
| --- | ---: | ---: | ---: |
| under 0.2 | 567 | 17 | 151 |
| 0.4 to 0.6 | 23,707 | 929 | 310 |
| 0.6 to 0.8 | 26,791 | 1,299 | 1,037 |
| 0.8 and up | 18,728 | 4,102 | 255 |

The bottom band is the history events again. The top band is reliable. The
middle does not separate open from closed (the 0.6 band has more known
closures than the 0.4 band), so only the top band is used: a place with no
evidence and a confidence of 0.80 or more takes that confidence as its
`open_score`. In the box that lifts 12,700 places off the flat 0.75.

### Why most "ended" lists fail and two pass

Nine registers that record an ended license, permit or registration were
tested as closures. Seven failed: SNAP end dates, French register
closures, Texas ended alcohol licenses, Texas sales tax out-of-business
dates, Oregon expired licenses, Sacramento business tax close dates, and
fuel tank removals. In each, the paperwork ends when
an owner or legal entity changes and the shop carries on.

Two pass, both limited to places with no brand: DC alcohol license
cancellations (1 open, 73 closed) and Chicago business license
cancellations (21 open, 292 closed, for sites with no live license). Both
record an explicit cancellation against a premises, not a lapse against a
taxpayer. The signals that work best are still the ones where someone saw
the place: an inspector's "out of business", a mapper's tag, Foursquare,
OSM edit history.

### Missing license

A bar cannot trade without an alcohol license, so in a state whose active
license list is complete, a bar that matches no license is suspect. Tested
in the District of Columbia, the one test area with such a list and with
positions on it.

| bars in DC | places | another source says open | another source says closed |
| --- | ---: | ---: | ---: |
| matched an active license | 228 | 32 | 3 |
| matched none | 560 | 17 | 131 |

Among the bars another source can speak to, no license means closed 89% of
the time. It is still not used as a closed verdict, for two reasons. The 17
open ones are real bars the matcher missed: the license is under another
trade name, or the bar sits inside a hotel or restaurant that holds the
license. And a sample of 40 unmatched bars with no other evidence held
several that looked like going concerns of that kind, so the true error
rate is likely higher than the 11% measured. Checking for another license
at the same address did not separate the two groups (bars with one: 9 open,
85 closed).

The same test in a New York City box, with the state's license list:

| bars in the box | places | another source says open | another source says closed |
| --- | ---: | ---: | ---: |
| matched an active license | 1,033 | 79 | 10 |
| matched none | 2,801 | 31 | 545 |

So the result is a flag and a lower score, not a status: `missing_license`
is true and `open_score` is 0.30 when there is no other evidence. In DC
that covers 390 bars. New York is on the list too. Restaurants and liquor stores are left alone: a
restaurant can run without a license, and liquor stores showed no signal
(2 open, 2 closed). California, Texas and Florida are not on the list:
their positions are geocoded and too many licenses miss their place. Among
unlicensed bars another source could check, Houston's were open 20 times
and closed 77, and Jacksonville's open 15 and closed 11, which is no
signal at all.

### Evidence sources in this version

| source | state | date used | how it attaches |
| --- | --- | --- | --- |
| fsq_closed | closed | Foursquare `date_closed` | Foursquare id carried in the Overture row |
| osm_lifecycle | closed | `end_date` tag if it parses, else the feature's last edit (an upper bound) | the OSM feature's own merge |
| osm_history | closed | day of the edit | OpenPOIs matched an OSM feature to the Overture place, and that feature was later deleted, lost its main tag, or was renamed to something else. Joined by Overture id. Full layer only. |
| wikidata_p576 | closed | P576 value | `wikidata` tag on a merged OSM feature, offices excluded |
| fdic_history | closed | effective date of change code 721 | matcher |
| fdic_locations | open | run date of the list | matcher |
| epa_ust_open | open | day the national layer was last edited | matcher |
| snap_current | open | last data edit of the layer | matcher |
| snap_history | open | last day the file covers, open-ended authorizations only | matcher |
| nces_schools | open | June 30 of the school year the file covers | matcher |
| cms_hospitals | open | the dataset's modified date | matcher, by address |
| nppes_orgs | open | later of last update and certification date | matcher, by address |
| dbpr_fl_food | open | day of the establishment's newest inspection | matcher, positions from the Census geocoder |
| agm_ny | open | day of the store's newest inspection | matcher |
| dcwp_nyc | open | day the dataset was last updated, active premises licenses only | matcher |
| dph_de | open | day of the establishment's newest inspection | matcher |
| moco_md | open | day of the newest inspection that ended in a pass or fail | matcher, positions from the Census geocoder |
| bot_sac | open | day the layer was last edited, active accounts only | matcher, positions from the Census geocoder |
| emd_sac | open | day of the facility's most recent inspection | matcher |
| lou_food | open | day of the establishment's newest inspection | matcher, positions from the Census geocoder |
| abc_ky_jefferson | open | day the layer was last edited | matcher |
| bbl_dc | open | day the data was refreshed, active licenses with a trade name | matcher, positions from the Census geocoder |
| bacp_chicago | open | day the dataset was last updated, unexpired issued licenses only | matcher |
| bacp_chicago_cancelled | closed | day the license status changed to cancelled | matcher; places with no brand only, and only when the site has no live license |
| li_phl | open | day the file was read, active company-held licenses | matcher |
| biz_seattle | open | day the layer was last edited, active locations in storefront trades | matcher |
| biz_denver | open | the layer's report date, active licenses | matcher, positions from the Census geocoder |
| tax_ny_tobacco | open | day the dataset was last updated | matcher |
| rev_pa_tobacco | open | day the dataset was last updated, unexpired retail licenses only | matcher |
| cpa_tx_tobacco | open | day the dataset was last updated | matcher, positions from the Census geocoder |
| elicense_ct | open | day the dataset was last updated, active unexpired shop-front license types | matcher, positions from the Census geocoder |
| dmv_ct | open | day the dataset was last updated, unexpired dealer, repairer and recycler licenses | matcher |
| biz_nola | open | day the dataset was last updated | matcher |
| dol_wa | open | day the dataset was last updated, active dealer licenses | matcher, positions from the Census geocoder |
| childcare_wa | open | day the dataset was last updated, active centers | matcher, positions from the Census geocoder |
| childcare_co | open | day the dataset was last updated, centers and preschools | matcher, positions from the Census geocoder |
| dbpr_fl_salon, dbpr_fl_vet, dbpr_fl_lodging, dbpr_fl_restaurant | open | day the files were read, current licenses only | matcher, positions from the Census geocoder |
| ocm_ny | open | day the dataset was last updated, active license and active operational status | matcher, positions from the Census geocoder |
| doh_ny_food | open | day of the operation's last inspection, unexpired permits only | matcher |
| isd_boston_food | open | day the list was last changed, active licenses | matcher |
| isd_boston_inspection | open | day of the establishment's newest inspection | matcher |
| lb_boston | open | day the list was last changed, active licenses | matcher, positions from the Census geocoder |
| lcb_wa | open | day the file was read, active unexpired licenses | matcher, positions from the Census geocoder |
| abc_nj | open | first day of the month of the report, licenses in use | matcher, positions from the Census geocoder |
| dor_wi_liquor | open | day the record was last updated, unexpired licenses | matcher, positions from the Census geocoder |
| lcc_ne | open | day the roster was read, active retail licenses | matcher, positions from the Census geocoder |
| bablo_me | open | day the file was read, active licenses for premises in Maine | matcher, positions from the Census geocoder |
| isp_id_liquor | open | day the file was read, issued unexpired retail licenses | matcher, positions from the Census geocoder |
| abc_ar | open | first day of the month of the list, active retail alcohol permits | matcher, positions from the Census geocoder |
| able_ok | open | day the lists were read, unexpired retail license types | matcher, positions from the Census geocoder |
| biz_lasvegas | open | day the layer was last edited, active licenses inside the city | matcher, positions from the Census geocoder |
| dchd_omaha_food | open | day of the establishment's newest inspection | matcher |
| mpls_food | open | day of the facility's newest inspection | matcher |
| mpls_liquor | open | day the layer was last edited, approved licenses | matcher |
| llb_baltimore | open | day the newest license year began | matcher, positions from the Census geocoder |
| cph_columbus_food | open | day the layer was read, permits that have not run out | matcher |
| mdard_mi_food | open | day the layer was read, active fixed establishments | matcher |
| dph_sc_food | open | day of the permit's newest inspection, active permits | matcher |
| mda_mn_food | open | day the list was read, unexpired licenses | matcher, positions from the Census geocoder |
| dca_ca_salon, dca_ca_auto, dca_ca_pharmacy | open | day the files were read, licenses in force held by organizations | matcher, positions from the Census geocoder |
| dpor_va | open | day the lists were read, unexpired shop licenses | matcher, positions from the Census geocoder |
| bop_tx, bop_oh | open | day the file was read, active retail pharmacies | matcher, positions from the Census geocoder |
| hrsa_health_centers | open | day the file was made, active permanent sites | matcher |
| childcare_az, _ca, _de, _ma, _mi, _mn, _nj, _tn, _vt, _wi | open | day the layer was last edited, or read; centers only | matcher |
| phx_liquor, nash_beer, mke_food, mke_liquor, anc_liquor, hsv_liquor, det_biz, det_liquor, det_food, miami_dade_biz, broward_biz, tucson_biz, bellevue_biz, saccounty_biz, longbeach_biz, anaheim_biz, glendale_az_biz, nn_biz, sac_tobacco, fairfax_food, wic_nj, tucson_liquor, lou_tobacco, wic_fl, wic_az, wic_va, chesapeake_biz, riverside_food, cdph_ca_facilities, co_tobacco, lac_biz | open | day the layer was last edited or read, licenses in force | matcher |
| sux_food, alameda_food | open | day of the site's newest inspection | matcher |
| maricopa_food | open | day the layer was last edited, issued permits | matcher |
| vb_biz | open | day the license began | matcher, positions from the Census geocoder |
| achd_pa_food | open | day of the newest inspection in the last two years, active permits | matcher, positions from the Census geocoder |
| abc_nc, abc_ky, abc_ks | open | day the search was run, active retail licenses | matcher, positions from the Census geocoder |
| plcb_pa | open | day the export was read, active retail licenses | matcher, positions from the Census geocoder |
| tda_tn_food | open | day the list was read, current licenses | matcher, positions from the Census geocoder |
| foodsafety_ak, _ar, _ia, _ks, _nd, _pa, _sd, _vt | open | day of the establishment's most recent inspection | matcher, positions from the Census geocoder |
| dhhs_nc_inspections | open | day of the establishment's newest inspection in the last two years | matcher, positions from the Census geocoder |
| cambridge_food | open | day the permit was issued, last two years | matcher |
| moco_md_alcohol, childcare_ny, childcare_nyc, nj_inspection, lottery_ny, lottery_fl | open | day the table was last updated | matcher |
| fw_co, fw_co_build | open | day the certificate of occupancy was issued, last three years; an opening, not a roster. fw_co_build holds the certificates that close a building permit | matcher |
| snhd_nv_food | open | day the nightly file was read; food permits active in Clark County, Nevada, one row per permit, mobile and portable kinds left out | matcher |
| lac_food | open | day the quarter's inventory was published; restaurants and food markets under a Los Angeles County health permit | matcher |
| sd_county_food, scc_food, wic_ny | open | day the table was last updated; San Diego County food permits in force for fixed premises, Santa Clara County food businesses, New York WIC stores and pharmacies | matcher; San Diego and New York positions from the Census geocoder |
| tceq_tx_cleaners | open | day the table was last updated, operating dry cleaners and drop stations | matcher, positions from the Census geocoder |
| wm_nyc | open | day of the shop's newest test in the last two years | matcher |
| austin_food, cincinnati_food, boulder_food, marin_food | open | day of the newest inspection in the last two years | matcher (Austin geocoded) |
| la_biz, sf_biz, biz_sandiego, brla_biz, norfolk_biz, berkeley_biz | open | day the table was last updated | matcher (Baton Rouge and Berkeley geocoded) |
| lottery_tx | open | end of the retailer's last month with sales | matcher, positions from the Census geocoder |
| childcare_pa, childcare_tx | open | day the table was last updated | matcher, positions from the Census geocoder |
| dph_ga_inspections, msdh_ms_food, adph_al_food | open | day of the establishment's newest inspection in the last two years | matcher, positions from the Census geocoder |
| osdh_ok_food | open | day the list was read | matcher, positions from the Census geocoder |
| rev_pa | open | day the dataset was last updated, unexpired licenses only | matcher |
| biz_de | open | day the dataset was last updated, current licenses only | matcher, positions from the Census geocoder |
| tdlr_tx | open | day the dataset was last updated, unexpired establishment licenses only | matcher, positions from the Census geocoder |
| cpa_tx | open | day the dataset was last updated, live permits only | matcher, positions from the Census geocoder |
| dos_ny_salons | open | day the dataset was last updated, unexpired licenses only | matcher |
| dmv_ny | open | day the dataset was last updated, unexpired registrations only | matcher |
| kc_wa_food | open | day of the business's newest inspection | matcher, positions from the Census geocoder |
| dohmh_nyc | open | day of the restaurant's newest inspection | matcher |
| cdph_chicago | open | day of the newest inspection that got in (pass or fail) | matcher |
| cdph_chicago_oob | closed | day of an inspection that found the business gone | matcher; places with no brand only |
| led_co | open | day the dataset was last updated | matcher |
| olcc_or | open | day the dataset was last updated | matcher, positions from the Census geocoder |
| atc_mo | open | day the dataset was last updated | matcher, positions from the Census geocoder |
| abt_fl | open | day the file was read | matcher, positions from the Census geocoder |
| abc_ca | open | the export's Updated date | matcher, positions from the Census geocoder |
| tabc_tx | open | day the dataset was last updated | matcher, positions from the Census geocoder |
| sla_ny | open | day the dataset was last updated | matcher |
| abca_dc_active | open | day the layer was last loaded | matcher |
| abca_dc_cancelled | closed | day the layer was last loaded (an upper bound) | matcher; restaurants, taverns, nightclubs and clubs only |
| ncua_branches | open | the quarter's cycle date | matcher, by address |
| irs_eo | open | last day of the month the newest return covers | matcher, by address |
| atp | open | day the spider collected the chain's locator | the AllThePlaces row's own merge |
| osm_check_date | open | `check_date` or `survey:date` tag | the OSM feature's own merge |

A current list can be stale. CMS still lists United Medical Center in
Washington as of 2026-07, and OSM tags it disused with an edit dated
2026-05. The list is newer, so the place comes out open, and the closing
record stays visible in `evidence`. One case in ten hospitals read; watch
this as more lists are added.

The ATP and OSM check_date rows were not in the brief. Being listed in a chain's own locator on
a known day, and a mapper's dated survey tag, are both dated records of
life, and both come for free with the base layer. Absence from a locator is
still not evidence of anything.

### Listings nobody vouches for

Most places have no evidence at all, and in a big city a large share of
those are listings that exist in Overture and nowhere else: a company
registration at an office suite, a page someone made once, a venue that
closed before anyone recorded it. Nothing can call them closed. But who
lists a place turns out to predict whether it is real.

Overture says which source each place came from. In a Seattle box 37% of
its places come from BrightQuery alone (company records), 37% from Meta,
14% from Microsoft, 10% from Foursquare. Seven percent of the BrightQuery
ones are also in OSM or AllThePlaces, against 29% of the Meta ones.

The test uses cities where a register is complete for one kind of place,
so a real one should be found in it. Restaurants and cafes against the
local inspection list, for places only Overture has and with no closing
record, share that match an inspection:

| city | Meta | BrightQuery | Foursquare | Microsoft | for comparison, places OSM also has |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seattle | 25% | 4% | 4% | 5% | 51 to 78% |
| Chicago | 36% | 5% | 5% | 9% | 40 to 80% |
| New York | 33% | 5% | 8% | 9% | 44 to 83% |
| Boston | 30% | 6% | 4% | 5% | 17 to 41% |
| Detroit | 33% | 8% | 3% | 12% | 4 to 63% |
| Columbus | 27% | 5% | 7% | 8% | 24 to 65% |

The same in a Sacramento box against California's license files, where
OSM has too few of these trades to compare with:

| kind | Meta | BrightQuery | Foursquare | Microsoft |
| --- | ---: | ---: | ---: | ---: |
| salons and barber shops | 40% | 16% | 5% | too few |
| auto repair | 43% | 28% | 12% | 21% |

Bars against the liquor license list run the same way: in a New York
City box 21% of Meta's Overture-only bars hold a license, 4 to 6% of the
others; in the DC box 14% and 1 to 6%.

So a restaurant that only Overture has, taken from BrightQuery, Foursquare
or Microsoft, is found by the inspectors about a tenth as often as one a
mapper has confirmed. For salons and repair shops the gap is smaller but
runs the same way.

What is done with it: `overture_sources` is published, and a place with no
evidence that only Overture has starts from a lower `open_score` (0.60 for
Meta or several sources, 0.40 for BrightQuery or Microsoft alone, 0.25 for
Foursquare alone) than one OSM or AllThePlaces also has (0.75). The
numbers are set by hand from the tables above, measured on three kinds of
place and applied to all, so they are a rule of thumb like the rest of the
score. Status is not touched: these places stay `unknown`.

A check against a source the core layer never reads. For core places that
OSM mappers have either surveyed since 2025 or tagged closed, the share
they call open, by the core layer's score:

| core `open_score` | Seattle | Chicago | New York |
| --- | ---: | ---: | ---: |
| 0.10 (closed) | 3% of 34 | 11% of 213 | 1% of 158 |
| 0.25 | 23% of 97 | 16% of 51 | 25% of 150 |
| 0.30 | 6% of 32 | 0% of 6 | 16% of 63 |
| 0.40 | 52% of 445 | 32% of 138 | 25% of 412 |
| 0.60 | 92% of 630 | 85% of 286 | 78% of 483 |
| 0.75 to 0.89 | 78% of 93 | 85% of 124 | 78% of 216 |
| 0.90 and up | 96% of 1,972 | 98% of 1,060 | 94% of 954 |

The order holds in all three. The places mappers can speak to lean toward
real ones, so the low rows are, if anything, flattered.

What was tried and not done: calling a restaurant suspect because the
inspection list does not have it, the way `missing_license` works for
bars. See section 9.

### Opening hours

Hours are carried, not judged. A place takes the hours of its newest
member that has any: an AllThePlaces record (dated by the day the spider
ran) or, in the full layer, an OSM feature (dated by its last edit, which
is not always an edit of the hours). Nothing checks them against anything
else yet, so `hours_date` is the reader's guide to how far to trust them.
On the DC test box that gives hours to 6% of all places and 24% of food
and drink; the core layer, with AllThePlaces alone, has 2%.

## 8. Licensing

| source | license | consequence |
| --- | --- | --- |
| Overture places | CDLA-Permissive-2.0 (rows from Foursquare are Apache-2.0) | attribution |
| AllThePlaces | CC0-1.0 | none |
| Foursquare OS Places | Apache-2.0 | keep the notice, see NOTICE |
| FDIC, USDA | US federal work, public domain | none |
| Wikidata | CC0-1.0 | none |
| OpenStreetMap | ODbL-1.0 | attribution and share-alike on any derived database |

A table that contains OSM-derived rows, or values computed from OSM, is an
ODbL derived database. That reaches further than the OSM-only rows: a core
place whose status was decided by an OSM lifecycle tag, or whose phone was
filled from OSM, is OSM-derived too.

**Decision: copyleft, with separable layers.**

- The code is AGPL-3.0-or-later.
- `places-<region>.parquet` is the core plus OSM. It must be under the ODbL.
- `core-<region>.parquet` is built without reading OSM. Its inputs are all
  permissive, so its license is a choice, and the choice is the ODbL as
  well, so that anything built on the Almanac stays open.
- The core layer is still built separately. That keeps the choice open: a
  file with no OSM in it can be offered under other terms later, a file
  with OSM in it never can.
- Every row carries `sources` and `licenses`, the licenses of the inputs
  that touched it.

What that asks of anyone who uses the files, closed source or not:

- show the credit line in NOTICE wherever the data, or anything made from
  it, is shown to the public;
- if they change the data or merge it into another database and let the
  public use the result, publish that database under the ODbL too;
- keep the notices with any copy.

An app does not have to open its own code to read the files, but it cannot
drop the credit, and it cannot keep an improved copy of the data to itself.
Public domain inputs do not weaken this: the license covers the merged
database, and nobody gets the matching, the statuses or the merged rows
except through it. One limit to be plain about: a single fact, such as one
shop's address, is not something any license can own.

Open point: whether the Wikidata P576 signal belongs in the core layer.
Wikidata is CC0, but the link from place to item comes from an OSM tag, so
for now it sits in the full layer only.

`SOURCES.md` records each source's license and URL. Sources with no stated
license (many city feeds) get an entry that says so before any adapter for
them is merged.

## 9. Rejected rules

Measured in the District of Columbia box unless noted. "Independent" means
evidence from a different source for the same place.

| rule | result | why it is out |
| --- | --- | --- |
| SNAP End Date means closed | 499 places matched. Independent evidence said still open 98 times, closed 27 times. | An ended authorization is a change of owner or a store leaving the program far more often than a closing. The adapter reads these rows and emits nothing. |
| Foursquare `date_closed` matched by name and position, for rows Overture does not link by id | 2,142 places matched. Independent: open 101, closed 129. | Foursquare often closes one of its own duplicate records for a place that is still there. Joined by id the same field is good: open 6, closed 33. |
| Jaro-Winkler from 0.93 | 10 pairs read between 0.93 and 0.95: 2 wrong ("Embassy of Albania" and "Embassy of Mali"), 1 doubtful. 30 read at 0.95 and up: none wrong. | Threshold raised to 0.95. |
| Name contained anywhere in the longer name | Joined a shop to the mall it is named after, and a department to its hospital. | Only leading words count now. |
| A bank branch record matching the bank's ATM | 3 of 40 FDIC closings landed on an ATM or mortgage desk listing. | A name with ATM on one side only never matches. |
| Wikidata P576 on offices | 4 hits across two boxes, 2 of them a company merger date on an office building. | Skipped when the OSM feature is `office=*`. The 2 that remain (a hospital, a school) are right. |
| Merging Overture duplicates on anything looser than an identical name | Same house number with a leading-words or near-spelling match: about 10 of 21 read were a part and its whole (a gift shop and its hospital, two advisors at one bank). No house number: mostly junk pages sharing a point. Different numbers within 30 m: 13 pairs, several wrong. | Only same number plus identical name merges. |
| Adding places from address-only food inspection registers (Alabama, Huntsville box) | 195 rows would be added. After three rounds of guards 37 were left, and 25 of the 37 were a storefront of its own. | The rest are campus dining halls, kiosks inside supermarkets, company cafeterias and day cares. An inspection list names kitchens, not storefronts. Used as evidence only. |
| Adding places from every class in the Nebraska liquor roster (Omaha box) | 69 would be added; 28 of 40 read were a storefront. | The roster holds special licenses of foundations, a parish office, a fraternity house and a sports commission. Those classes (nonprofit, special designated, catering, wholesale) are now a source of their own that never adds a place, and the premises classes do add (section 6). |
| Adding places from Missouri alcohol licenses (Kansas City box) | 63 would be added; 33 of 40 read were a storefront. | Two were a person's name, others a vending company and a food contractor. The trade-name column itself holds those names, so there is nothing to split on. Evidence only. |
| Adding places from Arkansas alcohol permits (Little Rock box) | 34 would be added; 27 were a storefront. | The rest carry the permit holder's company name ("Foxden USP Opco" for three U.S. Pizza branches already listed), in the alias column too. Evidence only. |
| Adding places from the NCES public school list (Houston box) | 44 would be added; nearly all are schools the map already has. | The list abbreviates ("KOLTER EL", "YATES H S"), so the name test does not see "Kolter Elementary School" as the same school, and the rest are programs at a district office. Evidence only. |
| Adding places from California child care licenses (Sacramento box) | 42 would be added; about 20 are a center of their own. | The rest are state preschools, Head Start rooms and after-school programs inside a school or college, some listed twice. Evidence only; the other states' child care lists were not read for this. |
| Adding places from California auto repair registrations (Sacramento box) | 287 would be added; about half of 40 read are a shop. | The other half are mobile mechanics and glass fitters registered at a home address. Evidence only. |
| Adding places from New York's tobacco retailer registrations (Buffalo box) | 47 would be added; most are a person's name. | The registration is in the name of the owner, often an individual, and the chain rows are the operating company of a station already listed. A person's name must never become a place. Evidence only. |
| Adding places from Florida restaurant licenses (Jacksonville box) | 200 would be added; about 25 of 40 read are a restaurant of its own. | The rest are stadium concession stands by number, food hall booths and a chain under its franchisee's code. Evidence only. |
| Adding places from Ohio pharmacy licenses (Columbus box) | 59 would be added; nearly all are a long-term-care pharmacy's license inside a nursing home. | Not a storefront. Evidence only. |
| Adding places from New York salon and barber shop licenses (New York City box) | Added places until 2026-10-12. Of 50 read then, 12 were a person's name, several at an apartment. | The address is the licensed place of business and the name is the business name, which for a sole proprietor is their own. A one-person studio in an apartment or a suite room is not a place someone walks into off a map: taken out the day it was read. Evidence only. |
| Adding places from New York repair shop and dealer registrations (New York City box) | Added places until 2026-10-12. Of 36 read then, 26 were a shop or dealer. | The rest are city agency garages, a person's name and an estate. Evidence only. |
| Adding places from every license in the liquor layers of Phoenix, Anchorage, Huntsville, Milwaukee and Boston | Read in each city. Phoenix: about 22 of 40 a storefront, the rest distributors, importers and spirit brands. Anchorage: 30 of 40, with wholesalers and ball clubs. Huntsville: 30 of 40, with one-day event licenses. Milwaukee: 32 of 40, with vendors on the festival grounds and caterers. Boston's Licensing Board: lodging houses, property trusts and people among the first 40. | Each layer holds license kinds that are not a premises open to the public. Phoenix and Anchorage name the kind in a field, and their retail kinds now add places (section 6). Milwaukee's misses hold the same license class as its taverns, and Huntsville and Boston were not split: evidence only. |
| Adding places from Tucson liquor licenses, Louisville tobacco licenses and the WIC store lists of Florida, Arizona and Virginia | As evidence all five read clean: 39 of 40 matches right in Tucson, 40 of 40 in Louisville, Miami, Phoenix and Norfolk. As adders: Tucson would add 92, and of 40 read 7 were wrong (a Costco placed 505 m from itself, a cinema 259 m, a hotel, a distributor under its old name, three court program rows at one county office). Louisville would add 27, 12 of them a bare "Convenience Store", "Food Market" or a person's name next to the shop itself. WIC would add 5 in Miami, 15 in Phoenix and none in Norfolk; the Phoenix 15 are Food City stores under the name "Bashas' - Food City", and Arizona's points sit 120 to 230 m off. | Tucson's points are sometimes hundreds of meters out and Louisville names the license, not the shop. WIC stores are large grocers the base already has. All five: evidence only. |
| Adding places from every Fort Worth certificate of occupancy | 669 would be added in the box, 220 of them certified in 2026. Of 45 read, 32 were a business with a door: taquerias, a cantina, tire and auto lots, salons, smoke shops, a bail bondsman. | The other 13 were a street address standing in for a name, a building or a remodel phase ("Tobias Place Bldg 7", "South Hills HS Phase 5 Remodel"), a landlord, a person, or a bare "Restaurant Taqueria". The occupant field is typed by the applicant. Certificates that close a building permit are now a source of their own that never adds a place, and an occupancy certificate adds one only when its name reads as a shop (section 6). |
| Adding places from a city business roll on the shop-name test alone | Read in more than twenty cities. About 22 of 40 a storefront in Los Angeles, 10 in San Francisco, 28 in Seattle, 25 in San Diego, 26 in Virginia Beach, 31 in Sacramento, 34 in Broward, 33 in Tucson, 35 in New Orleans. | A roll holds every registered business, and a jeweler, a bakery, a nail technician renting a chair or a mobile tire fitter has a shop's name. Twelve of those that fail pass once held to more (section 6: no unit address, no one-person trade names, a listed business within 40 m). |
| Adding places from a city business roll held to more: San Diego, Los Angeles, San Francisco, Bellevue, Norfolk, Berkeley, Chesapeake | San Diego 500 would be added, 32 of 40 a shop; Los Angeles 1,796, 32 of 40; San Francisco 919, 30 of 40; Bellevue 41, 32 of 40; Norfolk 97, 35 of 40; Berkeley 35, 29 of the 35; Chesapeake 63, 35 of 40. | What is left after every filter: home kitchens and jewelers on streets where the neighbor is itself a home business, sushi counters inside groceries, food trucks at their commissary, stadium concessions, parking lots and fuel stations under the operator's name. Evidence only. |
| Adding places from Philadelphia and Newport News business licenses | Philadelphia: 144 would be added held to more, 36 of 40. Newport News: 66, about 32 of 40. | Both write a name as "Legal Name (Trade Name)". The brackets sometimes hold a mailing line, a person or a store number ("WAWA INC (STORE 8631)"), so what is left unmatched is mostly a chain store or the shop next door under its company's name. Reading the brackets as the trade name did lift ordinary matching: 2,039 of 5,559 licenses in the Philadelphia box now find a place, and 1,839 of 7,261 in Newport News, up from 1,197. Evidence only. |
| Adding places from state license lists held to more: Florida restaurants (DBPR), Connecticut state licenses | Florida restaurants: 41 in Miami, about 32 of 40. Connecticut: 40 in Bridgeport, 35. | Florida restaurants: hotel "Main Kitchen" and "Banquet Kitchen" licenses. Connecticut: a bodega under its new owner's name beside the listing under the old one. Evidence only. Virginia (DPOR) and Washington (DOL) gave 2 and 4 rows, too few to read. |
| Adding places from food permit lists held to more: Southern Nevada, Santa Clara County, Maricopa County, Omaha, Austin, North Carolina, Louisville, Cincinnati | Las Vegas: 499 would be added, nearly all a casino's kitchens, service bars and concourse stands. Santa Clara: 85, 32 of 40. Maricopa: 242, 33 of 40. Omaha: 30 at first, 22. Austin: 49, about 25 of 40. North Carolina (Charlotte): 37, 29. Louisville: 57, 34 of 40. Cincinnati: 47, 31 of 40. | Santa Clara permits each department of a supermarket and company cafes. Maricopa's layer puts some rows at a county office and lists street taco stands. Omaha lists trucks and carts at their commissary. Austin, placed on address points, puts chain stores far from where the map has them, so they are added twice. Charlotte, Louisville and Cincinnati: company and campus cafes, a jail kitchen, stadium stands, church kitchens. Evidence only. Georgia, Cambridge, Kansas, Vermont, Tennessee, New York State, Mississippi, Alabama, Fairfax and Sioux Falls gave fewer than 30 rows in their boxes and were not read; Oklahoma, Boulder, Marin and Minnesota gave none, for want of address points. |
| Adding places from Texas sales tax outlets (Houston box) | 11,073 would be added, more than every other register in the box together. Of 50 read, about 22 are a storefront (food marts, cleaners, tire shops, a gun shop). | The rest sell from a house: craft, design and resale businesses on residential streets, and stalls inside a flea market under the stallholder's name. Counting only rows with a listed business within 40 m lifts it to about 20 of 28. Not enough either way: evidence only, and the best argument yet that the long tail cannot be added from a tax roll. |
| Adding places from address-only salon licenses (Texas TDLR, Houston box) | 565 would be added; 20 of 40 read were a storefront. | The other half are chair renters in salon suites, salons in a home, and licenses in a person's name. Used as evidence only. |
| Adding places from NYC weights and measures tests | 94 would be added; most of 40 read are a person's name. | The test is recorded under the licensee, often an individual. A person's name must never become a place. Used as evidence only. |
| San Francisco: a business location with an end date means closed | San Francisco box, places with no brand and no live location under the same name: independent closed 102, open after the end date 72. | 59%, far below the signals that are kept. The end date marks one registration ending; the shop often carries on under a new one. Held, not emitted. |
| Allegheny County: a food facility with a closing date means closed | Pittsburgh box, places with no brand and no active permit under the same name: independent closed 48, open after the closing date 49. With a brand: 1 and 25. | The date closes one permit; the next operator's is a new record. Held, not emitted. This is the fourth register whose own end dates fail the same way (Texas sales tax, Sacramento business tax, San Francisco locations). |
| New York health club filings as open evidence | New York City box: 6 of 50 found a place, and 2 of the 6 were a chain's head office and a condominium. | The filing is by the company, at the company's address. Not used. |
| Merging Overture rows within 60 m whose names differ only by generic words ("Safeway" and "Safeway Pharmacy"), as Vela's map bake does | DC box, 228 pairs, 60 read: 24 one business, 30 a part and its whole (33 pairs are a cash machine and its branch, 28 a pharmacy and its store), 4 different businesses (Global Integrity and Global Financial Integrity in one suite). | Right for drawing one pin, wrong for a list of places: the part has its own license and hours. Left to readers. |
| Merging Overture rows within 60 m with identical names and different house numbers | DC box, 26 pairs read: at least 5 are two places (two Starbucks 80 m apart, two garages of one operator, two offices of a practice that Overture put on one point). | Not merged. The same pairs with one house number, or one missing on a side, were all right and differ only by a bracketed aside or a legal form, which name cleanup now drops. |
| DC alcohol license cancellation means closed, for every license type | 283 places matched. Independent: open 18, closed 60. The open ones were grocery stores, hotels and places that had swapped one license for another. | Kept only for restaurants, taverns, nightclubs and clubs, and skipped when the same trade name has an active license at the address. After that: open 8, closed 54, in line with the Foursquare and OSM signals. |
| France: a closed SIRENE establishment means the place closed | Paris box, places whose newest SIRENE record was a closure: independent evidence said open 1,082, closed 647. Joined by SIRET id it was still open 130, closed 40. | A SIRET closes when a shop changes owner or legal form. Closed establishments are not emitted. |
| France: dating an active SIRENE record by the register's processing date | Nearly every record was processed in the last year. Dated that way, an active entry overrode 159 hand-tagged OSM closures and 152 Foursquare ones. | Dated by dateDebut, the last real change. Overrides fell to 39 and 14. Most SIRENE records are then old and inform `open_score` without setting a status. |
| A fuel site whose last underground tank was removed is closed (EPA) | Kentucky: 1,153 places matched. Independent: open 353, closed 15. | Tanks are replaced under a new record, and many sites are not fuel stations. Only sites with tanks in use are emitted, as open evidence. |
| Texas: a surrendered, cancelled or expired alcohol license means closed | Houston box, on-premise license types only, skipping names with an active license at the address: 1,212 places. Independent: open 79, closed 89. | Not emitted. |
| Chicago "Out of Business" inspections, for every place | Chicago box, places with no later inspection: independent open 63, closed 187. Split by whether the place carries a brand: chains open 36, closed 3; independents open 27, closed 184. | A chain outlet changes franchisee and license and carries on. The closure is kept for places with no brand only. The same limit now applies to DC license cancellations, which went from 8 open and 54 closed to 1 and 73. |
| Oregon: an expired on-premises alcohol license means closed | Portland box, places with no brand and no live license under the same name: independent open 6, closed 26. | 81% on a small sample is below the signals that are kept (87% and up). Not emitted. |
| Texas Comptroller out-of-business dates for sales tax locations | Houston box, places with no brand and no live permit under the same name: independent open 87, closed 85. | The date marks one taxpayer leaving; the shop often carries on under the next. Not emitted. Live permits are good open evidence: of 13,980 places with one, other sources called 79 closed and 5,053 open. |
| City of Sacramento close dates on business tax accounts | Sacramento box, places with no brand and no active account under the same name: independent open 33, closed 33. | Not emitted. |
| Overture operating_status as a closed verdict | 6,175 rows say permanently_closed, nearly all from one supplier, with no date. Where this build has dated evidence for them: closed 31, open 12. | No date, and wrong too often. Carried as `overture_status`, never used. |
| Restaurant with no inspection record, in a city whose inspection list is complete | Where another source could speak, restaurants with no inspection were closed 48% of the time in Seattle, 72% in Chicago, 79% in New York, 47% in Boston, 44% in Detroit, 41% in Omaha, 47% in Columbus. A bar with no license was closed 89% of the time. Restaurants trade under too many names for the absence to mean much. | No flag. The listing's source is used for the score instead (section 7). |

Carried over from earlier work and not retested: website liveness, and
"missing from the chain's locator means closed".

## 10. Other countries

The base layer and four signals are global: Overture, OSM, AllThePlaces,
Foursquare closing dates, OSM lifecycle and survey tags, Wikidata. A region
with a country code in `regions.tsv` builds from those alone. Registers are
then added per country, as adapters that write to
`data/cache/evidence/<country>/`.

What is tied to a country:

- The house number is read from the front of the street line. Right for
  the US, UK and France; wrong where the number follows the street name
  (Germany, Spain, Italy), which needs its own rule before those are built.
- `street_key` skips French street types and articles as well as English
  compass words. Legal forms dropped from names include the French ones.
- State outlines, `missing_license` and places minted from registers are
  US only for now.

**France.** Test area: a Paris box (48.815 2.224 48.902 2.470). Register:
SIRENE, the national list of business establishments.

| | Paris box |
| --- | ---: |
| places | 207,916 |
| with a dated status | 41,514 (20%) |
| with any evidence | 41% |
| open, decided by OSM survey date | 22,922 |
| open, decided by chain locator | 8,831 |
| open, decided by SIRENE | 6,902 |
| closed, by OSM lifecycle | 1,629 |
| closed, by Foursquare | 1,220 |

OSM carries far more here than in the US: 37% of named OSM features in the
box have a survey date. SIRENE matched 69,000 places. 25 matches were read
per rule: number 24 of 25, near 22 of 25 (the misses are a related company
at the address, or a short name that is the start of a longer one). 18,000
more joined exactly, through the SIRET that mappers tag on OSM features.

## 11. Publishing

Per region: `core-<region>.parquet`, `places-<region>.parquet`,
`added-<region>.parquet` lists the places the build added from a register
(id, name, category, position, source, opened_date, build_date), so a later
build can count how many of them the map datasets came to list.

`status-<region>.parquet` (id, status, status_date, status_source,
open_score and missing_license only, for readers that just join on id) and
`manifest-<region>.json`. Each release from the second one on also carries
`changes.parquet`: every place that appeared, vanished, closed, reopened,
was newly confirmed open, or went quiet since the release before, made by
`tools/changes.sql`. A real release has one region per state plus DC.

- GeoParquet, zstd, rows in Hilbert order, 20,000 rows per row group.
- `lat` and `lng` are ordinary double columns. A reader filtering
  `lat between .. and lng between ..` skips row groups by statistics, which
  works over HTTP range requests with DuckDB, pyarrow or GDAL. Prune on
  those, not on the geometry.
- The manifest lists the build date, the box, each source's release, and for
  each file its row count, size, license and SHA-256. It also carries the
  credit, so it travels with the data:

  | field | value |
  | --- | --- |
  | dataset | `Vela Almanac` |
  | license | `ODbL-1.0` |
  | credit | the credit line a reuser must show, as in NOTICE |
  | notice | URL of the NOTICE file with the source notices |
  | region, build_date, bbox | what was built and when |
  | country, iso_3166_2 | `US` and `US-NY`, so a reader can map a file to its own regions without knowing ours (null for a test box) |
  | osm_extracts | the Geofabrik extract names the region was built from |
  | sources | the release of each base source |
  | files | name, layer, license, rows, bytes, sha256 per file |
- First host: GitHub release assets, one release per monthly build, tagged
  with the build date. The release also carries `manifest.json`, which
  lists every region's files. The scheduled workflow pins one Overture
  release and one AllThePlaces run for the whole build. The
  largest state should come out near 200 MB, well under the 2 GB cap
  (Kentucky is 25 MB for 247,000 places).

State builds are clipped to the Census state outline (cartographic
boundary file, 1:500,000, public domain). The outline is generalized, so a
row just outside it is kept when its own address names the state and it is
within about 5 km.
