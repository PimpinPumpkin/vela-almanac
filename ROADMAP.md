# Roadmap

What gets built next, in order, and what counts as done. The aim is the
coverage and freshness people expect from a commercial map, from open
sources only, United States first.

Where things stand (build of 2026-10-12): 19.5 million places, 13.1% with a
dated status, 237,000 of them added from a register (the files of that
day repeat 59,000 of those in a neighboring state; fixed since). Banks 66%, chain
restaurants 61%, gas stations 57% (fewer rows than before: the listings a
forecourt has under each of its brands are now one place), grocery 49%,
pharmacies 41%, independent restaurants 35%, bars 28%, everything else 9%.
The city business lists added on 2026-10-12 (Los Angeles, San Francisco,
Miami-Dade, Broward and others) are in that build. Each doubles or
triples coverage inside its city and moves the national figure by a
fraction of a point: the long tail closes city by city.

## How every item is done

These rules do not change from item to item.

1. Fetch the source first and read its real layout. Record its license and
   URL in SOURCES.md before any code is merged.
2. One adapter per source, emitting the evidence format in SPEC.md section 5.
3. Build the test regions and read 40 matches per rule. Write the count in
   SPEC.md.
4. A closure signal must also pass the independent check: where another
   source can speak, it must agree far more often than not. The ones that
   failed so far (SNAP end dates, French register closures, tank removals,
   Foursquare by name) all looked reasonable before they were measured.
5. A rule that is wrong more than rarely is removed and written down with
   its numbers in SPEC.md section 9.
6. Tests pass, docs match the code, the change is pushed, and the monthly
   build stays green.

## 1. United States: licensed categories

The categories where a register can make coverage complete.

- **1.1 State alcohol license lists.** One adapter per state. Done:
  Arkansas, California, Colorado, Connecticut, DC, Florida, Idaho, Maine,
  Kansas, Kentucky, Missouri, Nebraska, New Jersey, New York, North
  Carolina, Oklahoma, Oregon, Texas, Washington, Wisconsin. Kansas,
  Kentucky and North Carolina are read through their search forms, and
  Pennsylvania from the board's own export. What could not be used is
  listed in FOLLOWUPS.md. Massachusetts publishes a file but its site turns
  this project's fetches away, so it is left alone. The other states were searched on 2026-10-07
  and offer a search form only, block fetches, or sell the list (the
  findings are in SOURCES.md). Done for a state when its bars pass 40% with
  a status.
- **1.2 Missing license flag** for each of those states whose list has
  positions (today: DC and New York).
- **1.3 Restaurant inspections.** Done: Florida (Jacksonville restaurants
  went to 31% with a status), New York City, and Chicago (56% in the test
  box, with an "out of business" result that works as a closure for
  independents), King County, Washington (52% in a Seattle box), Delaware,
  Montgomery County, Maryland, and New York's retail food stores.
  New York State outside the city is done too, and so are Los Angeles,
  San Diego and Santa Clara counties (permit inventories, no inspection
  results). Next: other large cities.
  Target: independent restaurants from 18% to 40% in covered areas.
- **1.4 Fuel.** Use the tank registry's "temporarily out of service" count
  to lower the score of mothballed stations. EV chargers from the federal
  station list (needs a key, see the last section).
- **1.5 Lodging, pharmacies, child care.** State license lists where
  published, Florida's hotel and restaurant licenses first.

## 2. United States: the long tail

Salons, repair shops, small retail. 84% of all rows, 8% with a status.

- **2.1 Auto repair registrations.** Done: New York (repair shops,
  inspection stations, dealers), California (repair dealers, smog and
  safety stations), Connecticut, Washington dealers. No other state file
  was found in the search of 2026-10-07.
- **2.2 Cosmetology and barber shop licenses.** Done: California, Florida,
  New York, Texas and Virginia
  (Houston nail salons went from 7% with a status to 52%). Next: state by
  state.
- **2.3 Sales tax permit lists.** Done: Texas, the biggest long-tail source
  so far. In a Houston box a quarter of auto repair, clothing, furniture
  and jewelry stores now have a status. Also done: Delaware's business
  license list, which took the whole state from 8% of places with a status
  to 19%, Pennsylvania's retail sales licenses, and Chicago's business
  licenses, whose cancellations also work as closures, and city business
  licenses for DC, Philadelphia, Sacramento, Seattle and Denver. Next: any other state
  that publishes active permits or licenses.
