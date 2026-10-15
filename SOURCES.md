# Sources

Every source the build reads, with its license and where it is fetched from.
All are anonymous and keyless. A source is added here before its importer or
adapter is merged. If a source states no license, the entry says so.

## Base layer

### Overture Maps, places theme
- License: CDLA-Permissive-2.0. Rows that came from Foursquare are Apache-2.0
  (each row's `sources` says which).
- Fetched from: `https://overturemaps-us-west-2.s3.amazonaws.com/release/<release>/theme=places/type=place/`
- Docs: https://docs.overturemaps.org/
- Attribution: Overture Maps Foundation, overturemaps.org.
- Used for: the spine of the place table.

### OpenStreetMap, via Geofabrik state extracts
- License: ODbL-1.0. Share-alike. Anything derived from it is in the full
  layer only.
- Fetched from: `https://download.geofabrik.de/north-america/us/<state>-latest.osm.pbf`
- Attribution: (c) OpenStreetMap contributors, https://www.openstreetmap.org/copyright
- Used for: named businesses and landmarks, lifecycle tags (closed),
  `check_date` tags (open), `wikidata` links.

### AllThePlaces
- License: CC0-1.0.
- Fetched from: `https://data.alltheplaces.xyz/runs/latest.json`, then the
  run's `output.zip`. The `parquet_url` in that file returns 404 as of
  2026-10; the zip is what works.
- Site: https://www.alltheplaces.xyz/
- Used for: chain locations (brand lineage spiders only), and open evidence
  dated the day the spider ran.

## Evidence

### Foursquare OS Places
- License: Apache-2.0. See NOTICE.
- Fetched from: `https://data.source.coop/fused/fsq-os-places/2025-02-06/places/<0..80>.parquet`
  (an anonymous mirror of the 2025-02-06 release).
- Newer releases need a Foursquare account. `signals/fsq_closed.sh` takes
  `FSQ_PLACES_GLOB` and `FSQ_RELEASE` for that; no token is stored in the repo.
- Used for: `date_closed`, joined on the Foursquare id Overture carries.

### OpenPOIs (Henry Spatial Analysis)
- License: ODbL-1.0 for the data. Full layer only.
- Fetched from: `https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/henryspatialanalysis/openpois/latest/conflated-parquet/`
- Project: https://github.com/henryspatialanalysis/openpois
- Used for: OSM edit history events matched to Overture places (closed),
  and its confidence as the open score of places with no other evidence,
  when 0.80 or more. US only.

### Wikidata
- License: CC0-1.0.
- Fetched from: `https://query.wikidata.org/sparql`
- Used for: P576 on items linked from OSM features.

### FDIC BankFind Suite
- License: US federal government work, public domain.
- Fetched from: `https://api.fdic.gov/banks/locations` and
  `https://api.fdic.gov/banks/history` (change code 721, branch closing).
- Docs: https://api.fdic.gov/banks/docs/
- Used for: open bank branches, dated branch closings.

### USDA SNAP retailer data
- License: US federal government work, public domain.
- Fetched from: the historical file linked on
  https://www.fns.usda.gov/snap/retailer/historical-data and the live layer at
  `https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0`
- Used for: stores currently authorized (open). End dates are not used; see
  SPEC.md section 9.

### EPA UST Finder
- License: US federal government work, public domain.
- Fetched from: `https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/UST_Finder_Feature_Layer_2/FeatureServer`
- Used for: sites with underground fuel tanks in use (open). The layer was
  last edited in December 2024.

### CMS Hospital General Information
- License: US federal government work, public domain.
- Fetched from: the CSV named in
  `https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u`
- Used for: Medicare-registered hospitals (open). No positions; matched by address.

### NCES public school locations (EDGE geocodes)
- License: US federal government work, public domain.
- Fetched from: `https://nces.ed.gov/programs/edge/data/EDGE_GEOCODE_PUBLICSCH_<years>.zip`
- Used for: public schools that operated in the file's school year (open).

### NPPES, the National Provider Identifier registry
- License: US federal government work, public domain.
- Fetched from: the monthly file linked on https://download.cms.gov/nppes/NPI_Files.html
- Used for: health care organizations (open, dated by the last update or
  certification). No positions; matched by address.

### NCUA quarterly call report data
- License: US federal government work, public domain.
- Fetched from: `https://ncua.gov/files/publications/analysis/call-report-data-<year>-<month>.zip`
- Used for: credit union offices (open, dated by the quarter). No positions;
  matched by address.

### IRS Exempt Organizations Business Master File
- License: US federal government work, public domain.
- Fetched from: `https://www.irs.gov/pub/irs-soi/eo1.csv` to `eo4.csv`
- Used for: nonprofits that filed a return (open, dated by the tax period).
  No positions; matched by address.

### California ABC daily license export
- License: none stated on the download page. California public record.
- Fetched from: `https://www.abc.ca.gov/wp-content/uploads/DailyExport-CSV.zip`,
  linked on https://www.abc.ca.gov/licensing/licensing-reports/
- Used for: active retail alcohol licenses (open), with positions from the
  Census geocoder. The file gives no date for surrenders or revocations, so
  there is no closed evidence from it.

### New York City DOHMH, restaurant inspection results
- License: none named on the dataset. NYC Open Data, a city public record;
  rows it touches are marked `NYC-Open-Data-terms`.
- Fetched from: `https://data.cityofnewyork.us/resource/43nn-pn8j.json`
- Used for: restaurants by newest inspection (open), with positions. Also
  mints missing places.

### King County, Washington, food establishment inspections
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.kingcounty.gov/resource/r878-4sxa.json`
- Used for: food businesses by newest inspection in the last three years
  (open), with positions from the Census geocoder.

### Chicago Department of Public Health, food inspections
- License: "See Terms of Use" of the City of Chicago Data Portal; rows it
  touches are marked `Chicago-Data-Portal-terms`.
- Fetched from: `https://data.cityofchicago.org/resource/4ijn-s7e5.json`
- Used for: food businesses by newest inspection (open), and the "Out of
  Business" result (closed, places with no brand only). Positions come
  with the data. Also mints missing places.

### Colorado Liquor Enforcement Division, liquor licenses
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.colorado.gov/resource/ier5-5ms2.json`
- Used for: active premises licenses (open). The list of recently expired
  and surrendered licenses is not used.

### Oregon Liquor and Cannabis Commission, liquor licenses
- License: none stated. Oregon public record. Rows it touches are marked
  `none-stated`.
- Fetched from: `https://data.oregon.gov/resource/srxe-qkm2.json`
- Used for: unexpired premises licenses (open), with positions from the
  Census geocoder. Expired licenses are not used; see SPEC.md section 9.

### Missouri Division of Alcohol and Tobacco Control, active licenses
- License: none stated. Missouri public record. Rows it touches are marked
  `none-stated`.
- Fetched from: `https://data.mo.gov/resource/yyhn-562y.json`
- Used for: active premises licenses (open), with positions from the Census
  geocoder. The file names each license's manager; that field is not read.

### Chicago BACP, business licenses
- License: "See Terms of Use" of the City of Chicago Data Portal; rows it
  touches are marked `Chicago-Data-Portal-terms`.
- Fetched from: `https://data.cityofchicago.org/resource/r5kz-chrr.json`
- Used for: sites with a live license (open), and sites whose newest
  record is a cancellation (closed, places with no brand only). Positions
  come with the data.
- Privacy: the legal name is not read, and nothing creates a place from
  this source.

### Florida DBPR, alcoholic beverage licenses
- License: none stated on the download page. Florida public record. Rows it
  touches are marked `none-stated`.
- Fetched from: `https://www2.myfloridalicense.com/sto/file_download/extracts/bd400lic.csv`
- Used for: current retail beverage licenses (open), with positions from
  the Census geocoder.

### Florida DBPR, food service inspections
- License: none stated on the download page. Florida public record. Rows it
  touches are marked `none-stated`.
- Fetched from: `https://www2.myfloridalicense.com/sto/file_download/extracts/<1..7>fdinspi.csv`,
  linked on https://www2.myfloridalicense.com/hotels-restaurants/public-records/
- Used for: restaurants inspected in the current fiscal year (open, dated
  by the inspection), with positions from the Census geocoder.

### Philadelphia Licenses and Inspections, business licenses
- License: none stated on the table. City public record via OpenDataPhilly;
  rows it touches are marked `none-stated`.
- Fetched from: `https://phl.carto.com/api/v2/sql` (table `business_licenses`)
- Used for: active company-held licenses for food, vehicle repair and fuel,
  child care, tire and precious metal businesses (open), with positions.
- Privacy: rental licenses and licenses held by individuals are not read.

### City of Seattle, business license locations
- License: none stated beyond an accuracy disclaimer. City public record;
  rows it touches are marked `none-stated`.
- Fetched from: `https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Seattle_Business_License/FeatureServer/0`
- Used for: active business locations in retail, food and lodging,
  recreation, and repair and personal services (open), with positions.
- Privacy: the file covers every business in the city, home businesses
  included. Only storefront industry codes are read, only the trade name
  and location address, never the contact fields, and nothing creates a
  place from it.

### City and County of Denver, active business licenses
- License: none stated on the layer. City public record; rows it touches
  are marked `none-stated`.
- Fetched from: `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_active_business_licenses/FeatureServer/42`
- Used for: active licenses for food, liquor, tobacco and marijuana stores,
  repair garages, lodging, body art, kennels and similar (open), with
  positions from the Census geocoder.
- Privacy: residential and short-term rental licenses, four fifths of the
  file, are not read.

### Tobacco retailer lists (New York, Pennsylvania, Texas)
- License: New York under the OPEN-NY Terms of Use; Pennsylvania and Texas
  public domain, as stated on the datasets.
- Fetched from: `https://data.ny.gov/resource/55xf-9jat.json`,
  `https://data.pa.gov/resource/ut72-sft8.json`,
  `https://data.texas.gov/resource/n4rp-ar9b.json`
- Used for: retail locations with a current cigarette, tobacco or vapor
  registration (open). Mostly convenience stores, delis, gas stations and
  smoke shops.
- Privacy: New York gives the registrant's name, which can be a person, so
  nothing creates a place from these lists. Pennsylvania's legal name and
  Texas's taxpayer name are not read.
- Not used: Colorado's tobacco license list (`data.colorado.gov` ejz2-rwds).
  On 2026-10-07 one of its 4,910 rows had an expiry date still ahead.

### Connecticut state licenses and DMV dealers and repairers
- License: public domain, as stated on both datasets.
- Fetched from: `https://data.ct.gov/resource/ngch-56tr.json`,
  `https://data.ct.gov/resource/apne-w8c6.json`
- Used for: active shop-front license types (liquor, bakeries, dairy
  stores, pharmacies, vapor dealers, lottery agents, gasoline dealers,
  child care centers, funeral homes, health clubs, kennels, opticians) and
  unexpired dealer, repairer and recycler licenses (open).
- Privacy: of 2.7 million credentials only business license types are
  read. The DMV list has people's names among its trading names, so
  nothing creates a place from it.

### City of New Orleans, active occupational licenses
- License: CC0, as stated on the dataset.
- Fetched from: `https://data.nola.gov/resource/iqay-p646.json`
- Used for: businesses with an active license (open), with positions.
- Privacy: home-based, driver and street vendor trades are not read, nor
  the owner name and phone columns, and nothing creates a place from it.

### Washington vehicle dealers and child care centers
- License: dealers under the Open Database License, as stated on the
  dataset; child care list states none and is marked `none-stated`.
- Fetched from: `https://data.wa.gov/resource/ucdg-xgbj.json`,
  `https://data.wa.gov/resource/was8-3ni8.json`
- Used for: active dealer licenses and active child care centers (open).
- Privacy: the contact person, phone and email columns are not read.

### Colorado licensed child care facilities
- License: Open Data Commons Public Domain Dedication and License.
- Fetched from: `https://data.colorado.gov/resource/a9rr-k8mu.json`
- Used for: centers, preschools and school-age programs (open).
- Privacy: family child care homes are not read.

### Florida DBPR, establishment licenses
- License: none stated. Florida public records; rows are marked `none-stated`.
- Fetched from: `https://www2.myfloridalicense.com/sto/file_download/extracts/`
  (`COSMETOLOGYLICENSE_1.csv`, `lic03bb.csv`, `lic26vt.csv`,
  `hrlodge1..7.csv`, `hrfood1..7.csv`)
- Used for: current salon, barbershop, veterinary premises, hotel, motel,
  bed and breakfast and fixed-premises restaurant licenses (open).
- Privacy: the profession files are mostly individual license holders,
  which are not read. Vacation rentals, condominiums and apartments in the
  lodging files are not read. Nothing creates a place from these files.

### New York Office of Cannabis Management, current licenses
- License: OPEN-NY Terms of Use.
- Fetched from: `https://data.ny.gov/resource/jskf-tt3q.json`
- Used for: retail dispensaries with an active license that the state
  marks as operating (open).
- Privacy: the contact name column is not read.

### New York State Department of Health, food service inspections
- License: OPEN-NY Terms of Use.
- Fetched from: `https://health.data.ny.gov/resource/cnih-y5dw.json`
- Used for: food service operations with an unexpired permit, dated by
  their last inspection (open), with positions. New York City, Suffolk
  County and Erie County are not in the file.
- Privacy: the operator name columns are not read.

### City of Boston, food licenses, inspections and Licensing Board licenses
- License: Open Data Commons Public Domain Dedication and License, as
  stated on each dataset.
- Fetched from: `https://data.boston.gov/datastore/dump/<resource>` for
  `active-food-establishment-licenses`, `food-establishment-inspections`
  and `licensing-board-licenses`
- Used for: active food establishment licenses, establishments dated by
  their newest inspection, and active Licensing Board licenses (open).
- Privacy: the owner, applicant, manager and phone columns are not read.

### State alcohol license lists found on agency sites (2026-10-07)
None of these pages states a license; rows are marked `none-stated`. In
each, only the trading name and premises address are read, never the
licensee, owner, manager or phone columns, and nothing creates a place.
- Washington LCB: on-premises and off-premises spreadsheets linked from
  `https://lcb.wa.gov/records/frequently-requested-lists` (dated file names)
- New Jersey ABC: retail license report linked from
  `https://www.njoag.gov/about/divisions-and-offices/division-of-alcoholic-beverage-control-home/licensing-bureau-applications-and-information/licensing-reports/`
  (monthly). Licenses with an inactivity date are not read.
- Wisconsin DOR: `https://ww2.revenue.wi.gov/WebServicesPublicWeb/rest/liquor/all` (CSV)
- Nebraska LCC: roster linked from `https://lcc.nebraska.gov/licensing-sdl/active-license-roster`
- Maine BABLO: file linked from `https://www.maine.gov/dafs/bablo/liquor-licensing/license-data`
- Idaho State Police ABC: `https://apps.isp.idaho.gov/AbcReporting/license/search/csv?licenseTypes=retail&status=ISSUED`
- Arkansas ABC: `https://www.dfa.arkansas.gov/wp-content/uploads/FullPermitYYYYMM.xlsx` (monthly)
- Oklahoma ABLE: one list per license type linked from
  `https://oklahoma.gov/able-commission/brand-registration/brand-registration-reports/listing-of-licensees-by-license-type.html`
- Not used yet: Massachusetts ABCC publishes its active retail licenses as
  an old binary .xls (`https://www.mass.gov/doc/abcc-active-retail-licenses/download`),
  which needs a reader the build does not have. On a second fetch the
  site answered "Not allowed" to this project's User-Agent, so it is left
  alone.
- Looked for and not found as a file: Pennsylvania, Ohio, Illinois,
  Michigan, Virginia, North Carolina, Arizona, Minnesota, South Carolina,
  Louisiana, Kansas, Utah, Vermont (search forms or blocked pages), and
  Indiana (sold per record).

### State alcohol registers read through their search forms (2026-10-07)
None states a license; rows are marked `none-stated`. Owner, licensee,
corporation and agent columns are not read.
- North Carolina ABC Commission: `https://abc2.nc.gov/Search/Permit`, asked
  once per county for active permits, reading the form's own spreadsheet
  export (200 requests). No robots.txt.
- Kentucky ABC: `https://abcportal.ky.gov/BelleExternal/ReportGenerator/Reports`,
  the "All Active Licenses" report for the whole state, reading its CSV
  export (4 requests). No robots.txt.
- Kansas ABC: `https://www.kdor.ks.gov/apps/liquorlicensee/LiquorLicenseeSearch.aspx`,
  asked once per license group, 500 rows a page (about 20 requests).
  robots.txt allows the page.
- Pennsylvania PLCB: the CSV of all licenses linked from its search page,
  `https://plcbplus.pa.gov/pub/LicenseExport.aspx` (2 requests). The
  site's robots.txt disallows everything except the search pages. The
  owner decided on 2026-10-07 to read the export anyway: it is the board's
  own public download button, and it is fetched once a month. Licenses in
  safekeeping are held, not used.
- Not read, because the site says no:
  - Tennessee's retail food list (`tnlcp.lcp.tracefirst.com`): robots.txt
    disallows the whole site.
  - Michigan MLCC, Virginia ABC, Arizona DLLC, Alaska AMCO: the sites
    answer 403 or a challenge page to this project's fetches.

### Food registers read a page at a time (2026-10-07)
None states a license; rows are marked `none-stated`.
- Tennessee Department of Agriculture retail food stores:
  `https://tnlcp.lcp.tracefirst.com/public_weblinks/food-safety-retail`,
  657 pages of 15. The site's robots.txt disallows the whole site; the
  owner decided on 2026-10-07 to read public registers like this anyway.
- North Carolina environmental health inspections, all 100 counties:
  `https://public.cdpehs.com/NCENVPBL/`, each county's search page asked
  for its CSV six months at a time (800 requests). No robots.txt. The
  inspector column is not read. Asking for two years at once fails
  without an error for the largest counties, which is why it is split.
- The "Food Safety" inspection system eight states share
  (`.../Inspection/PublicInspectionSearch.aspx`), read county by county,
  15 establishments a page, by `adapters/usafoodsafety.py` on its own
  schedule (`.github/workflows/crawl.yml`):
  Alaska `adec.safefoodinspection.com`, Arkansas
  `foodserviceprod.adh.arkansas.gov`, Iowa `iowa.safefoodinspection.com`,
  Kansas `foodsafety.kda.ks.gov`, North Dakota `fims.doh.nd.gov`,
  Pennsylvania `www.pafoodsafety.pa.gov`, South Dakota
  `sddoh.safefoodinspection.com`, Vermont `vtdoh.safefoodinspection.com`.
  None has a robots.txt. A search shows at most 500 establishments;
  Pennsylvania's large counties are split by inspection date to fit. Phone
  numbers are not read.
- Georgia environmental health inspections, all counties:
  `https://ga.healthinspections.us/stateofgeorgia/API/index.cfm/facilities/<page>`,
  five permits a request, newest inspection first, read to the end
  (about six thousand requests) by `adapters/dph_ga_inspections.py` on
  the slow schedule. Food service and tourist accommodation permits are
  kept, swimming pools are not. No robots.txt. Phone numbers are not read.
- Mississippi food facility inspections:
  `https://apps.msdh.ms.gov/food/FacilityListingDatesExport.aspx`, an
  export of every inspection between two dates; two years are read two
  months at a time (a dozen requests). No robots.txt. Grades are not read.
- Alabama food establishment scores: `https://foodscores.state.al.us/`,
  asked county by county and kind by kind (about 700 requests). The site
  keeps its session in the address. No robots.txt. Scores are not read.
- Oklahoma food service establishments:
  `https://www.phin.state.ok.us/inspections/`, county by county, 15 a
  page (about 1,700 requests). The list has no dates; an establishment's
  inspections are a request each and are not read. No robots.txt.
- Mapped and not read yet: Kentucky, Illinois counties and Salt Lake
  County on `public.cdpehs.com` (other pages of the vendor North Carolina
  uses; the whole host answered 502 on 2026-10-12). See FOLLOWUPS.md.
- Maine's health inspection search
  (`apps.web.maine.gov/online/hip_search/`) puts a reCAPTCHA on its
  search button. Left alone.
- Closed to this project: `inspections.myhealthdepartment.com` (Tennessee
  and Virginia restaurants, Hawaii, Oregon, Cuyahoga County and others)
  answers 403; Riverside, Santa Clara, St. Louis County and Baltimore
  County sit behind challenge pages.

### Colorado Department of Public Health and Environment, alcohol outlet points
- License: none stated. Colorado public record; used only for positions.
- Fetched from: `https://www.cohealthmaps.dphe.state.co.us/arcgis/rest/services/PSD/CDPHE_Alcohol_Outlet_Density/MapServer/0`
- Used for: the position of a Colorado liquor license, joined by license
  number, when that license adds a place (`data/cache/evidence/pins/led_co.csv`,
  written by `adapters/led_co.py`). Only points marked "Point Accuracy".

### Address points, by way of Overture's address theme
- License: Overture attaches a license to each address's source. Read are
  the National Address Database (US federal work, public domain), county
  files public domain under California or Florida law, Ada County, Idaho
  (CC BY 4.0, credited in NOTICE), and files Overture marks
  `LicenseRef-Proprietary` (Colorado, Oregon, Mississippi, New York City,
  Los Angeles County). The owner decided on 2026-10-12 to use the last
  group too: only a position is taken from any of them, for a register
  row that adds a place, and no address is published.
- Fetched from: `s3://overturemaps-us-west-2/release/<release>/theme=addresses/type=address/`
  (`base/addresses.sh`)

### Address points from county and state layers
Overture's address theme is bare in places (Pittsburgh, Charleston,
Oakland, most of Oklahoma, Las Vegas, New Orleans, Detroit, Milwaukee).
`base/address_layers.py` reads public layers for some of them into
`data/cache/addresses/`, and the build reads those beside Overture's.
Only a position is taken, as above; no address is published.
- Allegheny County, Pennsylvania, address points (663,000 active):
  `https://gisdata.alleghenycounty.us/arcgis/rest/services/Addressing/Addressing_AddressPoints/MapServer/0`.
  "For informational purposes only", no license.
