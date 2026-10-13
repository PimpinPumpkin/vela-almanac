#!/usr/bin/env python3
"""City of Fort Worth: certificates of occupancy.

fw_co        a business the city certified to occupy a commercial space,
             open as of the day the certificate was issued. Certificates
             of the last three years are read; an older one says little
             about who is behind the door today.
fw_co_build  the same for a certificate that closes a building permit (a
             new building, a remodel, an addition). These name projects
             and buildings as often as businesses, so they are a source of
             their own that never adds a place.

A certificate is issued when a business moves in, when a use changes and
when a new building is finished, so this is a list of openings, not a
roster: nothing here says a business is still there. Homes, apartment
buildings, warehouses, shells and accessory structures are left out. Where
one occupant holds several certificates at an address the newest is read.

City of Fort Worth Development Services Department. CC BY.
https://data.fortworthtexas.gov
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, features
from evidence import Writer, address

LAYER = ("https://services5.arcgis.com/3ddLCBXe1bRt7mzj/arcgis/rest/services/"
         "CFW_Open_Data_Certificates_of_Occupancy_Table_view/FeatureServer/0")
USES = ("Sales and Service", "Office", "Assembly", "Education", "Mixed Use", "Institutional", "Auto Sales")


def main():
    since = (datetime.date.today() - datetime.timedelta(days=3 * 365)).isoformat()
    where = ("Status = 'Finaled' AND ApplicationType IN ('Occupancy', 'Commercial Building Permit') "
             "AND JobUse IN (%s) AND CODate >= DATE '%s'" % (", ".join("'%s'" % u for u in USES), since))
    newest = {}
    for a, _ in features(LAYER, where=where, geometry=False,
                         fields="PermitID,ApplicationType,Occupant,ProjectName,Location,Latitude,Longitude,CODate"):
        name = (a.get("Occupant") or "").strip()
        # the occupant field sometimes holds a suite number or a count
        if not name or name.isdigit():
            name = (a.get("ProjectName") or "").strip()
        # "2902 E BERRY ST, FORT WORTH, TX"
        street = (a.get("Location") or "").split(",")[0].strip()
        when = day(a["CODate"])
        key = (name.upper(), street.upper())
        if key not in newest or when > newest[key][-1]:
            newest[key] = ("fw_co" if a.get("ApplicationType") == "Occupancy" else "fw_co_build",
                           a.get("PermitID"), name, address(street, "FORT WORTH", "TX"),
                           a.get("Latitude"), a.get("Longitude"), when)
    for source in ("fw_co", "fw_co_build"):
        out = Writer(source)
        for row in newest.values():
            if row[0] == source:
                out.row(*row[:6], "open", row[6])
        out.close()


if __name__ == "__main__":
    main()
