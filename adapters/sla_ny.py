#!/usr/bin/env python3
"""New York State Liquor Authority: premises with an active alcohol license.

sla_ny  every active retail or producer license with a premises of its own,
        open as of the day the dataset was last updated. The trade name
        (DBA) is used when there is one. Positions come with the data.

Left out: additional bars inside a licensed premises, temporary permits,
caterers, direct shippers, wholesalers, importers, and licenses for
vessels, aircraft and rail cars. The list holds active licenses only, so
there is no closed evidence here.

OPEN-NY Terms of Use: free reuse for any lawful purpose, no attribution or
share-alike required, license revocable by the State.
https://data.ny.gov/d/9s3h-dpkz
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.ny.gov/api/views/9s3h-dpkz.json"
ROWS = "https://data.ny.gov/resource/9s3h-dpkz.json"
PAGE = 50000
NO_PREMISES = ("additional bar", "temporary", "direct shipper", "cater", "wholesale", "importer",
               "vessel", "aircraft", "railroad")


def main():
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    out = Writer("sla_ny")
    offset = 0
    while True:
        q = {"$limit": PAGE, "$offset": offset, "$order": "licensepermitid"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            kind = (r.get("description") or "").lower()
            if any(word in kind for word in NO_PREMISES):
                out.drop("no premises of its own")
                continue
            lng, lat = (r.get("georeference") or {}).get("coordinates") or (None, None)
            out.row("sla_ny", r["licensepermitid"], r.get("dba") or r.get("legalname"),
                    address(r.get("actualaddressofpremises"), r.get("city"), "NY %s" % (r.get("zipcode") or "")[:5]),
                    lat, lng, "open", updated, since=r.get("originalissuedate"))
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close()


if __name__ == "__main__":
    main()