- **2.4 State inspection and emissions station lists.**
- **2.5 Geocode the address-only registers.** Done for California and Texas
  licenses with the Census geocoder: California went from 25% of licenses
  finding a place to 61%. Still to do: the federal address-only registers
  (NPPES, IRS, CMS, NCUA).
- **2.6 Add places from address-only registers.** Built on 2026-10-12: a
  row is pinned to its address point in the National Address Database and
  may then add a place (SPEC.md section 6). On for the Texas, Washington,
  North Carolina, Kansas, Kentucky, New Jersey, Maine, California,
  Florida, Colorado, Oregon, Idaho and Nebraska liquor registers, seven
  city liquor lists, the Texas and Colorado tobacco
  retailer lists, and Texas pharmacies and child care centers;
  Nebraska, Missouri and Arkansas were read and refused. Next: find
  address points for Colorado, Oregon, Mississippi and the other
  states with none in the public domain (their liquor registers cannot be read for
  this until then); carry the register's own business type.

Done when "everything else" passes 15% in states with two or more of these.

## 3. Quality

- **3.1 One category vocabulary.** Done: every row has a `category_group`
  (Overture's thirteen top-level groups) and, for 92% of rows in the DC
  box, a `category_subgroup` (Overture's second level, about 110 values).
  OSM tags and register categories are mapped onto both.
- **3.2 Trade name aliases.** Looked at on 2026-10-07 and set aside for
  salons: most unmatched salon licenses are stylists renting a chair in a
  shared salon-suite building, licensed under a name the sign does not
  show. Still worth a look for restaurants and bars.
- **3.3 Score calibration.** Build a labeled set (places with both a
  register verdict and an independent one) and fit `open_score` to it
  instead of the current rule of thumb.
- **3.4 Names and categories for places minted from registers.** Done:
  title case, store numbers stripped, the trade name after "dba", and a
  category read from the name where the name states one. Still to do:
  carry the register's own business type where it has one (license class).
- **3.5 Duplicates inside Overture.** Done for fuel: the rows a forecourt
  has under each brand it has had are one place (SPEC.md section 6). The
  generic-word fold Vela's map bake uses was measured and left to readers
  (section 9). In the full layer OSM now picks the name of a merged lot
  no locator spoke for. Still to do: look for other kinds of place that
  are one per lot.
- **3.6 Listings only Overture has.** First step done: the source Overture
  took a place from is published and sets the starting score of a place
  with no evidence (SPEC.md section 7). Still to do: fit those numbers
  instead of setting them by hand (with 3.3), test more kinds of place,
  and decide whether company-record listings at a home or an office suite
  belong in a map of places at all.

## 4. Operations

- **4.1 Monthly change file.** Built: each release compares its status
  files with the release before and publishes `changes.parquet`. It first
  produces something at the second release that has status files. That is
  also what will measure id churn.
- **4.2 Tests on every push.** Done: matcher tests, a syntax check of every
  script, and a check that every adapter is documented.
- **4.3 Failures.** Done: a state whose build fails is tried once more,
  and the release notes name any state left out. A source whose adapter
  fails keeps last run's file, so one portal being down does not stop the
  build.
- **4.4 Source watch.** Done: each build compares every register file with
  the one before. A file that lost more than half its rows is not used
  (last run's is), a file that moved by more than a fifth is flagged, and
  the list rides along as `source-watch.txt` and in the release notes.
  Still to do: notice a layout change that keeps the row count.

- **4.5 Held records.** Done for Missouri's "out of business" list and
  Colorado's expired and surrendered list: each
  build adds the current list to a file that rides along as a release
  asset (`held.tar.gz`), unused until there is enough to test. Also held
  from 2026-10-07: every record that was on an active register one run and
  is gone the next, dated the day it was first missed (`vanished.csv`).
  That is the closure signal with the best chance of working for the long
  tail, because it sees an ending when it happens. It can be tested from
  the third monthly build on. Next:
  Florida's weekly emergency closures, and the test itself once a few months have piled up.

## 5. Readers

Work in this repo that makes the files easier to consume. Changes to Vela
itself happen in Vela.

- **5.1 Region ids in the manifest.** Done: each region carries its country,
  its ISO 3166-2 code and the names of the OSM extracts it was built from.
- **5.2 A small status file per state.** Done: `status-<region>.parquet`.

## 6. Other countries

- **6.1 France, whole country.** Regions, a full SIRENE run, license check.
- **6.2 United Kingdom.** Food hygiene ratings, then Companies House.
- **6.3 Addresses where the number follows the street**, which unlocks
  Germany, Spain and Italy for the global signals.
- **6.4 Canada**, province by province.

Each country starts with the global signals alone, then gains registers.

## 7. Contributions

- **7.1 A simple way for a map user to confirm a place** that lands in
  OpenStreetMap as a survey date or a closure tag, and so in the next build.
- **7.2 Owner updates**, if 7.1 proves people use it.

## 8. Hours, popularity, reviews

Asked for by the owner on 2026-10-07.

- **8.1 Hours from what is already open.** Done: `opening_hours` from
  AllThePlaces and OSM, with its source and date.
- **8.2 Hours from website markup already collected by others.** Measured
  and set aside on 2026-10-07. Web Data Commons (December 2024, from
  Common Crawl) has schema.org LocalBusiness markup from 1.46 million
  sites, 254,000 of them with opening hours. Places whose own website is
  one of those: 866 of 101,082 in the DC box and 563 of 63,574 in a
  Seattle box, under 1%. Not worth 23 GB of two-year-old data.
- **8.3 A crawler of our own.** First measurement, 2026-10-07: the home
  pages of 400 independent places in the DC box that have a website and
  no hours, fetched once each, robots.txt obeyed. 28 (7%) carry opening
  hours markup, 17 more (4%) state hours in plain text, 218 (55%) say
  nothing about hours on the home page, 10 forbid crawlers, and 127 (32%)
  did not answer at all. So a home page crawler would add hours to about
  one in fourteen of those places. Still to measure before building it:
  whether contact and hours pages raise that, how right the markup is
  against OSM and AllThePlaces hours, and whether the third of sites that
  do not answer says anything about the place being closed (an earlier
  note in SPEC.md section 9 says website liveness was not retested).
  Rules if built: schema.org markup only, robots.txt obeyed, a few pages
  per site per month, the project User-Agent.
  On hold by the owner's decision of 2026-10-07: registers come first. The
  crawler is to be built later, robust and for every country, as its own
  project or as an add-on once the rest is in place.
- **8.4 Popularity.** No open source has foot traffic. A stand-in can be
  built from what is open: how many sources list the place, Wikipedia page
  views for places with an article, how often mappers touch it. To be
  tested before it is called popularity.
- **8.5 Reviews.** A separate project. Mangrove (open reviews, CC BY) is
  the only open review set found so far and it is small. Nothing here
  until the owner decides where reviews would be stored.
- **8.6 Owners keeping their own listing current.** Open question. The
  cheapest form is 7.2: an owner edits OSM, or their own site's markup,
  and the next build picks it up.

## Standing decisions

Set by the owner on 2026-10-06.

- **Test areas.** The fixed ones (a District of Columbia box, Sacramento and
  Davis, Delaware, Kentucky, Paris) plus, for any other state, a box around
  that state's largest city. A table that covers one city or county is
  tested in that city (2026-10-12).
- **Keys.** None for now. Sources that need a key wait.
- **Licenses.** Decided 2026-10-12: public data is used even where its
  terms are unclear or restrictive, with the terms as found and the
  decision written in SOURCES.md and the rows labelled with the source's
  own terms. Before that day only public domain, CC0, ODbL, CC BY, open
  government licences, Common Crawl's terms and unlicensed US public
  records were taken. A page that blocks the project (403, challenge
  page, CAPTCHA, login) is still never worked around.
- **Order.** Section 1 first.
- **Search-form registers.** Decided 2026-10-07: build crawlers for the state
  registers that only offer a search form (liquor licenses, restaurant
  inspections), because that is a bounded list of real places. This is not
  the website crawler for hours (8.3), which stays on hold.
- **robots.txt.** Followed by default. The owner decides exceptions one site
  at a time for public registers (first: Pennsylvania's license export,
  2026-10-07). Blocks and CAPTCHAs are never worked around.
- **Unvouched listings.** How a reader shows them (hide, dim, or both) is
  decided later, once the data is in. The columns are there.
- **Clinical laboratories.** Worth adding, low priority.
- **France and other countries.** Parked.
- **New York outside the city.** Buffalo is the test area for sources that
  leave New York City out (2026-10-07).
- **Git history** stays as it is; no rewrite (2026-10-07).

## What needs the owner

Everything above can proceed without asking, except these.

- **Keys and accounts**, if that decision is revisited, and where a key
  would be stored.
- **License calls** outside the list above.
- **Anything that costs money or needs a server** beyond GitHub Actions and
  release storage.
- **Speaking for the project**: contacting another project or a data owner.
- **Deleting a release.**
- **A source or rule that fails in a way the rules above do not settle.**
