#!/usr/bin/env python3
"""Southern Nevada Health District: food establishment permits (Clark County, Las Vegas).

snhd_nv_food  a food establishment whose permit is active in the district's
              nightly file, open as of the day the file was read.

A casino holds one permit per kitchen, bar and outlet, each under its own
name ("McDonald's #3549 D HOTEL"), so rows are read per permit and a name
that repeats at an address is read once. Caterers, food trucks, portable
bars and units and farmers' market stands have no fixed door and are left
out. The file's latitude and longitude columns are swapped. Inactive
permits carry no end date and are not read.

Southern Nevada Health District, restaurant inspection data for developers.
https://www.southernnevadahealthdistrict.org/permits-and-regulations/restaurant-inspections/developers/
"""
import csv
import datetime
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://www.southernnevadahealthdistrict.org/restaurants/download/restaurants.zip"
ACTIVE = ("01", "04")  # active, billable or exempt from billing
# caterer, farmer's market, food truck, portable bar, portable unit, self-service food truck
NO_DOOR = {"9", "14", "22", "24", "25", "28"}


def table(z, name):
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"), delimiter=";")


def main():
    today = datetime.date.today().isoformat()
    z = zipfile.ZipFile(io.BytesIO(get(URL)))
    kind = {r["PE"]: r["category_id"] for r in table(z, "restaurant_pe_category_xref.csv")}
    out = Writer("snhd_nv_food")
    seen = set()
    for r in table(z, "restaurant_establishments.csv"):
        if r.get("record_status") not in ACTIVE:
            continue
        if kind.get(r.get("PE")) in NO_DOOR:
            out.drop("no fixed door")
            continue
        name, street = (r.get("restaurant_name") or "").strip(), (r.get("address") or "").strip()
        if (name.upper(), street.upper()) in seen:
            continue
        seen.add((name.upper(), street.upper()))
        out.row("snhd_nv_food", r.get("permit_number"), name,
                address(street, r.get("city_name"), "NV %s" % (r.get("zip_code") or "")[:5]),
                r.get("longitude"), r.get("latitude"), "open", today)
    out.close()


if __name__ == "__main__":
    main()
