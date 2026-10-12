#!/usr/bin/env python3
"""California ABC daily license export: premises licensed to sell alcohol.

abc_ca  issued, active retail licenses (bars, restaurants, stores, breweries,
        tasting rooms), open as of the "Updated" date in the file's first
        line. The trade name (DBA) is used when there is one.

Surrendered, suspended and revoked licenses are in the file with no date of
the change, so they are not emitted. Applications, caterer and event
permits, wholesalers and importers are left out: none is a premises a
person can walk into. The file has no positions; addresses are sent to the
Census geocoder, and the ones it cannot place are matched by address.

The download page states no license. California public record.
https://www.abc.ca.gov/licensing/licensing-reports/
"""
import csv
import datetime
import io
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import CACHE, Writer, address, download

URL = "https://www.abc.ca.gov/wp-content/uploads/DailyExport-CSV.zip"
# 20/21 off-sale stores, 40/41/42/47/48/61 on-sale restaurants and bars,
# 23/75 breweries and brewpubs, 02 winegrowers, 74 craft distillers, 51/52/57 clubs
RETAIL = {"20", "21", "40", "41", "42", "47", "48", "61", "23", "75", "02", "74", "51", "52", "57"}


def main():
    today = datetime.date.today().isoformat()
    path = download(URL, os.path.join(CACHE, "abc_ca", "DailyExport-CSV-%s.zip" % today))
    out = Writer("abc_ca")
    seen = set()
    with zipfile.ZipFile(path) as z:
        f = io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8-sig", newline="")
        m = re.search(r"(\d{1,2})\w* of (\w+) (\d{4})", f.readline())
        if not m:
            raise SystemExit("no Updated line at the top of the export")
        as_of = datetime.datetime.strptime(" ".join(m.groups()), "%d %B %Y").date().isoformat()
        for raw in csv.DictReader(f):
            r = {k.strip(): (v or "").strip() for k, v in raw.items()}
            if r["Lic or App"] != "LIC" or r["Type Status"] != "ACTIVE":
                out.drop("not an active issued license")
                continue
            if r["License Type"] not in RETAIL:
                out.drop("not a retail license type")
                continue
            # one premises can hold several license types under one file number
            if r["File Number"] in seen:
                continue
            seen.add(r["File Number"])
            # With no trade name the file gives the license holder, who can be a person. Those
            # rows go out under their own source name: good for matching, never for adding a place.
            out.row("abc_ca" if r["DBA Name"] else "abc_ca_holder", r["File Number"], r["DBA Name"] or r["Primary Name"],
                    address(r["Prem Addr 1"], r["Prem City"], "%s %s" % (r["Prem State"], r["Prem Zip"][:5])),
                    None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
