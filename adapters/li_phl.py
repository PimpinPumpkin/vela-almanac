#!/usr/bin/env python3
"""Philadelphia Licenses and Inspections: business licenses.

li_phl  an active license held by a company for a food business, a motor
        vehicle repair or fuel business, a child care facility, a tire or
        precious metal dealer, open as of the day the file was read.
        Positions come with the data.

Most of this dataset is rental licenses, which are not places in this
project's sense, and licenses held by individuals; both are left out, along
with vendors, dumpsters, tow trucks and event permits.

OpenDataPhilly. City of Philadelphia public record.
https://opendataphilly.org/datasets/licenses-and-inspections-business-licenses/
"""
import datetime
import json
import re
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

API = "https://phl.carto.com/api/v2/sql"
KINDS = ("Food Preparing and Serving", "Food Preparing and Serving (30+ SEATS)",
         "Food Establishment, Retail Permanent Location", "Food Establishment, Retail Perm Location (Large)",
         "Motor Vehicle Repair / Fuel Dispensing", "Child Care Facility", "Tire Dealer", "Precious Metal Dealer")
PAGE = 20000


def main():
    today = datetime.date.today().isoformat()
    kinds = ", ".join("'%s'" % k for k in KINDS)
    out = Writer("li_phl")
    seen, offset = set(), 0
    while True:
        sql = ("select licensenum, business_name, address, zip, ST_Y(the_geom) as lat, ST_X(the_geom) as lng "
               "from business_licenses where licensestatus = 'Active' and legalentitytype = 'Company' "
               "and licensetype in (%s) order by licensenum limit %d offset %d" % (kinds, PAGE, offset))
        rows = json.loads(get(API + "?" + urllib.parse.urlencode({"q": sql})))["rows"]
        for r in rows:
            # one business holds several licenses at an address
            k = ((r.get("business_name") or "").upper(), r.get("address"))
            if k in seen:
                continue
            seen.add(k)
            # "Carrols Corporation (BURGER KING)": the sign on the door is in the brackets
            # (the brackets of a chain's license hold a mailing line instead: "(ATTN: ...)")
            name = r.get("business_name") or ""
            m = re.match(r"(.+?)\s*\((?:T/A\s+)?([^()]{2,})\)\s*$", name)
            if m and not re.match(r"(attn|c/o)\b", m.group(2), re.I):
                name = "%s dba %s" % (m.group(1), m.group(2))
            elif m:
                name = m.group(1)
            out.row("li_phl", r["licensenum"], name,
                    address(r.get("address"), "PHILADELPHIA", "PA %s" % (r.get("zip") or "")[:5]),
                    r.get("lat"), r.get("lng"), "open", today)
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close()


if __name__ == "__main__":
    main()
