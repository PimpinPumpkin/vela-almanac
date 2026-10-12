#!/usr/bin/env python3
"""Georgia environmental health inspections (all counties).

dph_ga_inspections  a restaurant, other food service or hotel, open as of
                    the day of its newest inspection in the last two years.

County health departments inspect; the state's portal lists every permit,
newest inspection first, five to a request and nothing larger. The list
is read to its end, about six thousand requests, so this reader runs on
the slow schedule (.github/workflows/crawl.yml), not in the monthly
build. Swimming pools are left out, and so is a permit never inspected.
Phone numbers are not read. No positions; addresses go to the Census
geocoder.

Set GA_CITY to read one city only (used for the Atlanta test box).

Georgia public record. No license stated. The site has no robots.txt.
https://ga.healthinspections.us/stateofgeorgia/
"""
import base64
import datetime
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address

API = "/stateofgeorgia/API/index.cfm/"
KEEP = {"Food Service", "Tourist Accommodation"}


def main():
    site = Site("https://ga.healthinspections.us", pause=1.0)
    city = os.environ.get("GA_CITY")
    if city:
        query = json.dumps({"city": base64.b64encode(city.encode()).decode(), "keyword": ""}, separators=(",", ":"))
        route = API + "search/" + urllib.parse.quote(query) + "/"
    else:
        route = API + "facilities/"
    since = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()
    seen, rows, page, failed, empty = set(), [], 0, 0, 0
    while True:
        try:
            batch = json.loads(site.fetch(route + str(page)))
        except Exception as e:
            # one page that will not load is five permits; many is the site being down
            failed += 1
            if failed > 20:
                raise SystemExit("dph_ga_inspections: gave up at page %d (%s)" % (page, e))
            page += 1
            continue
        if not batch:
            # the feed sometimes answers with nothing in the middle of the list: ask again,
            # and call it the end only when three pages in a row stay empty
            time.sleep(20)
            try:
                batch = json.loads(site.fetch(route + str(page)))
            except Exception:
                batch = []
        if not batch:
            empty += 1
            if empty >= 3:
                break
            page += 1
            continue
        empty = 0
        page += 1
        for f in batch:
            if f.get("id") in seen:
                continue
            seen.add(f.get("id"))
            cols = {}
            for v in (f.get("columns") or {}).values():
                if ": " in v:
                    k, _, val = v.partition(": ")
                    cols[k] = val.strip()
            if cols.get("Permit Type") not in KEEP:
                continue
            m = re.match(r"(\d\d)-(\d\d)-(\d{4})$", cols.get("Last Inspection Date", ""))
            if not m:
                continue
            when = "%s-%s-%s" % (m.group(3), m.group(1), m.group(2))
            if when < since:
                continue
            lines = [x.strip() for x in (f.get("mapAddress") or "").split("\n") if x.strip()]
            if len(lines) < 2:
                continue
            town = re.match(r"(.*), GA\s+(\d{5})?", lines[-1])
            if not town:
                continue
            rows.append((base64.b64decode(f["id"]).decode(), f.get("name"),
                         address(" ".join(lines[:-1]), town.group(1), "GA %s" % (town.group(2) or "")), when))
    if not city and len(rows) < 10000:
        # the list ended early: keep last run's file rather than drop most of the state
        raise SystemExit("dph_ga_inspections: only %d rows from %d pages" % (len(rows), page))
    out = Writer("dph_ga_inspections")
    for key, name, addr, when in rows:
        out.row("dph_ga_inspections", key, name, addr, None, None, "open", when)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
