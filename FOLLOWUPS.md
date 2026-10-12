# To circle back on

Sources that exist and could not be used yet, and what would unblock each.
Newest findings first within a group. SOURCES.md has the addresses.

## Needs someone to ask

- **Maricopa County, Arizona: food permits** (105,000, with positions; all
  of Phoenix). The layer's terms say county internal use only, and that
  outside use needs written authorization from the county GIS office.
  Ask for it.
- **Virginia Beach business licenses** (42,000). The terms were not read
  in full; read them, and ask if they are unclear.
- **Indiana alcohol licenses**: sold per record. **Utah DOPL lists** and
  **Oregon Board of Pharmacy**: paid list services. Ask whether a free
  copy is possible for an open dataset.
- **Georgia child care (DECAL)**: the export button needs the site's own
  token. Ask for a file.

## The site turns the project's fetches away

Nothing is done to get around these. They may open up, or answer a request.

- **Massachusetts ABCC** active retail licenses (.xls): "Not allowed" on
  the second fetch.
- **Michigan MLCC** weekly license spreadsheet: 403.
- **Virginia ABC** license search: 403.
- **Arizona DLLC** license query: challenge page.
- **Alaska AMCO** and Alaska business license downloads: 403.
- **Maine health inspection search**: a reCAPTCHA on the search button.
- **Kansas Department of Agriculture**, **Rhode Island DOH lists**,
  **Colorado DORA roster generator**, **New Hampshire liquor**: 403.

## Stale, check again later

- **Albuquerque business registrations**: export stopped at 2025-08-30.
- **Anchorage food inspections**: stopped advancing in May 2026.
- **Arizona child care layer**: last run February 2025 (used, with that date).
- **Maryland child care**: May 2024 snapshot. **Kentucky child care**:
  layer stops at exactly 2,001 rows.
- **Colorado tobacco licenses**: one unexpired row of 4,910.
- **Hawaii food establishments**: 2011 and 2020 files.
- **Kansas City, Providence, Baltimore** city files: years old.
- **Sioux Falls alcohol licenses**: no dates in the layer at all.
- **Southern Nevada restaurant inspections**: rows have no names.
- **Newark, New Jersey open data portal**: answered 503 throughout.
- **Ohio liquor permit lookup**: connection resets.

## Search forms not crawled yet

- **Philadelphia restaurant inspections.** The state lookup lists the city
  as a jurisdiction but returns nothing for it (24 establishments in the
  whole county), so the 43,000 Pennsylvania establishments read are the
  rest of the state. Philadelphia needs its own source. (Allegheny
  County's own list was added on 2026-10-12.)
- **South Dakota inside Sioux Falls** is the city's own list (already read);
  the state list has almost nothing there, as expected.
- **Wyoming food inspections** (`wda.safefoodinspection.com`): the same
  system as eight states already read, but every search answers with a
  server error. Try again later.
- **Kentucky restaurants**, **Illinois counties**, **Salt Lake County** on
  `public.cdpehs.com` (the same vendor as North Carolina, different pages).
  The whole host answered 502 on 2026-10-12, North Carolina included; find
  the pages once it is back.
- **Oklahoma inspection dates.** The list is read without them. A request
  per establishment would date each one (about 25,000 requests).
- **Minnesota AGED** liquor license lookup (a JavaScript app).
- **Illinois ILCC** license lookup (a Salesforce site).
- **Anchorage** and **Columbus**-style county portals (one request lists
  every facility, but dates need a request per facility).
- **Missouri professional registration downloads** (moved to a Salesforce page).
- **South Carolina, Louisiana, Mississippi** alcohol license searches. No
  public business-permit search was found for Louisiana (2026-10-12).
- **Utah DABS licensee list**: a Looker Studio report, no file.
  **Vermont DLL licensee database**: behind a Salesforce login page.
- **Orlando business tax receipts** (119,000): addresses have no ZIP, which
  the address matcher needs. Could be read with the city as the ZIP's stand-in.

## Closed portals (403 or a challenge page), nothing to do but ask

- **inspections.myhealthdepartment.com**: Tennessee and Virginia
  restaurants, Hawaii, Oregon, Cuyahoga County, El Paso and Weld County
  CO, Orange County CA and more.
- **Riverside, Santa Clara, St. Louis County, Baltimore County, Louisiana,
  Rhode Island, New Hampshire** restaurant lookups.

## Held signals waiting for enough months to test

- Records that vanish from a register between runs (`vanished.csv`).
- Missouri "out of business" alcohol licenses, Colorado expired and
  surrendered licenses.
- Pennsylvania licenses in safekeeping. First look, Philadelphia box: of
  23 that matched a place, other sources called 3 closed and 9 open.
- California delinquent salon and repair shop licenses (not collected yet).
- San Francisco business locations with an end date (59% right on first look).
- Detroit restaurant establishments marked "Permanently Closed" (1,449, no date in the layer; not collected yet).

## Low priority, known to work

- **Clinical laboratories** (CMS CLIA, 300,000 rows, no positions).
