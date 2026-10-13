#!/usr/bin/env python3
"""New York City DCWP: licensed businesses.

dcwp_nyc  a business premises with an active license from the Department of
          Consumer and Worker Protection (tobacco and electronics shops,
          secondhand dealers, laundries, garages, hotels, pawnbrokers, car
          washes and more), open as of the day the dataset was last updated.
          Positions come with the data.

Licenses held by a person rather than a premises are left out, and so are
trades with no shop a customer visits (home improvement contractors, debt
collectors, process servers, tow trucks, delivery services).

NYC Open Data. https://data.cityofnewyork.us/d/w7w3-xahh
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import rows, updated

HOST, DATASET = "data.cityofnewyork.us", "w7w3-xahh"
NO_SHOP = ("contractor", "debt collection", "process serv", "tow truck", "delivery", "horse drawn",
           "labor provider", "bingo", "games of chance", "ticket seller", "employment agency", "stoop line")


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("dcwp_nyc")
    for r in rows(HOST, DATASET, where="license_type = 'Premises' AND license_status = 'Active' AND address_state = 'NY'",
                  select="license_nbr,business_name,dba_trade_name,business_category,address_building,"
                         "address_street_name,address_city,address_zip,latitude,longitude,license_creation_date"):
        if any(word in (r.get("business_category") or "").lower() for word in NO_SHOP):
            out.drop("no shop a customer visits")
            continue
        street = ("%s %s" % (r.get("address_building") or "", r.get("address_street_name") or "")).strip()
        out.row("dcwp_nyc", r["license_nbr"], r.get("dba_trade_name") or r.get("business_name"),
                address(street, r.get("address_city"), "NY %s" % (r.get("address_zip") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "open", as_of, since=r.get("license_creation_date"))
    out.close()


if __name__ == "__main__":
    main()