- Alameda County, California, address points (637,000):
  `https://services5.arcgis.com/ROBnTHSNjoZ2Wm1P/arcgis/rest/services/Address_Points/FeatureServer/0`.
  No terms stated.
- Charleston County, South Carolina (70,000, the unincorporated county
  and small towns) and City of Charleston (58,000):
  `https://services.arcgis.com/jR9eNCjAkxwH2nLe/arcgis/rest/services/Charleston_County_Addresses/FeatureServer/0`,
  `https://services2.arcgis.com/tQaXW7Zb1Vphzvgd/arcgis/rest/services/City_Addresses/FeatureServer/0`.
  The county's notice cites SC Code 30-2-50, which bars using personal
  information from public records for commercial solicitation; an
  address point holds none.
- Oklahoma NG911 address points (1.9 million), the public release from
  okmaps.org as hosted by the University of Oklahoma:
  `https://services.arcgis.com/3xOwF6p0r7IHIjfn/arcgis/rest/services/NG911_Address_Points/FeatureServer/0`.
  No terms stated.
- City of Philadelphia address index (862,000 points on a parcel or a
  911 point; those placed along a street range are left out):
  `https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/AIS_Address_Points/FeatureServer/0`.
  City of Philadelphia open data; no license stated on the layer.
- Milwaukee County address points (464,000 active):
  `https://services2.arcgis.com/s1wgJQKbKJihhhaT/arcgis/rest/services/Milwaukee_County_Address_Points/FeatureServer/56`.
  No terms stated.
