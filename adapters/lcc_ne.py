#!/usr/bin/env python3
"""Nebraska Liquor Control Commission: active license roster.

lcc_ne  an active retail license, open as of the day the roster was read.

Shippers and the other non-retail groups are left out. The manager and
licensee columns are not read. No positions; addresses go to the Census
geocoder.

Nebraska public record. No license stated.
https://lcc.nebraska.gov/licensing-sdl/active-license-roster
"""
import urllib.parse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

from xlsx import rows

PREMISES = {"A", "B", "C", "D", "I", "J", "L", "G", "AB", "IB", "CS", "E", "Y", "Y1", "Z", "M"}
PAGE = "https://lcc.nebraska.gov/licensing-sdl/active-license-roster"
LINK = re.compile(r'href="([^"]*Active[^"]*License[^"]*Roster[^"]*\.xlsx)"', re.I)
PLACE = re.compile(r"^(.*?)\s*(?:_x000D_)?\s*\n\s*(.*?),\s*NE\s+(\d{5})", re.S)


def main():
    today = datetime.date.today().isoformat()
    links = LINK.findall(get(PAGE).decode("utf-8", "replace"))
    if not links:
        raise SystemExit("lcc_ne: no roster linked from the roster page")
    table = rows(get(urllib.parse.urljoin(PAGE, links[0].replace(" ", "%20"))))
    head = next(table)
    col = {name: head.index(name) for name in ("License Type Group", "Class", "License Number", "License State", "Trade Name", "Address")}
    out = Writer("lcc_ne")
    for r in table:
        r = r + [""] * (len(head) - len(r))
        if r[col["License Type Group"]] != "Retail" or r[col["License State"]] != "Active":
            continue
        m = PLACE.match(r[col["Address"]])
        if not m:
            out.drop("no usable address")
            continue
        # Premises classes (bars, restaurants, stores, breweries) keep the source name. Nonprofit and
        # special designated licenses, caterers' second licenses and wholesalers get their own, so
        # they can confirm a place and never add one.
        source = "lcc_ne" if r[col["Class"]] in PREMISES else "lcc_ne_other"
        out.row(source, r[col["License Number"]], r[col["Trade Name"]],
                address(m.group(1), m.group(2), "NE %s" % m.group(3)), None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
