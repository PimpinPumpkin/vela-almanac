#!/usr/bin/env python3
"""City of New Orleans: active occupational licenses.

biz_nola  a business holding an active occupational license, open as of the
          day the dataset was last updated. Positions come with the data.

Every business in the city holds one, so the file has people working from
home, drivers and street vendors beside the shops. Those trades are left
out, only the business name and address are read (not the owner or the
phone number), and nothing here creates a place.

Creative Commons Zero, as stated on the dataset.
https://data.nola.gov/d/iqay-p646
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.nola.gov", "iqay-p646"
NOT_A_SHOP = ("home based", "special events", "taxi", "limousine", "on streets", "flea market", "lessors of",
              "contractors", "peddler", "vendor", "tour guide", "pedicab")


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("biz_nola")
    seen = set()
    for r in rows(HOST, DATASET, where="state = 'LA'",
                  select="businesslicensenumber,businessname,businesstype,businessaddress,city,zip,the_geom,businessstartdate"):
        kind = (r.get("businesstype") or "").lower()
        if any(k in kind for k in NOT_A_SHOP):
            out.drop("not a shop-front trade")
            continue
        # one license per line of business at the same counter
        key = ((r.get("businessname") or "").upper(), r.get("businessaddress"))
        if key in seen:
            continue
        seen.add(key)
        lat, lng = point(r.get("the_geom"))
        out.row("biz_nola", r.get("businesslicensenumber"), r.get("businessname"),
                address(r.get("businessaddress"), r.get("city"), "LA %s" % (r.get("zip") or "")[:5]),
                lat, lng, "open", as_of, since=r.get("businessstartdate"))
    out.close()


if __name__ == "__main__":
    main()
