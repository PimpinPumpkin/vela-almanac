#!/usr/bin/env python3
"""Los Angeles County Department of Public Health: restaurant and market inventory.

lac_food  a restaurant or food market the county's Environmental Health
          division holds a permit for, open as of the day the inventory
          was published.

The county publishes the inventory every quarter as a new layer with the
date in its name, so the newest one is found by search. Pasadena, Long
Beach and Vernon run their own health departments and are not in it. A
facility with several permits (a market and its deli) is read once, under
the facility's name. Owner names and addresses are not read.

County of Los Angeles Public Health. https://data.lacounty.gov
"""
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, features
from evidence import Writer, address, get

SEARCH = "https://www.arcgis.com/sharing/rest/search?"
QUERY = 'title:"Environmental Health Restaurant and Market Inventory" orgid:RmCCgQtiZLDCtblq type:"Feature Service"'


def newest():
    """(layer address, ISO date published) of the latest inventory."""
    found = json.loads(get(SEARCH + urllib.parse.urlencode(
        {"q": QUERY, "f": "json", "num": 10, "sortField": "modified", "sortOrder": "desc"})))["results"]
    if not found:
        raise SystemExit("lac_food: no inventory layer found")
    return found[0]["url"].rstrip("/") + "/0", day(found[0]["modified"])


def main():
    layer, as_of = newest()
    out = Writer("lac_food")
    seen = set()
    for a, (lat, lng) in features(layer, fields="FACILITY_ID,FACILITY_NAME,FACILITY_ADDRESS,FACILITY_CITY,FACILITY_ZIP"):
        if a.get("FACILITY_ID") in seen:
            continue
        seen.add(a.get("FACILITY_ID"))
        # a facility the county could not place sits at 0, 0
        if not lat or not lng or abs(lat) < 1:
            lat = lng = None
        out.row("lac_food", a.get("FACILITY_ID"), a.get("FACILITY_NAME"),
                address(a.get("FACILITY_ADDRESS"), a.get("FACILITY_CITY"), "CA %s" % str(a.get("FACILITY_ZIP") or "")[:5]),
                lat, lng, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
