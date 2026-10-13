#!/usr/bin/env python3
"""Allegheny County, Pennsylvania (Pittsburgh): food facility inspections.

achd_pa_food  a restaurant, bar, store or other food facility with an
              active permit, open as of the day of its newest inspection
              in the last two years.

The state's food safety lookup leaves Allegheny County out, because the
county health department inspects its own. Mobile units and temporary
stands are left out. No positions; addresses go to the Census geocoder.

Creative Commons Zero, as stated on the dataset (Western Pennsylvania
Regional Data Center).
https://data.wprdc.org/dataset/allegheny-county-restaurant-food-facility-inspection-violations
"""
import datetime
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from ckan import rows
from evidence import Writer, address

HOST, RESOURCE = "data.wprdc.org", "1c9cf8d8-f3db-4364-b925-d7078c2fb02f"
CLOSED = "112a3821-334d-4f3f-ab40-4de1220b1a0a"
CLOSED_SINCE = "2021-01-01"
SKIP = ("mobile", "temporary", "vending", "push cart", "seasonal")


def main():
    since = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()
    newest = {}
    for r in rows(HOST, RESOURCE):
        when = (r.get("inspect_dt") or "")[:10]
        kind = (r.get("category") or "").lower()
        if when < since or (r.get("permit_status") or "") != "Active" or any(k in kind for k in SKIP):
            continue
        street = ("%s %s" % (r.get("num") or "", r.get("street") or "")).strip()
        key = hashlib.sha1(("%s|%s|%s" % (r.get("facility_name"), street, r.get("zip_code"))).upper().encode()).hexdigest()[:16]
        if key not in newest or when > newest[key][0]:
            newest[key] = (when, r.get("facility_name"), address(street, r.get("city"), "PA %s" % (r.get("zip_code") or "")[:5]))
    out = Writer("achd_pa_food")
    for key, (when, name, addr) in newest.items():
        out.row("achd_pa_food", key, name, addr, None, None, "open", when)
    out.close(geocode=True)

    # Facilities the county gives a closing date for (a second table, with positions). Held, not
    # used: where another source could check them, it called 48 closed and 49 open afterwards.
    closed = Writer("achd_pa_closed", held=True)
    for r in rows(HOST, CLOSED):
        when = (r.get("bus_cl_date") or "")[:10]
        if when < CLOSED_SINCE or any(k in (r.get("description") or "").lower() for k in SKIP):
            continue
        street = ("%s %s" % (r.get("num") or "", r.get("street") or "")).strip()
        closed.row("achd_pa_closed", r.get("id"), r.get("facility_name"),
                   address(street, r.get("city"), "PA %s" % (r.get("zip") or "")[:5]),
                   r.get("y"), r.get("x"), "closed", when)
    closed.close()


if __name__ == "__main__":
    main()
