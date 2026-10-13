#!/usr/bin/env python3
"""Colorado Liquor Enforcement Division: liquor licenses.

led_co        an active license for a premises (restaurant, tavern, store,
              brewery, club and the like), open as of the day the dataset
              was last updated.
The companion list of recently expired and surrendered licenses is not
used: it is a few hundred rows statewide, "expired" often means a renewal
that is late, and the 14 that matched in a Denver box were too few to test.
Each run adds it to data/cache/held/led_co_ended.csv so the records add up;
the build does not read that file.

Permits that ride on another license (takeout, delivery, sidewalk, storage),
shippers, importers, wholesalers and festival permits are left out. Rows
without a position go to the Census geocoder.

Public domain, as stated on the datasets.
https://data.colorado.gov/d/ier5-5ms2
"""
import csv
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import features
from evidence import EVIDENCE, Writer, address, get

HOST = "https://data.colorado.gov"
ACTIVE, ENDED = "ier5-5ms2", "pwjb-9dd5"
OUTLETS = "https://www.cohealthmaps.dphe.state.co.us/arcgis/rest/services/PSD/CDPHE_Alcohol_Outlet_Density/MapServer/0"
PAGE = 50000
NOT_A_PREMISES = ("permit", "shipper", "importer", "wholesale", "master file", "sidewalk", "nonresident",
                  "alternating", "optional premises", "related facility", "festival", "special event")


def rows(dataset):
    offset = 0
    while True:
        q = {"$limit": PAGE, "$offset": offset, "$order": ":id"}
        page = json.loads(get("%s/resource/%s.json?%s" % (HOST, dataset, urllib.parse.urlencode(q))))
        yield from page
        offset += len(page)
        if len(page) < PAGE:
            return


def pick(r, *names):
    return next((r[n] for n in names if r.get(n)), "")


def emit(out, source, dataset, state, date_of):
    seen = set()
    for r in rows(dataset):
        kind = pick(r, "license_type", "licensetype").lower()
        if any(word in kind for word in NOT_A_PREMISES):
            out.drop("not a premises license")
            continue
        number = pick(r, "license_number", "licensenumber")
        if number in seen:
            continue
        seen.add(number)
        lng, lat = (r.get("geo") or {}).get("coordinates") or (None, None)
        zip5 = pick(r, "zip").split(".")[0][:5]
        out.row(source, number, pick(r, "doing_business_as", "doingbusinessas", "licensee_name", "companyname"),
                address(pick(r, "street_address", "streetaddress"), pick(r, "city").upper(), "CO %s" % zip5),
                lat, lng, state, date_of(r))


def pins():
    """Positions for licenses, by license number, from the state health department's alcohol outlet
    points. The Census geocoder's guess is enough to match a place; a license may only add a place
    from one of these points, and only from those the layer marks as placed on the address."""
    folder = os.path.join(EVIDENCE, "pins")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "led_co.csv")
    try:
        found = [(a.get("license_no"), lat, lng) for a, (lat, lng) in
                 features(OUTLETS, where="accuracy = 'Point Accuracy'", fields="license_no")
                 if a.get("license_no") and lat is not None]
    except (Exception, SystemExit) as e:
        print("led_co pins not refreshed: %s" % str(e)[:120], file=sys.stderr)
        return
    with open(path + ".part", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "source_id", "lat", "lng"])
        w.writerows(("led_co", number, "%.6f" % lat, "%.6f" % lng) for number, lat, lng in found)
    os.replace(path + ".part", path)
    print("led_co pins: %d" % len(found))


def main():
    updated = datetime.datetime.fromtimestamp(
        json.loads(get("%s/api/views/%s.json" % (HOST, ACTIVE)))["rowsUpdatedAt"],
        datetime.timezone.utc).date().isoformat()
    out = Writer("led_co")
    emit(out, "led_co", ACTIVE, "open", lambda r: updated)
    out.close(geocode=True)

    pins()

    held = Writer("led_co_ended", held=True)
    emit(held, "led_co_ended", ENDED, "closed", lambda r: pick(r, "expirationdate", "expiration")[:10])
    held.close(geocode=True)


if __name__ == "__main__":
    main()
