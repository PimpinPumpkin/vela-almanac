#!/usr/bin/env python3
"""Mississippi food facility inspections (statewide).

msdh_ms_food  a restaurant, bar, bakery, school or hospital kitchen, food
              store deli or food plant, open as of the day of its newest
              inspection in the last two years.

The State Department of Health's lookup has an export that returns every
inspection between two dates as one table, so two years are read in a
dozen requests, two months each. Mobile units, temporary events, summer
feeding sites, vending companies, milk trucks, farmers markets and family
day care homes are left out. The grade is not read. No positions;
addresses go to the Census geocoder.

Mississippi public record. No license stated. The site has no robots.txt.
https://apps.msdh.ms.gov/food/
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

EXPORT = ("/food/FacilityListingDatesExport.aspx?s_District=&Start_Date=%s&End_Date=%s&s_Result="
          "&s_FacilityTypesID=&s_CountyID=&s_ShowToPublic=&FacListingDir=Asc&FacListingPageSize=10000")
ROW = re.compile(r"<tr>\s*" + r'<td class="KnockoutDataTD">(.*?)</td>\s*' * 9, re.S)
SKIP = re.compile(r"mobile|special event|temporary|summer feeding|vending|milk (hauler|tanker)|farmers market|family day care", re.I)


def text(cell):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", cell)).replace("\xa0", " ").split())


def main():
    site = Site("https://apps.msdh.ms.gov")
    today = datetime.date.today()
    newest, start = {}, today - datetime.timedelta(days=730)
    while start <= today:
        end = min(start + datetime.timedelta(days=60), today)
        page = site.fetch(EXPORT % (start.strftime("%m%%2f%d%%2f%Y"), end.strftime("%m%%2f%d%%2f%Y")),
                          timeout=600).decode("utf-8", "replace")
        found = ROW.findall(page)
        if len(found) >= 10000:
            raise SystemExit("msdh_ms_food: a two month window filled the export's 10,000 rows")
        for _, name, street, town, _, zip5, date, _, kind in found:
            name, street, town, zip5, kind = text(name), text(street), text(town), text(zip5), text(kind)
            m = re.match(r"(\d\d)/(\d\d)/(\d{4})", text(date))
            if not m or not name or not street or SKIP.search(kind):
                continue
            when = "%s-%s-%s" % (m.group(3), m.group(1), m.group(2))
            key = hashlib.sha1(("%s|%s|%s" % (name, street, zip5[:5])).upper().encode()).hexdigest()[:16]
            if key not in newest or when > newest[key][0]:
                newest[key] = (when, name.rstrip(" -"), address(street, town, "MS %s" % zip5[:5]))
        start = end + datetime.timedelta(days=1)
    out = Writer("msdh_ms_food")
    for key, (when, name, addr) in newest.items():
        out.row("msdh_ms_food", key, name, addr, None, None, "open", when)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