- Not found yet: Las Vegas (Clark County publishes only its newest 27,000
  points), New Orleans (`gis.nola.gov` serves a site address layer whose
  certificate Python cannot check; left alone), Detroit (its open layer
  holds 1,042 points).
  Wisconsin's statewide NG911 layer has no ZIP field, which the address
  key needs. A layer titled for Wayne County turned out to be Ohio's.
- Used for: the position of a register row that has only an address, when
  that row adds a place. Not used to match.

### Tables found by searching the open data catalog (2026-10-12)
Read by `adapters/open_data_tables.py`, one source per table. Owner,
contact, inspector, phone and email columns are not read; home day cares
are left out.
- Cambridge, Massachusetts, food establishment permits:
  `https://data.cambridgema.gov/d/iect-ma2e`. ODC Public Domain Dedication
  and License.
- Montgomery County, Maryland, alcohol licensees:
  `https://data.montgomerycountymd.gov/d/c6rw-fazn`. Public domain.
- New York State child care regulated programs:
  `https://data.ny.gov/d/cb42-qumz`. OPEN-NY terms.
- New York City active child care programs:
  `https://data.cityofnewyork.us/d/gy3q-4tzp`. NYC Open Data terms.
- Pennsylvania child care providers: `https://data.pa.gov/d/ajn5-kaxt`.
  Marked "Public Domain U.S. Government" by the publisher.
