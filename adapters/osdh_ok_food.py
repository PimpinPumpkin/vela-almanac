#!/usr/bin/env python3
"""Oklahoma food service establishments (all counties).

osdh_ok_food  a restaurant, school kitchen, store deli or other food
              service establishment on the State Department of Health's
              inspection lookup, open as of the day the list was read.

The lookup lists establishments county by county, fifteen to a page, with
no file: about 1,700 requests, two seconds apart. The list carries no
dates (an establishment's inspections are a request each), so a row is
dated the day it was read, as a license list is. Of 40 establishments
drawn at random, 38 had been inspected within two years (SPEC.md). No positions; addresses go to the Census geocoder.

Set OK_COUNTIES to a space separated list of county numbers to read only
those (55 is Oklahoma County, used for the Oklahoma City test box).

Oklahoma public record. No license stated. The site has no robots.txt.
https://www.phin.state.ok.us/inspections/
"""
import datetime
import hashlib
import html
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address

PAGE = "/inspections/"
HIDDEN = re.compile(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"')
ROW = re.compile(r'<tr class="dgText"[^>]*>\s*<td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>', re.S)
PAGER = re.compile(r'<tr class="dgPager".*?</tr>', re.S)
LINK = re.compile(r"__doPostBack\(&#39;([^&]+)&#39;,&#39;&#39;\)\">([^<]+)</a>")


def text(cell):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", cell)).split())


def county_pages(site, county):
    """Every result page of one county, in order."""
    form = {k: html.unescape(v) for k, v in HIDDEN.findall(site.fetch(PAGE).decode("utf-8", "replace"))}
    form.update({"cmbCounties": str(county), "txtSearch": "", "cmdSearch": "Find"})
    page, number = site.fetch(PAGE, form=form).decode("utf-8", "replace"), 1
    while True:
        yield page
        pager = PAGER.search(page)
        links = LINK.findall(pager.group(0)) if pager else []
        # the next page by its number, or the "..." that follows the last number shown
        target = next((t for t, label in links if label.strip() == str(number + 1)), None)
        if target is None and links and links[-1][1].strip() == "...":
            shown = [int(label) for _, label in links if label.strip().isdigit()]
            if not shown or max(shown) <= number:
                target = links[-1][0]
        if target is None:
            return
        form = {k: html.unescape(v) for k, v in HIDDEN.findall(page)}
        form.update({"cmbCounties": str(county), "txtSearch": "", "__EVENTTARGET": target, "__EVENTARGUMENT": ""})
        page, number = site.fetch(PAGE, form=form).decode("utf-8", "replace"), number + 1


def main():
    site = Site("https://www.phin.state.ok.us")
    asked = os.environ.get("OK_COUNTIES")
    counties = [int(c) for c in asked.split()] if asked else range(1, 78)
    today = datetime.date.today().isoformat()
    rows, empty = {}, []
    for county in counties:
        found = 0
        for page in county_pages(site, county):
            for name, street, town, zip5, _ in ROW.findall(page):
                name, street, town, zip5 = text(name), text(street), text(town), text(zip5)
                if not name or not street:
                    continue
                key = hashlib.sha1(("%s|%s|%s" % (name, street, zip5)).upper().encode()).hexdigest()[:16]
                rows[key] = (name, address(street, town, "OK %s" % zip5[:5]))
                found += 1
        if not found:
            empty.append(county)
    if not asked and (len(empty) > 3 or len(rows) < 8000):
        # a county left out would look like a county that closed: keep last run's file instead
        raise SystemExit("osdh_ok_food: %d rows, %d counties empty" % (len(rows), len(empty)))
    out = Writer("osdh_ok_food")
    for key, (name, addr) in rows.items():
        out.row("osdh_ok_food", key, name, addr, None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
