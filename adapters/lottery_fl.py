#!/usr/bin/env python3
"""Florida Lottery retailers.

lottery_fl  a store with an active lottery terminal, open as of the day
            the layer was last edited. Positions come with the data.

The Florida Division of Emergency Management publishes the Lottery's
terminal list as a map layer, refreshed daily: supermarkets, convenience
stores with and without fuel, liquor stores and the like. One row per
retailer; phone numbers are not read.

Florida public record. No license stated.
https://services.arcgis.com/3wFbqsFPLeKqOlIK/arcgis/rest/services/Lottery_Terminals/FeatureServer/0
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import edited, features
from evidence import Writer, address

LAYER = "https://services.arcgis.com/3wFbqsFPLeKqOlIK/arcgis/rest/services/Lottery_Terminals/FeatureServer/0"
# "301 S State Road 7, Hollywood, BROWARD, 33023-6756"
WHERE = re.compile(r"(.+),\s*([^,]+),\s*[^,]+,\s*(\d{5})")


def main():
    as_of = edited(LAYER) or datetime.date.today().isoformat()
    out = Writer("lottery_fl")
    for a, (lat, lng) in features(LAYER, where="STATUS = 'Active'", fields="NAME,DESCRIPTION,PRN"):
        m = WHERE.match(a.get("DESCRIPTION") or "")
        if not m:
            out.drop("address not understood")
            continue
        # a retailer with several terminals is listed once per terminal
        out.row("lottery_fl", a.get("PRN"), a.get("NAME"),
                address(m.group(1), m.group(2), "FL %s" % m.group(3)), lat, lng, "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