- Texas HHSC child care operations: `https://data.texas.gov/d/bc5r-88dy`.
  CC0.
- New Jersey vehicle inspection facility locations (private facilities):
  `https://data.nj.gov/d/t6tk-mr48`. No license stated; `none-stated`.
- New York State lottery retailers: `https://data.ny.gov/d/2vvn-pdyi`.
  OPEN-NY terms.
- New York City weights, measures and other tests (scales, fuel pumps,
  laundry dryers): `https://data.cityofnewyork.us/d/8fei-z6rz`. NYC Open
  Data terms. Pedicabs, fuel trucks and mobile vendors are left out.
- San Francisco registered business locations: `https://data.sf.gov/d/g8m3-pdis`
  (101,000 locations with no end date, with positions). ODC Public Domain
  Dedication and License. Owner names and mailing addresses are not read.
  Locations with an end date are held, not used.
- Los Angeles listing of active businesses: `https://data.lacity.org/d/6rrh-rzua`
  (632,000 rows, with positions). CC0.
- Austin food establishment inspection scores:
  `https://datahub.austintexas.gov/d/ecmv-9xxi`. Public domain.
- Cincinnati food safety program: `https://data.cincinnati-oh.gov/d/rg6p-b3h3`.
  Public domain.
- Boulder County restaurant inspections: `https://data.colorado.gov/d/6ytb-f2cq`.
  Public domain.
- Marin County food facility inspections:
  `https://data.marincounty.gov/d/73zb-z5me`. ODbL.
- East Baton Rouge Parish registered businesses:
  `https://data.brla.gov/d/xw6s-bcqm`. Public domain.
