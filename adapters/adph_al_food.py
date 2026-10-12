#!/usr/bin/env python3
"""Alabama food establishment scores (all counties).

adph_al_food  a restaurant, food store, school lunchroom or other food
              establishment, open as of the day of its newest inspection
              in the last two years.

County health departments inspect; the Department of Public Health shows
each establishment's latest score through a search page, with no file.
The page is asked county by county and kind by kind, one page of
results each: about 600 requests, two seconds apart. Mobile units, camps,
caterers and seasonal stands are not asked for. Scores are not read. No
positions; addresses go to the Census geocoder.

Set AL_COUNTIES to a space separated list of county names to read only
those (MADISON is used for the Huntsville test box).

Alabama public record. No license stated. The site has no robots.txt.
https://foodscores.state.al.us/
"""
import datetime
import hashlib
import html
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import UA, Writer, address

P = "ctl00$ContentPlaceHolder1$"
KINDS = ["Daycare Food Service", "Food Service Establishment", "Insitutional Food Service", "Limited Food",
         "Limited Retail", "Nursing Home Food Service", "Retail Food Store", "School Lunchroom - Private",
         "School Lunchroom - Public"]
HIDDEN = re.compile(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"')
RECORD = re.compile(r'DtList_ctl(\d+)_LblEst">(.*?)</span>.*?_LnkAdd"[^>]*>(.*?)</a>.*?_Label1">(.*?)</span>'
                    r'.*?_Label2">(.*?)</span>.*?_LblInDt">(.*?)</span>', re.S)


def text(cell):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", cell)).split())


def main():
    site = Site("https://foodscores.state.al.us")
    # the site keeps its session in the address: /(S(...))/default.aspx
    with site.opener.open(urllib.request.Request(site.base + "/", headers={"User-Agent": UA}), timeout=120) as r:
        path, first = urllib.parse.urlparse(r.geturl()).path, r.read().decode("utf-8", "replace")
    time.sleep(site.pause)
    select = re.search(r'<select name="ctl00\$ContentPlaceHolder1\$DrpCnty".*?</select>', first, re.S).group(0)
    counties = {name.strip(): value for value, name in re.findall(r'<option[^>]*value="(\d+)">([^<]+)', select)}
    asked = os.environ.get("AL_COUNTIES")
    wanted = asked.split() if asked else sorted(counties)
    since = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()
    rows, page, dead = {}, first, []
    for county in wanted:
        answered = 0
        for kind in KINDS:
            form = {k: html.unescape(v) for k, v in HIDDEN.findall(page)}
            form.update({P + "TxtEstdNm": "", P + "DrpEstdType": kind, P + "txtCity": "",
                         P + "DrpCnty": counties[county], P + "BtnSearch.x": "20", P + "BtnSearch.y": "10"})
            try:
                # every result comes on one page
                got = site.fetch(path, form=form, tries=2, timeout=600).decode("utf-8", "replace")
            except Exception:
                # the site answers a search that finds nothing with a server error
                continue
            page, answered = got, answered + 1
            for _, name, street, town, zip5, date in RECORD.findall(page):
                name, street, town, zip5 = text(name), text(street), text(town), text(zip5)
                m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", text(date))
                if not m or not name or not street:
                    continue
                when = "%s-%02d-%02d" % (m.group(3), int(m.group(1)), int(m.group(2)))
                key = hashlib.sha1(("%s|%s|%s" % (name, street, zip5[:5])).upper().encode()).hexdigest()[:16]
                if when >= since and (key not in rows or when > rows[key][0]):
                    rows[key] = (when, name, address(street, town, "AL %s" % zip5[:5]))
        if not answered:
            dead.append(county)
    if len(dead) > (0 if asked else 3):
        # a county left out would look like a county that closed: keep last run's file instead
        raise SystemExit("adph_al_food: no answer for %s" % ", ".join(dead[:8]))
    if not asked and len(rows) < 8000:
        raise SystemExit("adph_al_food: only %d rows" % len(rows))
    out = Writer("adph_al_food")
    for key, (when, name, addr) in rows.items():
        out.row("adph_al_food", key, name, addr, None, None, "open", when)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
