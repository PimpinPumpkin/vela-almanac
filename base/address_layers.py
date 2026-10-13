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

# name: layer, filter, the field holding "1876 GREENLEAF ST", the ZIP field
LAYERS = {
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
                for a, (lat, lng) in features(layer, where, "%s,%s" % (full, zip_field)):
                    m = re.match(r"\s*(\d+)[A-Za-z]?(?:\s+1/2)?\s+(\S.*)$", str(a.get(full) or ""))
                    zip5 = re.match(r"\d{5}", str(a.get(zip_field) or ""))
                    if not m or not zip5 or lat is None:
                        continue
                    out.writerow((m.group(1), " ".join(m.group(2).split()), zip5.group(0), "%.6f" % lat, "%.6f" % lng))
                    n += 1
            if n == 0:
                raise RuntimeError("no rows")
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
