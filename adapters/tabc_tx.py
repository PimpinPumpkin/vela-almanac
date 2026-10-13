#!/usr/bin/env python3
"""Texas Alcoholic Beverage Commission: active retail alcohol licenses.

tabc_tx  an active retail license, open as of the day the dataset was last
         updated. The trade name is used when there is one.

Surrendered, cancelled and expired licenses carry a date, but are not
emitted. Tested in a Houston box for bars, on-premise beer and wine and
private clubs, skipping any whose name still held an active license at the
address: 1,212 places matched, and other evidence said still open 79 times
and closed 89. Temporary event permits and the manufacturing and
distribution tiers are left out too.

The file has no positions; addresses go to the Census geocoder.

Neither the dataset nor data.texas.gov states a license. Texas public record.
https://data.texas.gov/d/7hf9-qc9f
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.texas.gov/api/views/7hf9-qc9f.json"
ROWS = "https://data.texas.gov/resource/7hf9-qc9f.json"
PAGE = 50000
TEMPORARY = {"NT", "TR", "NE", "NB"}
FIELDS = "license_id,license_type,trade_name,owner,address,city,zip,original_issue_date"


def main():
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    out = Writer("tabc_tx")
    offset = 0
    while True:
        q = {"$select": FIELDS, "$where": "tier='Retail' AND state='TX' AND primary_status='Active'",
             "$limit": PAGE, "$offset": offset, "$order": "license_id"}
        page = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in page:
            if r.get("license_type") in TEMPORARY:
                out.drop("temporary permit")
                continue
            out.row("tabc_tx", (r.get("license_id") or "").split(".")[0], r.get("trade_name") or r.get("owner"),
                    address(r.get("address"), (r.get("city") or "").upper(), "TX %s" % (r.get("zip") or "")[:5]),
                    None, None, "open", updated, since=r.get("original_issue_date"))
        offset += len(page)
        if len(page) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
