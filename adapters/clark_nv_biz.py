#!/usr/bin/env python3
"""Clark County, Nevada: business licenses (unincorporated county, which holds the Las Vegas
Strip, Paradise, Spring Valley, Enterprise and Sunrise Manor).

clark_nv_biz  a location whose license is in force ("Licensed"), open as of the day the
              layer was read. The license's first issue is passed on as the place's
              opening day.

Kinds that have no door a customer walks through (property management, short-term
rentals, contractors, vendors who travel) are left out. Phone numbers are not read.

Clark County Business License. https://maps.clarkcountynv.gov/arcgis/rest/services/BusinessLicense
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import features
from evidence import Writer, address

LAYER = "https://maps.clarkcountynv.gov/arcgis/rest/services/BusinessLicense/BusinessLicenseData/FeatureServer/1"
NO_DOOR = re.compile(r"property manage|rental|short.?term|contractor|solicit|peddl|vendor|mobile|"
                     r"home based|home occupation|delivery|transport|limousine|taxi|towing|security|"
                     r"consult|out of county|employment agen|independent|lodging tax|mail fax|franchise|"
                     r"telecom|^reg -|broker|gaming|agenda|master license|holding company|penalty|"
                     r"special folder|work card|unlicensed|telemarket|peer-to-peer|driver|construction|"
                     r"landfill|waste|sanitation|armored|process server|repossess|outcall|traveling|"
                     r"temporary|adjuster|bus stop|ambulance|special event|advertising|septic|"
                     r"exterminat|welder|pedicab|auctioneer|promoter|appraiser|appraisal|escrow|factoring|"
                     r"investigation|electric power|wireless service|accommodations facilitator|"
                     r"timeshare|time share|commercial leasing|other activities related to real estate|"
                     r"contract labor|mobile home|outside pgc|incidental activity", re.I)


def main():
    today = datetime.date.today().isoformat()
    out = Writer("clark_nv_biz")
    fields = ("USER_FullCredentialNumber,USER_LocationName,USER_unitLine,USER_AddressLine1,USER_City,"
              "USER_ZipCode,USER_CredentialDescription,USER_InitialLicenseIssuedDate")
    for a, (lat, lng) in features(LAYER, where="USER_StatusDescription = 'Licensed'", fields=fields):
        if NO_DOOR.search(a.get("USER_CredentialDescription") or ""):
            out.drop("no door a customer walks through")
            continue
        first = str(a.get("USER_InitialLicenseIssuedDate") or "")
        since = "%s-%s-%s" % (first[:4], first[4:6], first[6:8]) if re.match(r"\d{8}$", first) else None
        out.row("clark_nv_biz", a.get("USER_FullCredentialNumber"), a.get("USER_LocationName"),
                address(a.get("USER_AddressLine1"), a.get("USER_City"), "NV %s" % str(a.get("USER_ZipCode") or "")[:5]),
                lat, lng, "open", today, since=since)
    out.close()


if __name__ == "__main__":
    main()
