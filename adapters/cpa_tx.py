#!/usr/bin/env python3
"""Texas Comptroller: storefront locations permitted to collect sales tax.

cpa_tx  a location with a live permit (no out-of-business date), open as of
        the day the dataset was last updated.

The Comptroller also gives an out-of-business date for 450,000 locations,
but it is not emitted. Tested in a Houston box on places with no brand and
no live permit under the same name: other evidence said still open 87 times
and closed 85. The date marks one taxpayer leaving; the shop often carries
on under the next one.

Only storefront trades are read (retail, food and lodging, repair and
personal services, recreation), and not the non-store retailers, who are
mostly people selling from home. The taxpayer's own name and address are
not read; only the outlet's. Rows are evidence for places that are already
listed; nothing here creates a place. No positions; addresses go to the
Census geocoder.

Set CPA_TX_CITY to read one city only (for testing).

Public domain, as stated on the dataset.
https://data.texas.gov/d/3kx8-uryv
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.texas.gov/api/views/3kx8-uryv.json"
ROWS = "https://data.texas.gov/resource/3kx8-uryv.json"
PAGE = 50000
# NAICS sectors: 44-45 retail, 71 recreation, 72 food and lodging, 81 repair and personal services
STOREFRONT = ("44", "45", "71", "72", "81")
NON_STORE_RETAIL = "454"
FIELDS = "tp_number,loc_number,loc_name,address_number,address_text,loc_city,loc_zip,first_sale_date"


def main():
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    where = "loc_state = 'TX' AND out_of_business_date IS NULL AND (%s) AND NOT starts_with(naics, '%s')" % (
        " OR ".join("starts_with(naics, '%s')" % p for p in STOREFRONT), NON_STORE_RETAIL)
    if os.environ.get("CPA_TX_CITY"):
        where += " AND loc_city = '%s'" % os.environ["CPA_TX_CITY"].upper().replace("'", "''")
    out = Writer("cpa_tx")
    offset = 0
    while True:
        q = {"$select": FIELDS, "$where": where, "$limit": PAGE, "$offset": offset, "$order": "tp_number,loc_number"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            street = ("%s %s" % (r.get("address_number") or "", r.get("address_text") or "")).strip()
            out.row("cpa_tx", "%s-%s" % (r.get("tp_number"), r.get("loc_number")), r.get("loc_name"),
                    address(street, r.get("loc_city"), "TX %s" % (r.get("loc_zip") or "")[:5]),
                    None, None, "open", updated, since=r.get("first_sale_date"))
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
