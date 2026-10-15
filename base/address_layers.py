#!/usr/bin/env python3
"""Address points from county and state layers, for places Overture's address theme leaves bare.

Writes data/cache/addresses/<name>.csv (number, street, postcode, lat, lng), which build.sh
reads beside the Overture address points. Only a position is ever taken from these: a
register row that has an address and no point is put on its building (SPEC.md section 6).
No address is published from here.

  base/address_layers.py            every layer
  base/address_layers.py ok_ng911   the named ones

Layer addresses and terms are in SOURCES.md.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import json
import time
import urllib.parse

from arcgis import info
from evidence import CACHE, get

# name: layer, filter, the field holding "1876 GREENLEAF ST" (or the fields that make it,
# in order), the ZIP field
LAYERS = {
    # Philadelphia's address index: points on the parcel, not those placed along a street range
    "philadelphia_pa": ("https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/AIS_Address_Points/FeatureServer/0",
                        "geocode_type IN ('pwd_parcel', 'dor_parcel', 'ng911')", "street_address", "zip_code"),
    # no ZIP field: the ZIP is the Census ZIP code area the point falls in
    "new_orleans_la": ("https://gis.nola.gov/arcgis/rest/services/Address/SiteAddressPoint/MapServer/0",
                       "1=1", ("ADDRNUM", "FULLNAME"), None),
    "wi_ng911": ("https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_Site_Structure_Address_Points_2/FeatureServer/0",
                 "1=1", ("Add_Number", "St_Name"), None),
    "milwaukee_wi": ("https://services2.arcgis.com/s1wgJQKbKJihhhaT/arcgis/rest/services/Milwaukee_County_Address_Points/FeatureServer/56",
                     "Addr_Status = 'Active'", ("HouseNo", "Dir", "Street", "StType"), "Zip_Code"),
    "allegheny_pa": ("https://gisdata.alleghenycounty.us/arcgis/rest/services/Addressing/Addressing_AddressPoints/MapServer/0",
                     "STATUS = 'ACTIVE'", "FULL_ADDRESS", "ZIP_CODE"),
    "charleston_sc": ("https://services.arcgis.com/jR9eNCjAkxwH2nLe/arcgis/rest/services/Charleston_County_Addresses/FeatureServer/0",
                      "1=1", "WHOLE_ADDRESS", "POSTAL_CODE"),
    "charleston_city_sc": ("https://services2.arcgis.com/tQaXW7Zb1Vphzvgd/arcgis/rest/services/City_Addresses/FeatureServer/0",
                           "1=1", "ADDRLABEL", "ZIPCODE"),
    "alameda_ca": ("https://services5.arcgis.com/ROBnTHSNjoZ2Wm1P/arcgis/rest/services/Address_Points/FeatureServer/0",
                   "1=1", "ADDRESS", "ZIPCODE"),
    "ok_ng911": ("https://services.arcgis.com/3xOwF6p0r7IHIjfn/arcgis/rest/services/NG911_Address_Points/FeatureServer/0",
                 "1=1", "label", "zipcode"),
}


def features(layer, where, fields):
    """Every feature as (attributes, (lat, lng)), walked by object id: a layer of millions
    of points fails now and then at a deep offset, and an id range can be asked for again."""
    meta = info(layer)
    oid = meta.get("objectIdField") or next(f["name"] for f in meta["fields"] if f["type"] == "esriFieldTypeOID")
    size, last = meta.get("maxRecordCount") or 1000, -1
    step = size
    while True:
        q = {"where": "(%s) AND %s > %d" % (where, oid, last), "outFields": "%s,%s" % (oid, fields), "outSR": 4326,
             "f": "json", "orderByFields": oid, "resultRecordCount": step}
        body = json.loads(get(layer + "/query?" + urllib.parse.urlencode(q)))
        if "error" in body:
            # one bad record can sink a page: ask for less, and at one row step over it
            if step == 1:
                last += 1
            step = max(1, step // 10)
            time.sleep(2)
            continue
        feats = body.get("features", [])
        for f in feats:
            g = f.get("geometry") or {}
            yield f["attributes"], (g.get("y"), g.get("x"))
        if not feats:
            return
        last = feats[-1]["attributes"][oid]
        step = min(size, step * 10)


def zip_from_areas(path):
    """Fill the ZIP of every point from the Census ZIP code area (ZCTA) it falls in."""
    import subprocess
    areas = os.path.join(CACHE, "census", "zcta.parquet")
    if not os.path.exists(areas):
        raise RuntimeError("no %s: see SOURCES.md" % areas)
    sql = """load spatial;
copy (select a.number, a.street, z.zip as postcode, a.lat, a.lng
      from read_csv('{p}', header = true, all_varchar = true) a
      join '{z}' z on st_contains(z.geom, st_point(a.lng::double, a.lat::double)))
to '{p}.zip' (header, delimiter ',');""".format(p=path, z=areas)
    subprocess.run(["duckdb", "-c", sql], check=True)
    os.replace(path + ".zip", path)


def main():
    folder = os.path.join(CACHE, "addresses")
    os.makedirs(folder, exist_ok=True)
    failed = []
    for name in sys.argv[1:] or sorted(LAYERS):
        layer, where, full, zip_field = LAYERS[name]
        path = os.path.join(folder, name + ".csv")
        n = 0
        try:
            with open(path + ".part", "w", newline="") as f:
                out = csv.writer(f)
                out.writerow(("number", "street", "postcode", "lat", "lng"))
                parts = full if isinstance(full, tuple) else (full,)
                for a, (lat, lng) in features(layer, where, ",".join(parts + ((zip_field,) if zip_field else ()))):
                    line = " ".join(str(a.get(f) or "").strip() for f in parts if a.get(f) not in (None, ""))
                    m = re.match(r"\s*(\d+)[A-Za-z]?(?:\s+1/2)?\s+(\S.*)$", line)
                    zip5 = re.match(r"\d{5}", str(a.get(zip_field) or "")) if zip_field else None
                    if not m or (zip_field and not zip5) or lat is None:
                        continue
                    out.writerow((m.group(1), " ".join(m.group(2).split()), zip5.group(0) if zip5 else "",
                                  "%.6f" % lat, "%.6f" % lng))
                    n += 1
            if n == 0:
                raise RuntimeError("no rows")
            if not zip_field:
                zip_from_areas(path + ".part")
            os.replace(path + ".part", path)
            print("%s: %d address points" % (name, n))
        except (Exception, SystemExit) as e:  # keep last run's file
            if os.path.exists(path + ".part"):
                os.remove(path + ".part")
            failed.append("%s (%s)" % (name, str(e)[:100]))
    if failed:
        print("address_layers: " + "; ".join(failed), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