- Norfolk business licenses: `https://data.norfolk.gov/d/dpi6-sct5`, and
  Berkeley business licenses: `https://data.cityofberkeley.info/d/rwnf-bu3w`
  (landlords' licenses left out). No license stated; `none-stated`.
- Texas lottery sales by retailer: `https://data.texas.gov/d/beka-uwfq`,
  asked for each retailer's last month with sales. The table says "See
  Terms of Use" and points at the Texas Lottery's copyright page
  (`https://www.texaslottery.com/export/sites/lottery/Misc/copyright.html`).
  The owner decided on 2026-10-12 to use it; rows are marked
  `Texas-Lottery-terms`. Sales figures are not read.
- Texas Commission on Environmental Quality, operating dry cleaner
  registrations (plants and drop stations, 1,400 rows):
  `https://data.texas.gov/d/qfph-9bnd`. No license stated; `none-stated`.
  Billing addresses, customer names and phone numbers are not read.
  39 of 40 matches right in Houston. May add places (SPEC section 6).
- City of Fort Worth certificates of occupancy (72,000 since 2013; the
  3,300 of the last three years for shops, offices, assembly and school
  uses are read, with the occupant's name and the day issued):
  `https://services5.arcgis.com/3ddLCBXe1bRt7mzj/arcgis/rest/services/CFW_Open_Data_Certificates_of_Occupancy_Table_view/FeatureServer/0`.
  The city releases its open data under CC BY 4.0; rows are marked
  `CC-BY-4.0` and the city is credited in NOTICE. A new kind of source:
  a list of openings. Occupancy certificates may add places when the
  name reads as a shop (SPEC section 6); certificates that close a
  building permit are the separate source `fw_co_build` and never do.
  Looked for the same in other cities on 2026-10-13 and found none as
  good: Los Angeles (`data.lacity.org/d/3f9m-afei`), New York City,
  Seattle (`axkr-2p68`), Montgomery County, Maryland (`2fhm-xt6p`),
  Cambridge (`qwvv-deed`), Detroit, Tucson and Baltimore County certify
  buildings and name no occupant; Dallas names the business but stopped
  in 2022 (`www.dallasopendata.com/d/9qet-qt9e`); Miami-Dade's
  certificates of use (147,000 since 2003, layer
  `CertificateOfUse_New_gdb`) name the corporation and, as the trade
  name, often the applicant, and the county's business tax layer already
  lists the same businesses.
- Clark County, Nevada, business licenses (unincorporated county: the
  Strip, Paradise, Spring Valley, Enterprise), with each license's first
  issue date:
  `https://maps.clarkcountynv.gov/arcgis/rest/services/BusinessLicense/BusinessLicenseData/FeatureServer/1`.
  74,000 in force; 40,700 read once kinds with no door (property
  management, rentals, contractors, brokers, gaming routes, tax accounts)
  are left out. No license stated; `none-stated`. Phone numbers are not
  read.
- Southern Nevada Health District (Clark County: Las Vegas, Henderson,
  North Las Vegas), food establishment permits, from the district's
  nightly file for developers:
  `https://www.southernnevadahealthdistrict.org/restaurants/download/restaurants.zip`
  (described at `.../permits-and-regulations/restaurant-inspections/developers/`).
  The page offers the file for download and states no license;
  `none-stated`. Read: active permits (17,600). Not read: owner ids,
  inspections, violations, and the 16,500 inactive permits, which carry
  no end date. The file's latitude and longitude columns are swapped.
- Los Angeles County Department of Public Health, Environmental Health
  restaurant and market inventory (37,000 facilities; Pasadena, Long
  Beach and Vernon keep their own). Published each quarter as a new layer
  with the date in its name, so `adapters/lac_food.py` finds the newest
  by searching the county's ArcGIS account (`orgid:RmCCgQtiZLDCtblq`);
  the layer of 2026-09-30 is
  `https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Environmental_Health_Restaurant_and_Market_Inventory_09-30-2026/FeatureServer/0`.
  No license stated; `none-stated`. Owner names and addresses are not
  read. The county also publishes inspections and violations as CSV
  items; not read.
- San Diego County food facility permits (active, 13,000 fixed premises;
  trucks, carts, boats, vending machines, caterers, schools and home
  kitchens left out): `https://internal-sandiegocounty.data.socrata.com/d/c5ez-ufrd`.
  Marked public domain. Owner names and phone numbers are not read.
- Santa Clara County Department of Environmental Health, food businesses
  (9,700, with positions): `https://data.sccgov.org/d/vuw7-jmjk`. No
  license stated; `none-stated`.
- New York State WIC vendors (2,800 groceries and pharmacies; farmers
  left out): `https://health.data.ny.gov/d/4az8-5hx6`. OPEN-NY terms.
  Read in their own boxes: 40 of 40 matches right in San Diego, San Jose
  and Buffalo. None of the three may add places: food permits were tried
  for that elsewhere and refused (SPEC section 9), and WIC stores are
  grocers the base already has.
- Looked at and not used: Delaware and Massachusetts child care tables
  (`data.delaware.gov/d/iuzd-3dbt`, `educationtocareer.data.mass.gov/d/dn4d-tjbb`),
  the same rosters `adapters/childcare_centers.py` already reads;
  Connecticut grocery and pharmacy tables, already inside the state
  license table; Cincinnati business licenses (`7dk3-gngs`), no business
  names; New York health club filings
  (`data.ny.gov/d/vgfa-ui3c`), see SPEC.md section 9; Orlando business
  tax receipts (`data.cityoforlando.net/d/7388-4re5`, addresses carry no
  ZIP); Marin and Everett business licenses (mostly people and
  contractors); Missouri tobacco licensees (mailing addresses only).

### Statewide food establishment lists found on agency sites (2026-10-07)
None states a license; rows are marked `none-stated`.
- Michigan MDARD food service licenses, with positions:
  `https://gisagomdard.state.mi.us/arcgis/rest/services/MDARD/RestaurantsCommissariesOpenData/FeatureServer/0`
- South Carolina food grades (inspections, with positions):
  `https://services5.arcgis.com/G4BLIH7rTQoIjCFv/arcgis/rest/services/Restaurants/FeatureServer` (layers 0 and 4)
- Minnesota Department of Agriculture retail food handlers (grocers and
  the like, not restaurants): the license lookup's text download at
  `https://www2.mda.state.mn.us/webapp/lis/LisResults.jsp`
- Not used: Vermont's food and lodging layer is a working map for
  inspectors, not a published dataset. Hawaii's and Rhode Island's files
  are years old. In most other states restaurants are licensed by counties
  and the state has a search form only.

### California Department of Consumer Affairs, licensee files
- License: none stated ("licensee data suitable for disclosure"); rows are
  marked `none-stated`.
- Fetched from: the shared folder linked from
  `https://www.dca.ca.gov/consumers/public_info/index.shtml`
  (`https://dca.box.com/s/oss6hf8jys2bmgxqd2gdz7w4oepm2il9`), folders for
  Barbering and Cosmetology, Automotive Repair and Pharmacy.
- Used for: establishment and barber shop licenses, automotive repair
  dealers, smog and safety inspection stations, retail pharmacies (open).
- Privacy: the files are mostly individual licensees, which are not read.
  Only rows marked as organizations are read, and nothing creates a place.
- Not used: licenses marked delinquent (12,600 salons, 8,200 repair
  dealers). An ended registration has not passed as a closure signal
  elsewhere (SPEC.md section 7), and this one has not been tested.

### Virginia DPOR, Texas and Ohio boards of pharmacy
None states a license; rows are marked `none-stated`.
- Virginia DPOR current license lists for shop occupations:
  `https://www.dpor.virginia.gov/RegulantLists`. The individual name and
  email columns are not read.
- Texas State Board of Pharmacy: `https://www.pharmacy.texas.gov/downloads/phydsk.csv`
- Ohio Board of Pharmacy: `https://www.pharmacy.ohio.gov/licensing/rosterrequests.aspx?listid=7`
- In both pharmacy files the pharmacist and responsible person columns
  are not read.

### HRSA health center sites
- License: US government work, public domain.
- Fetched from: `https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv`
- Used for: active permanent sites (open), with positions.

### State child care licensing layers
California's is CC BY (California Department of Social Services); the
others state no license and are marked `none-stated`. Only centers are
read, never family child care homes, and never the contact, owner,
director, phone or email columns.
- Arizona: `https://services1.arcgis.com/mpVYz37anSdrK4d8/arcgis/rest/services/AZLicensedFacilities/FeatureServer/17` (last run February 2025; rows carry that date)
- California: `https://services.arcgis.com/XLPEppdz2H9dOiqp/arcgis/rest/services/CDSS_CCL_Facilities/FeatureServer/0`
- Delaware: `https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Society/DE_ChildCareCenters/FeatureServer/0`
- Massachusetts: `https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Licensed_Child_Care_Programs/FeatureServer/0`
- Michigan: `https://utility.arcgis.com/usrsvcs/servers/a79c3b0caedf412599085941e2af91d4/rest/services/CSS/CSS_LARA/MapServer/5`
- Minnesota: `https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_mngeo/econ_child_care/FeatureServer/0`
- New Jersey: `https://mapsdep.nj.gov/arcgis/rest/services/Features/Structures/MapServer/4`
- Tennessee: `https://services1.arcgis.com/YuVBSS7Y1of2Qud1/arcgis/rest/services/Active_ChildCare_Locations/FeatureServer/0`
- Vermont: `https://services.arcgis.com/YKJ5JtnaPQ2jDbX8/arcgis/rest/services/Vermont%20Child%20Care%20Provider%20Data/FeatureServer/0`
- Wisconsin: `https://dhsgis.wi.gov/server/rest/services/DHS_DCF/Child_Care/MapServer/0`
- Not used: Maryland (a May 2024 snapshot), Kentucky (the layer stops at
  exactly 2,001 rows).
- Found and not built yet: CMS's list of clinical laboratories (300,000
  rows, no positions).

### City of San Diego, active business tax certificates
- License: ODC Public Domain Dedication and License, as stated on the
  dataset page.
- Fetched from: `https://seshat.datasd.org/business_tax_certificates/sd_businesses_active_datasd.csv`,
  linked on https://data.sandiego.gov/datasets/business-tax-certificates/
- Used for: businesses with an unexpired certificate (open). Positions
  come with the data.
- Privacy: the owner's name is not read, mailbox addresses are left out,
  and nothing creates a place from this source.

### Florida Lottery terminals, as published by the Division of Emergency Management
- License: none stated. Florida public record; `none-stated`.
- Fetched from: `https://services.arcgis.com/3wFbqsFPLeKqOlIK/arcgis/rest/services/Lottery_Terminals/FeatureServer/0`
- Used for: retailers with an active terminal (open), with the layer's
  positions. 13,200 retailers, refreshed daily. Phone numbers are not read.

### Allegheny County Health Department, food facility inspections
- License: Creative Commons Zero, as stated on the dataset.
- Fetched from: `https://data.wprdc.org/datastore/dump/1c9cf8d8-f3db-4364-b925-d7078c2fb02f`
  (Western Pennsylvania Regional Data Center)
- Used for: food facilities with an active permit (open, dated by the
  newest inspection in two years), with positions from the Census
  geocoder. This is the county the state's lookup leaves out.

### Maricopa County, Arizona, food establishment permits
- Terms: the layer's description says it is for county internal use and
  that outside use needs written authorization from the county GIS
  office. The owner decided on 2026-10-12 to use it without asking. Rows
  it touches are marked `Maricopa-County-terms`.
- Fetched from: `https://services.arcgis.com/ykpntM6e3tHvzKRJ/arcgis/rest/services/Restaurant_(External)/FeatureServer/0`
- Used for: establishments with an issued permit (open, dated by the
  layer's last edit), with the layer's own positions. 28,800 permits.

### City of Virginia Beach, business licenses
- Terms: public, and "applications using data supplied by this site must
  include" the city's disclaimer, which NOTICE carries. Rows it touches
  are marked `Virginia-Beach-terms`.
- Fetched from: `https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Business_Licenses_view/FeatureServer/0`
- Used for: licenses at a Virginia Beach address (open, dated the day the
  license began), with positions from the Census geocoder. Event,
  trustee, non-store, rental, construction and out-of-town classes are
  left out; the owner's name and phone are not read.

### City and county layers added 2026-10-12
Found by searching ArcGIS Hub; read by `adapters/city_layers.py`, which
now writes one file per source. None states a license; rows are marked
`none-stated`. Owner names, mailing addresses and phone numbers are not
read; home-based businesses and landlords' licenses are left out where the
layer marks them.
- Miami-Dade County local business tax (175,000 active receipts):
  `https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/Local_Business_Tax_Feature_Layer_View/FeatureServer/0`
- Broward County local business tax (100,000):
  `https://services.arcgis.com/JMAJrTsHNLrSsWf5/arcgis/rest/services/TaxDatabase2021/FeatureServer/0`
- Tucson business licenses:
  `https://services3.arcgis.com/9coHY2fvuFjG9HQX/arcgis/rest/services/BUSLIC/FeatureServer/9`
- Bellevue, Washington, business licenses:
  `https://services1.arcgis.com/EYzEZbDhXZjURPbP/arcgis/rest/services/Business_Licenses_(All)/FeatureServer/3`
- Sacramento County business licenses:
  `https://services1.arcgis.com/5NARefyPVtAeuJPU/arcgis/rest/services/Business_Licenses/FeatureServer/0`
- Long Beach business licenses:
  `https://services6.arcgis.com/yCArG7wGXGyWLqav/arcgis/rest/services/Business_Licenses_Public_View/FeatureServer/0`
- Chesapeake, Virginia, business licenses:
  `https://services1.arcgis.com/OAphVRUvJVpBRovs/arcgis/rest/services/Business_Licenses/FeatureServer/1`
- Detroit restaurant establishments (status Open):
  `https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/food_service_establishment_inspections/FeatureServer/0`
- Alameda County restaurant inspections (each place's newest in two years;
  the county's list leaves out Berkeley, which inspects its own):
  `https://services5.arcgis.com/ROBnTHSNjoZ2Wm1P/arcgis/rest/services/Restaurant_Inspections/FeatureServer/0`
- Riverside County retail food facilities (active permits):
  `https://services1.arcgis.com/pWmBUdSlVpXStHU6/arcgis/rest/services/Food/FeatureServer/0`
- California Department of Public Health, licensed and certified
  healthcare facilities (status open):
  `https://services5.arcgis.com/FlidZxdI0LGC9vAw/arcgis/rest/services/CDPH_LC_Facilities_Data/FeatureServer/0`
- Colorado licensed tobacco retailers, with positions (unexpired):
  `https://services3.arcgis.com/66aUo8zsujfVXRIT/arcgis/rest/services/PSD_TRAC_DOR_Licensed_Tobacco_Retailers/FeatureServer/0`
- Los Angeles County business licenses in unincorporated areas (apartment
  houses left out):
  `https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Business_License/FeatureServer/0`
- Anaheim active business licenses (located in Anaheim only):
  `https://services3.arcgis.com/hPs600I3X0RTaaaq/arcgis/rest/services/ActiveBusinessLicenses/FeatureServer/0`
- Glendale, Arizona, business licenses (status VALID, Arizona addresses;
  the layer has no points, so rows go to the Census geocoder):
  `https://services1.arcgis.com/9fVTQQSiODPjLUTa/arcgis/rest/services/Glendale_Business_Licenses/FeatureServer/0`
- Tucson liquor licenses (active), a Pima County layer:
  `https://services3.arcgis.com/9coHY2fvuFjG9HQX/arcgis/rest/services/Liquor_Licenses_Active_and_Pending_HFL/FeatureServer/16`
- Louisville Metro tobacco retail licenses (active retailers):
  `https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/tobacco_licenses/FeatureServer/0`
- Stores authorized for the WIC program, as three state health
  departments map them. Florida:
  `https://services1.arcgis.com/CY1LXxl9zlJeBuRZ/arcgis/rest/services/WIC_Vendors/FeatureServer/0`
  Arizona:
  `https://services1.arcgis.com/mpVYz37anSdrK4d8/arcgis/rest/services/WIC_Vendors/FeatureServer/1`
  Virginia:
  `https://services8.arcgis.com/0xEpEhgj2AqvWPLe/arcgis/rest/services/WICRetailers/FeatureServer/0`
  New Jersey:
  `https://services7.arcgis.com/Z0rixLlManVefxqY/arcgis/rest/services/wic_stores_6_24/FeatureServer/0`
- Newport News, Virginia, business licenses (active; retail, service,
  professional and wholesale classes, with contractors, peddlers, direct
  sellers and short-term rentals left out). The city account publishes the
  layer under the service name TEST. It also holds 7,060 closed licenses
  with the day each closed; those are not read, since end dates of this
  kind read about half right elsewhere (SPEC section 9):
  `https://services6.arcgis.com/SiUAoHzWN11AIADA/arcgis/rest/services/TEST/FeatureServer/0`
- City of Sacramento tobacco retail licenses (status Licensed):
  `https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/Tobacco_Retail_Points/FeatureServer/0`
- Retail food shops permitted by the Virginia Department of Agriculture
  and Consumer Services, as Fairfax County's health department maps them
  (the county's GIS disclaimer applies, no license):
  `https://services1.arcgis.com/ioennV6PpG5Xodq0/arcgis/rest/services/VDACS_Retail_Food_Establishments/FeatureServer/0`
  Read in their own boxes: 40 of 40 matches right in Newport News,
  Sacramento and Newark, 39 of 40 in Fairfax.
  Tucson, Glendale and Arizona's health department each attach an "as is"
  disclaimer and no license. None of these layers may add places (SPEC
  section 9).
- Seen and not read yet: Hayward, Reno,
  City of Miami and Charleston County business layers; Colorado retail
  alcohol outlet points (no dates). Not usable: Cape Coral (parcels, old
  rows), Gainesville (addresses only), St. Louis County food
  establishments (last edited 2019).

### City layers added 2026-10-07: Phoenix, Nashville, Milwaukee, Anchorage, Sioux Falls, Huntsville, Detroit
Milwaukee's data is CC BY (City of Milwaukee, per data.milwaukee.gov);
the others state no license and are marked `none-stated`. Agent, owner and
licensee columns are not read.
- Phoenix liquor licenses: `https://maps.phoenix.gov/pub/rest/services/Public/LIQUOR_RACMap/MapServer` (layers 0 to 13)
  Series 3, 6, 7, 9, 10, 11 and 12 (bars, stores, hotels, restaurants, microbreweries) are the source
  `phx_liquor`; the other series are `phx_liquor_trade`. Anchorage is split the same way by license type.
- Nashville beer permits: `https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Beer_Permit_Locations_Feature_Layer_view/FeatureServer/0`
- Milwaukee food and alcohol licenses: `https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/regulation/license/MapServer` (layers 9 and 0)
- Anchorage liquor licenses: `https://services2.arcgis.com/Ce3DhLRthdwbHlfF/arcgis/rest/services/LiquorLicenses_Hosted/FeatureServer/0`
- Sioux Falls restaurant sites: `https://gis.siouxfalls.gov/arcgis/rest/services/Data/Safety/MapServer/17`
- Huntsville alcohol licenses: `https://maps.huntsvilleal.gov/server/rest/services/Licenses/AlcoholBeverageLicenses/MapServer/0`
- Detroit business licenses and liquor licenses: `https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/` (`bseed_active_business_licenses`, `Liquor_Licenses`)
- Not used, and why:
  - Maricopa County food permits (105,000 rows): the county's terms forbid
    downloading for commercial use or resale, which the ODbL cannot honor.
  - Virginia Beach business licenses: no positions and terms not read in full.
  - Sioux Falls alcohol licenses: the layer carries no dates.
  - Albuquerque business registrations: the export stopped in August 2025.
  - Anchorage food inspections: stopped advancing in May 2026.
  - Atlanta, Charlotte, Indianapolis, Oklahoma City, Salt Lake City,
    Honolulu, Boise, Des Moines, Little Rock, Jackson, Wichita, Newark,
    Manchester, Portland (Maine and Oregon), Burlington, Billings, Fargo,
    Cheyenne, Charleston WV: nothing usable found.

### City layers: Las Vegas, Omaha, Minneapolis, Baltimore, Columbus
None states a license; rows are marked `none-stated`.
- Las Vegas active business licenses:
  `https://services1.arcgis.com/F1v0ufATbBQScMtY/arcgis/rest/services/Business_Licenses_OpenData/FeatureServer/0`.
  Owner and phone columns are not read; home, mobile and office-only
  trades are left out. Its "Closed" licenses carry no date and are not used.
- Douglas County, Nebraska restaurant inspections:
  `https://services.arcgis.com/pDAi2YK0L0QxVJHj/arcgis/rest/services/Restaurant_Inspections/FeatureServer/14`
- Minneapolis food inspections and on-sale and off-sale liquor licenses:
  `https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/` (`Food_Inspections`, `On_Sale_Liquor`, `Off_Sale_Liquor`)
- Baltimore liquor licenses:
  `https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/LIquor_Licenses/FeatureServer/0`.
  The licensee's name is not read.
- Columbus inspected restaurants and markets:
  `https://maps2.columbus.gov/arcgis/rest/services/Schemas/Health/MapServer/3`
- Not used: Southern Nevada Health District restaurant inspections on the
  Las Vegas portal. The rows have no names or addresses.

### Pennsylvania Department of Revenue, sales tax licenses
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.pa.gov/resource/ugeq-ckxd.json`
- Used for: current retail sales licenses (open), with positions.
- Privacy: the legal name is not read, and nothing creates a place from
  this source; it holds home sellers as well as shops.

### Delaware Division of Revenue, business licenses
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.delaware.gov/resource/5zy2-grhr.json`
- Used for: current licenses in storefront trades (open), with positions
  from the Census geocoder.
- Privacy: many licensees are one person working from home. Nothing creates
  a place from this source.

### Texas Department of Licensing and Regulation, all licenses
- License: none stated. Texas public record. Rows it touches are marked
  `none-stated`.
- Fetched from: `https://data.texas.gov/resource/7358-krk7.json`
- Used for: unexpired salon and barber establishment licenses (open), with
  positions from the Census geocoder.
- Privacy: the dataset is mostly licenses held by people. Only
  establishment licenses are read.

### Texas Comptroller, permitted sales tax locations
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.texas.gov/resource/3kx8-uryv.json`
- Used for: storefront locations with a live permit (open), with positions
  from the Census geocoder. Out-of-business dates are not used; see SPEC.md
  section 9.
- Privacy: non-store retailers are skipped, the taxpayer's own name and
  address are not read, and nothing creates a place from it.

### Texas Alcoholic Beverage Commission, license information
- License: none stated by the dataset or by data.texas.gov. Texas public
  record. Rows it touches are marked `none-stated`.
- Fetched from: `https://data.texas.gov/resource/7hf9-qc9f.json`
- Used for: active retail licenses (open). Ended licenses are not used; see
  SPEC.md section 9.

### US Census Bureau geocoder
- License: US federal government work, public domain.
- Fetched from: `https://geocoding.geo.census.gov/geocoder/locations/addressbatch`
- Used for: positions for register rows that have only an address
  (California and Texas licenses).

### New York State Liquor Authority, active licenses
- License: OPEN-NY Terms of Use (2013). Free reuse for any lawful purpose,
  no attribution or share-alike required. The license is revocable by the
  State and comes with an indemnity clause; it is not a standard open
  license.
- Fetched from: `https://data.ny.gov/resource/9s3h-dpkz.json`
- Used for: active licenses with a premises (open), with positions. Also
  mints missing places and drives the missing-license flag in New York.

### New York Department of State, salon and barber shop licenses
- License: OPEN-NY Terms of Use, as above.
- Fetched from: `https://data.ny.gov/resource/y3u4-jbgh.json`
- Used for: unexpired appearance enhancement business and barber shop
  licenses (open), with positions. The license holder's name is not read.

### New York Agriculture and Markets, food safety inspections
- License: OPEN-NY Terms of Use, as above.
- Fetched from: `https://data.ny.gov/resource/d6dy-3h7r.json`
- Used for: retail food stores by newest inspection (open), with positions.
  Also mints missing places.

### New York City DCWP, issued licenses
- License: none named on the dataset. NYC Open Data; rows it touches are
  marked `NYC-Open-Data-terms`.
- Fetched from: `https://data.cityofnewyork.us/resource/w7w3-xahh.json`
- Used for: active premises licenses (open), with positions.

### Delaware Division of Public Health, food establishment inspections
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.delaware.gov/resource/384s-wygj.json`
- Used for: food establishments by newest inspection (open), with
  positions. Also mints missing places.

### Montgomery County, Maryland, food inspections
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.montgomerycountymd.gov/resource/dkrp-gr48.json`
- Used for: food businesses by newest inspection (open), with positions
  from the Census geocoder.

### New York DMV, licensed facilities
- License: OPEN-NY Terms of Use, as above.
- Fetched from: `https://data.ny.gov/resource/nhjr-rpi2.json`
- Used for: unexpired repair shop, inspection station and dealer
  registrations (open), with positions. The owner's name is not read.

### City of Sacramento, Business Operation Tax accounts
- License: none stated on the layer. City public record; rows it touches
  are marked `none-stated`.
- Fetched from: `https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/account_data_with_header_NEW/FeatureServer/0`
- Used for: active accounts (open), with positions from the Census
  geocoder. Close dates are not used; see SPEC.md section 9.
- Privacy: owner and mailing fields are not read, and nothing creates a
  place from this source.

### Sacramento County, food facility inspections
- License: none stated on the layer. County public record; rows it touches
  are marked `none-stated`.
- Fetched from: `https://services1.arcgis.com/5NARefyPVtAeuJPU/arcgis/rest/services/Food_Inspections/FeatureServer/0`
- Used for: food facilities by most recent inspection (open), with
  positions. Also mints missing places.

### Louisville Metro, Kentucky, restaurant inspections and ABC licenses
- License: none stated on the layers. Louisville Metro Open Data; rows
  they touch are marked `none-stated`.
- Fetched from: `https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/FoodServiceData/FeatureServer/0`
  and `.../ABC_State_ActiveLicenses/FeatureServer/0`
- Used for: food establishments by newest inspection (open, geocoded), and
  active state alcohol licenses in Jefferson County (open, with positions,
  also mints missing places).

### District of Columbia, Basic Business Licenses
- License: CC-BY-4.0, as stated on opendata.dc.gov. Attribution is in NOTICE.
- Fetched from: `https://maps2.dcgis.dc.gov/dcgis/rest/services/FEEDS/DCRA/FeatureServer/0`
- Used for: active licenses that carry a trade name and are not housing
  rentals (open), with positions from the Census geocoder.
- Privacy: most rows are rentals or people trading under their own names.
  Owner, agent and billing fields are never read, and nothing creates a
  place from this source.

### District of Columbia ABCA liquor licenses
- License: CC-BY-4.0, as stated on opendata.dc.gov. Attribution is in NOTICE.
  Open question: whether CC-BY-4.0 data may sit inside an ODbL database
  without a waiver. OpenStreetMap asks for one. Only the status and its date
  are taken from this source, not the listing itself.
- Fetched from: layers 5 (locations) and 42 (cancellations) of
  `https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer`
- Used for: active licenses (open) and cancellations (closed, for
  restaurants, taverns, nightclubs and clubs).

### France: SIRENE (INSEE)
- License: Licence Ouverte 2.0 (Etalab). Attribution: "INSEE, base Sirene",
  with the date of the file. Generally treated as compatible with the ODbL;
  not checked with a lawyer.
- Fetched from: the monthly parquet files listed at
  https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret
  read in place over HTTP.
- Used for: active establishments (open, dated by the last change to the
  entry). Closed establishments are not used; see SPEC.md section 9.
- Privacy: only rows marked freely diffusible are read, and a sole trader's
  row only when it carries a shop sign. Nothing creates a place from it.

### US Census cartographic boundary file, states
- License: US federal government work, public domain.
- Fetched from: `https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip`
- Used for: clipping state builds to the state outline. Not evidence.

## Not used yet

Survey of what comes next, in order. None of these has been fetched or
checked by this project.

- More state alcohol license lists. Found, not yet built: Washington
  (data.wa.gov, 9dee-kzm5).
  Missouri's "out of business" list (nytw-fmz3) and its new license list
  (dymb-xy5c) are found but not used yet.
- Florida also publishes new food licenses and changes of owner by fiscal
  year, and lodging inspections.
- Health inspections and city business licenses: many city portals state no
  license. Each one gets an entry here saying what it states before it is used.
