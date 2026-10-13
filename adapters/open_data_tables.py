#!/usr/bin/env python3
"""City, county and state tables on open data portals (Socrata).

One source per table, each written to its own file so one portal being
down does not lose the others. Set TABLES to a few names to read only those.

austin_food       Austin, Texas: a food establishment, open as of its
                  newest inspection in the last two years. Public domain.
cincinnati_food   Cincinnati, Ohio: a licensed food business, open as of
                  its newest inspection in the last two years. Public domain.
boulder_food      Boulder County, Colorado: a restaurant, open as of its
                  newest inspection (the table starts in 2025). Public domain.
marin_food        Marin County, California: a food facility, open as of
                  its newest inspection in the last two years. ODbL.
cambridge_food    Cambridge, Massachusetts: a food establishment permit
                  issued in the last two years. PDDL.
brla_biz          East Baton Rouge Parish, Louisiana: a business with an
                  open occupational account. Public domain.
norfolk_biz       Norfolk, Virginia: a business license. No license stated.
berkeley_biz      Berkeley, California: a business license at an address
                  in the city. No license stated.
moco_md_alcohol   Montgomery County, Maryland: an alcohol licensee.
                  Public domain.
childcare_ny      New York State: a licensed or registered day care
                  center or school-age program. No license stated.
childcare_nyc     New York City: an active group child care program.
                  Public domain.
childcare_pa      Pennsylvania: a certified child care center. US
                  government works, as the table states.
childcare_tx      Texas: a licensed child care center. CC0.
nj_inspection     New Jersey: a private vehicle inspection facility (a
                  repair shop licensed to inspect). No license stated.
lottery_ny        New York State: a lottery retailer. OPEN-NY terms.
lottery_tx        Texas: a lottery retailer, open as of its last month with
                  sales. The table's terms are the Texas Lottery's own
                  (texaslottery.com copyright page); the owner decided on
                  2026-10-12 to use it.
wm_nyc            New York City: a shop whose scales, pumps or dryers the
                  city tested, open as of its newest test in the last two
                  years. NYC Open Data terms.
la_biz            Los Angeles: an active business tax account. CC0.
sf_biz            San Francisco: a registered business location with no
                  end date. PDDL. Locations with an end date are held,
                  not used.

Tables without inspection or issue dates are dated the day the table was
last updated. Owner, contact person, inspector, phone and email columns
are not read, home day cares are left out, and nothing here creates a
place. Tables with no positions go to the Census geocoder.
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, street_city
from socrata import point, rows, updated

SINCE = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()


def day(value):
    return (value or "")[:10]


def austin_food(out):
    host, table = "datahub.austintexas.gov", "ecmv-9xxi"
    for r in rows(host, table, select="facility_id,restaurant_name,address,max(inspection_date) as seen",
                  where="inspection_date >= '%s'" % SINCE, group="facility_id,restaurant_name,address",
                  order="facility_id"):
        # "9516 N Lamar Blvd Austin, TX 78753-4108", sometimes with the point on two more lines
        parts = street_city((r.get("address") or "").split("\n")[0])
        if not parts:
            out.drop("address not understood")
            continue
        out.row("austin_food", r.get("facility_id"), r.get("restaurant_name"),
                address(parts[0], parts[1], "TX %s" % parts[3][:5]), None, None, "open", day(r.get("seen")))


def cincinnati_food(out):
    host, table = "data.cincinnati-oh.gov", "rg6p-b3h3"
    for r in rows(host, table,
                  select="license_no,business_name,address,city,postal_code,latitude,longitude,max(action_date) as seen",
                  where="action_date >= '%s' and license_status = 'Issued'" % SINCE,
                  group="license_no,business_name,address,city,postal_code,latitude,longitude", order="license_no"):
        out.row("cincinnati_food", r.get("license_no"), r.get("business_name"),
                address(r.get("address"), r.get("city"), "OH %s" % (r.get("postal_code") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "open", day(r.get("seen")))


def boulder_food(out):
    host, table = "data.colorado.gov", "6ytb-f2cq"
    newest = {}
    for r in rows(host, table, select="business_id,name,address,b1_situs_city,b1_situs_zip,rec_date,rec_date_1,location"):
        seen = max(day(r.get("rec_date")), day(r.get("rec_date_1")))
        if seen and (r.get("business_id") not in newest or seen > newest[r["business_id"]][0]):
            newest[r.get("business_id")] = (seen, r)
    for key, (seen, r) in newest.items():
        lat, lng = point(r.get("location"))
        out.row("boulder_food", key, r.get("name"),
                address(r.get("address"), r.get("b1_situs_city"), "CO %s" % (r.get("b1_situs_zip") or "")[:5]),
                lat, lng, "open", seen)


def marin_food(out):
    host, table = "data.marincounty.gov", "73zb-z5me"
    newest = {}
    for r in rows(host, table, select="business_id,business_name,formatted_address,inspection_date,businessaddress",
                  where="inspection_date >= '%s'" % SINCE):
        seen = day(r.get("inspection_date"))
        if r.get("business_id") not in newest or seen > newest[r["business_id"]][0]:
            newest[r.get("business_id")] = (seen, r)
    for key, (seen, r) in newest.items():
        lat, lng = point(r.get("businessaddress"))
        out.row("marin_food", key, (r.get("business_name") or "").strip('"'),
                (r.get("formatted_address") or "").strip('"'), lat, lng, "open", seen)


def cambridge_food(out):
    host, table = "data.cambridgema.gov", "iect-ma2e"
    newest = {}
    for r in rows(host, table, select="id,full_address,latitude,longitude,issue_date,business_name,dba,permit_type",
                  where="issue_date >= '%s' and status = 'Complete'" % SINCE):
        key = ((r.get("dba") or r.get("business_name") or "").upper(), r.get("full_address"))
        if key not in newest or day(r.get("issue_date")) > day(newest[key].get("issue_date")):
            newest[key] = r
    for r in newest.values():
        out.row("cambridge_food", r.get("id"), r.get("dba") or r.get("business_name"), r.get("full_address"),
                r.get("latitude"), r.get("longitude"), "open", day(r.get("issue_date")))


def brla_biz(out):
    host, table = "data.brla.gov", "xw6s-bcqm"
    as_of = updated(host, table)
    seen = set()
    for r in rows(host, table, where="tstatus = 'O' and tphysicalstate = 'LA'",
                  select="taccount,tacctlocation,tname,naicname,tphysicaladdress1,tphysicalcity,tphysicalzipcode5"):
        key = ((r.get("tname") or "").upper(), r.get("tphysicaladdress1"))
        if key in seen:
            continue
        seen.add(key)
        out.row("brla_biz", "%s-%s" % (r.get("taccount"), r.get("tacctlocation")), r.get("tname"),
                address(r.get("tphysicaladdress1"), r.get("tphysicalcity"), "LA %s" % (r.get("tphysicalzipcode5") or "")),
                None, None, "open", as_of)


def norfolk_biz(out):
    host, table = "data.norfolk.gov", "dpi6-sct5"
    as_of = updated(host, table)
    n = 0
    for r in rows(host, table, select="trading_as_name,location_address,latitude,longitude"):
        m = re.match(r"(.*?)\s+(\d{5})$", r.get("location_address") or "")
        if not m:
            out.drop("address not understood")
            continue
        n += 1
        out.row("norfolk_biz", "%s|%s" % ((r.get("trading_as_name") or "").upper(), m.group(1)), r.get("trading_as_name"),
                address(m.group(1), "Norfolk", "VA %s" % m.group(2)), r.get("latitude"), r.get("longitude"), "open", as_of)


def berkeley_biz(out):
    host, table = "data.cityofberkeley.info", "rwnf-bu3w"
    as_of = updated(host, table)
    for r in rows(host, table, where="b1_situs_city = 'BERKELEY'",
                  select="recordid,dba,b1_business_name,b1_address1,b1_full_address,b1_situs_zip,busdesc"):
        if "rental" in (r.get("busdesc") or "").lower():
            out.drop("a landlord's license")
            continue
        out.row("berkeley_biz", r.get("recordid"), r.get("dba") or r.get("b1_business_name"),
                address(r.get("b1_address1") or r.get("b1_full_address"), "Berkeley", "CA %s" % (r.get("b1_situs_zip") or "")[:5]),
                None, None, "open", as_of)


def moco_md_alcohol(out):
    host, table = "data.montgomerycountymd.gov", "c6rw-fazn"
    as_of = updated(host, table)
    for r in rows(host, table, select="licensee_number,licensee_name,street,city,zip,location"):
        lat, lng = point(r.get("location"))
        out.row("moco_md_alcohol", r.get("licensee_number"), r.get("licensee_name"),
                address(r.get("street"), r.get("city"), "MD %s" % (r.get("zip") or "")[:5]), lat, lng, "open", as_of)


def childcare_ny(out):
    host, table = "data.ny.gov", "cb42-qumz"
    as_of = updated(host, table)
    for r in rows(host, table, where="program_type in ('DCC', 'SACC', 'SDCC') and facility_status in ('License', 'Registration')",
                  select="facility_id,facility_name,street_number,street_name,city,zip_code,latitude,longitude"):
        out.row("childcare_ny", r.get("facility_id"), r.get("facility_name"),
                address("%s %s" % (r.get("street_number") or "", r.get("street_name") or ""), r.get("city"),
                        "NY %s" % (r.get("zip_code") or "")[:5]), r.get("latitude"), r.get("longitude"), "open", as_of)


def childcare_nyc(out):
    host, table = "data.cityofnewyork.us", "gy3q-4tzp"
    as_of = updated(host, table)
    for r in rows(host, table, select="dcid,program_name,address,borough,zipcode,latitude,longitude"):
        out.row("childcare_nyc", r.get("dcid"), r.get("program_name"),
                address(r.get("address"), r.get("borough"), "NY %s" % (r.get("zipcode") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "open", as_of)


def childcare_pa(out):
    host, table = "data.pa.gov", "ajn5-kaxt"
    as_of = updated(host, table)
    for r in rows(host, table, where="provider_type = 'Child Care Center'",
                  select="mpi_id,mpi_location_id,facility_name,facility_address,facility_city,facility_zip_code"):
        out.row("childcare_pa", "%s-%s" % (r.get("mpi_id"), r.get("mpi_location_id")), r.get("facility_name"),
                address(r.get("facility_address"), r.get("facility_city"), "PA %s" % (r.get("facility_zip_code") or "")[:5]),
                None, None, "open", as_of)


def childcare_tx(out):
    host, table = "data.texas.gov", "bc5r-88dy"
    as_of = updated(host, table)
    for r in rows(host, table, where="operation_type = 'Licensed Center' and temporarily_closed = 'NO'",
                  select="operation_id,operation_name,location_address"):
        # "10935 CAYMAN MIST DR  HOUSTON TX- 77075 5065"
        m = re.match(r"(.*?)\s{2,}(.*?)\s+TX-\s*(\d{5})", r.get("location_address") or "")
        if not m:
            out.drop("address not understood")
            continue
        out.row("childcare_tx", r.get("operation_id"), r.get("operation_name"),
                address(m.group(1), m.group(2), "TX %s" % m.group(3)), None, None, "open", as_of)


def nj_inspection(out):
    host, table = "data.nj.gov", "t6tk-mr48"
    as_of = updated(host, table)
    for r in rows(host, table, where="type = 'Private Inspection Facility'",
                  select="lic_id,st_nm,adr_street,adr_city,zip,geocoded_column"):
        lat, lng = point(r.get("geocoded_column"))
        out.row("nj_inspection", r.get("lic_id"), r.get("st_nm"),
                address(r.get("adr_street"), r.get("adr_city"), "NJ %s" % (r.get("zip") or "")[:5]), lat, lng, "open", as_of)


def lottery_ny(out):
    host, table = "data.ny.gov", "2vvn-pdyi"
    as_of = updated(host, table)
    for r in rows(host, table, where="state = 'NY'", select="retailer,name,street,city,zip,latitude,longitude"):
        out.row("lottery_ny", r.get("retailer"), r.get("name"),
                address(r.get("street"), r.get("city"), "NY %s" % (r.get("zip") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "open", as_of)


def wm_nyc(out):
    host, table = "data.cityofnewyork.us", "8fei-z6rz"
    newest = {}
    for r in rows(host, table, where="date_of_occurance >= '%s' and address_type = 'Complete Address'" % SINCE,
                  select="business_unique_id,business_name,business_category,date_of_occurance,building_no,street_1,"
                         "city,zip_code,latitude,longitude"):
        kind = (r.get("business_category") or "").lower()
        if any(k in kind for k in ("pedicab", "mobile food", "truck", "fuel oil", "airline", "vendor")):
            out.drop("not a shop")
            continue
        key = (r.get("business_unique_id"), r.get("building_no"), r.get("street_1"))
        if key not in newest or day(r.get("date_of_occurance")) > day(newest[key].get("date_of_occurance")):
            newest[key] = r
    for (ident, number, street), r in newest.items():
        out.row("wm_nyc", "%s|%s %s" % (ident, number, street), r.get("business_name"),
                address("%s %s" % (number or "", street or ""), r.get("city"), "NY %s" % (r.get("zip_code") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "open", day(r.get("date_of_occurance")))


def la_biz(out):
    host, table = "data.lacity.org", "6rrh-rzua"
    as_of = updated(host, table)
    for r in rows(host, table, select="location_account,business_name,dba_name,street_address,city,zip_code,location_1,location_start_date"):
        lat, lng = point(r.get("location_1"))
        if lat is None:
            # no point means an address outside the city, often outside California
            out.drop("not located in the city")
            continue
        out.row("la_biz", r.get("location_account"), r.get("dba_name") or r.get("business_name"),
                address(r.get("street_address"), r.get("city"), "CA %s" % (r.get("zip_code") or "")[:5]), lat, lng, "open", as_of,
                since=r.get("location_start_date"))


def lottery_tx(out):
    host, table = "data.texas.gov", "beka-uwfq"
    # one row per retailer, game and month: ask the portal for each retailer's last month with sales
    recent = (datetime.date.today() - datetime.timedelta(days=400)).isoformat()
    for r in rows(host, table, where="month_end_date >= '%s' and net_sales_amount > 0 and location_state = 'TX'" % recent,
                  select="retailer_number,location_name,location_address,location_city,location_zip,max(month_end_date) as seen",
                  group="retailer_number,location_name,location_address,location_city,location_zip", order="retailer_number"):
        out.row("lottery_tx", r.get("retailer_number"), r.get("location_name"),
                address(r.get("location_address"), r.get("location_city"), "TX %s" % (r.get("location_zip") or "")[:5]),
                None, None, "open", day(r.get("seen")))


def sf_biz(out):
    host, table = "data.sf.gov", "g8m3-pdis"
    as_of = updated(host, table)
    seen = set()
    for r in rows(host, table, where="city = 'San Francisco' and location_end_date is null and dba_end_date is null",
                  select="uniqueid,dba_name,full_business_address,business_zip,location,location_start_date"):
        key = ((r.get("dba_name") or "").upper(), r.get("full_business_address"))
        if key in seen:
            continue
        seen.add(key)
        lat, lng = point(r.get("location"))
        out.row("sf_biz", r.get("uniqueid"), r.get("dba_name"),
                address(r.get("full_business_address"), "San Francisco", "CA %s" % (r.get("business_zip") or "")[:5]),
                lat, lng, "open", as_of, since=r.get("location_start_date"))
    # Locations the city has an end date for are kept aside, not used: where another source
    # could check them, it called 102 closed and 72 still open (SPEC.md section 9).
    held = Writer("sf_biz_ended", held=True)
    for r in rows(host, table, where="city = 'San Francisco' and location_end_date >= '%s'" % SINCE,
                  select="uniqueid,dba_name,full_business_address,business_zip,location,location_end_date"):
        lat, lng = point(r.get("location"))
        held.row("sf_biz_ended", r.get("uniqueid"), r.get("dba_name"),
                 address(r.get("full_business_address"), "San Francisco", "CA %s" % (r.get("business_zip") or "")[:5]),
                 lat, lng, "closed", day(r.get("location_end_date")))
    held.close()


def tceq_tx_cleaners(out):
    """Dry cleaners and their drop stations registered with the Texas environmental agency."""
    host, table = "data.texas.gov", "qfph-9bnd"
    as_of = updated(host, table)
    for r in rows(host, table, where="location_state = 'TX'",
                  select="registration_id,regulated_entity_name,location_address,location_city,location_zip_code"):
        out.row("tceq_tx_cleaners", r.get("registration_id"), r.get("regulated_entity_name"),
                address(r.get("location_address"), r.get("location_city"), "TX %s" % (r.get("location_zip_code") or "")[:5]),
                None, None, "open", as_of)


def sd_county_food(out):
    """San Diego County food facility permits. Trucks, carts, boats, vending machines, caterers
    and home kitchens have no shop to find."""
    host, table = "internal-sandiegocounty.data.socrata.com", "c5ez-ufrd"
    as_of = updated(host, table)
    for r in rows(host, table, where="active_permit = 'A' and permit_status in ('Permit Renewed', 'Issued') and state = 'CA' "
                  "and business_type in ('Restaurant Food Facility', 'Pre-Packaged Retail Market', 'Retail Market with Deli', "
                  "'Low Risk Food Facility', 'Miscellaneous Food Facility', 'Retail Food Processing', 'Single Operating Site')",
                  select="record_id,record_name,address,city,zip"):
        out.row("sd_county_food", r.get("record_id"), r.get("record_name"),
                address(r.get("address"), r.get("city"), "CA %s" % (r.get("zip") or "")[:5]), None, None, "open", as_of)


def scc_food(out):
    host, table = "data.sccgov.org", "vuw7-jmjk"
    as_of = updated(host, table)
    for r in rows(host, table, select="business_id,name,address,city,postal_code,latitude,longitude"):
        out.row("scc_food", r.get("business_id"), r.get("name"),
                address(r.get("address"), r.get("city"), "CA %s" % (r.get("postal_code") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "open", as_of)


def wic_ny(out):
    host, table = "health.data.ny.gov", "4az8-5hx6"
    as_of = updated(host, table)
    for r in rows(host, table, where="type <> 'Farmer'", select="facility_name,street_address,city,zip"):
        out.row("wic_ny", "%s-%s-%s" % (r.get("facility_name"), r.get("street_address"), r.get("zip")), r.get("facility_name"),
                address(r.get("street_address"), r.get("city"), "NY %s" % (r.get("zip") or "")[:5]), None, None, "open", as_of)


TABLES = [sf_biz, lottery_tx, lottery_ny, wm_nyc, cambridge_food, moco_md_alcohol, childcare_ny, childcare_nyc, childcare_pa,
          childcare_tx, nj_inspection, la_biz, austin_food, cincinnati_food, boulder_food, marin_food, brla_biz,
          norfolk_biz, berkeley_biz, tceq_tx_cleaners, sd_county_food, scc_food, wic_ny]
NO_POSITIONS = {tceq_tx_cleaners, sd_county_food, wic_ny, lottery_tx, austin_food, brla_biz, berkeley_biz, childcare_pa, childcare_tx}


def main():
    only = os.environ.get("TABLES", "").split()
    failed = []
    for table in TABLES:
        if only and table.__name__ not in only:
            continue
        out = Writer(table.__name__)
        try:
            table(out)
            out.close(geocode=table in NO_POSITIONS)
        except Exception as e:
            # leave last run's file where it is
            out.f.close()
            os.remove(out.path + ".part")
            failed.append("%s (%s)" % (table.__name__, str(e)[:120]))
    if failed:
        print("open_data_tables: " + "; ".join(failed), file=sys.stderr)
        # prepare.sh reads the names from this file, so the watch report flags the one source,
        # not every source this reader writes
        note = os.environ.get("ALMANAC_FAILED")
        if not note:
            raise SystemExit(1)
        with open(note, "a") as f:
            f.writelines(x.split(":")[0].split(" (")[0] + "\n" for x in failed)


if __name__ == "__main__":
    main()
