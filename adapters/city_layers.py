#!/usr/bin/env python3
"""City license and inspection layers for six more cities.

phx_liquor   Phoenix: an active liquor license inside the city
nash_beer    Nashville: an issued beer permit
mke_food     Milwaukee: an unexpired food dealer license
mke_liquor   Milwaukee: an unexpired alcohol license
anc_liquor   Anchorage: a liquor license good for this year or later
sux_food     Sioux Falls: a food site, dated by its newest inspection
hsv_liquor   Huntsville: an active alcohol license renewed for this year
det_biz      Detroit: an unexpired city business license
det_liquor   Detroit: an active state liquor license in the city

All are open as of the day the layer was last edited (the day it was read
when the layer does not say), except Sioux Falls, which carries inspection
dates. Positions come with the data. Agent, owner and licensee columns are
not read.

Milwaukee's data is CC BY (City of Milwaukee). The others state no
license. Layer addresses are in SOURCES.md.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import EVIDENCE, Writer, address

TODAY = datetime.date.today()
NOW_MS = int(datetime.datetime(TODAY.year, TODAY.month, TODAY.day).timestamp() * 1000)
MKE = "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/regulation/license/MapServer/"
DET = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/"

# source: layers, filter, id fields, name fields (first one filled wins), street, city (a field or a fixed name),
# state, ZIP field, and a date field when the rows carry their own
SOURCES = {
    "phx_liquor": (["https://maps.phoenix.gov/pub/rest/services/Public/LIQUOR_RACMap/MapServer/%d" % i for i in range(14)],
                   "LICENSE_STATUS = 'ACTIVE' AND JURISDICTION = 'INSIDE PHOENIX'",
                   ("STATE_LICENSE", "ACCOUNT_ID"), ("BUSINESS_NAME",), "BUSINESS_ADDRESS", "=PHOENIX", "AZ", "ZIP_CODE", None),
    "nash_beer": (["https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Beer_Permit_Locations_Feature_Layer_view/FeatureServer/0"],
                  "Status = 'ISSUED'", ("Permit__",), ("Business_Name",), "Address", "City", "TN", "ZIP", None),
    "mke_food": ([MKE + "9"], "EXPIRATION_DATE > timestamp '%s 00:00:00'" % TODAY.isoformat(),
                 ("LICENSE_ID",), ("TRADE_NAME", "CORP_NAME"), "ENTITY_ADDRESS", "=MILWAUKEE", "WI", None, None),
    "mke_liquor": ([MKE + "0"], "EXPIRATION_DATE > timestamp '%s 00:00:00'" % TODAY.isoformat(),
                   ("LICENSE_ID",), ("TRADE_NAME", "CORP_NAME"), "ENTITY_ADDRESS", "=MILWAUKEE", "WI", None, None),
    "anc_liquor": (["https://services2.arcgis.com/Ce3DhLRthdwbHlfF/arcgis/rest/services/LiquorLicenses_Hosted/FeatureServer/0"],
                   "ExpirationYear >= '%d'" % TODAY.year,
                   ("LicenseNumber",), ("Establishment",), "ServiceLocation", "=ANCHORAGE", "AK", None, None),
    "sux_food": (["https://gis.siouxfalls.gov/arcgis/rest/services/Data/Safety/MapServer/17"],
                 "SITE_TYPE <> 'MOB'", ("SITE_INV",), ("SITE_NAME",), "FULL_ADDRESS", "=SIOUX FALLS", "SD", None, "INSP_DATE1"),
    "hsv_liquor": (["https://maps.huntsvilleal.gov/server/rest/services/Licenses/AlcoholBeverageLicenses/MapServer/0"],
                   "Status = 'ACTIVE' AND LastBusYear >= %d" % TODAY.year,
                   ("LocationID", "SchID"), ("LocDBA", "BusinessName"), "address_full", "MailCity", "AL", "ZipCode", None),
    "det_biz": ([DET + "bseed_active_business_licenses/FeatureServer/0"], "expiration_date >= '%s'" % TODAY.isoformat(),
                ("record_id",), ("business_name",), "address", "=DETROIT", "MI", "zip_code", None),
    "det_liquor": ([DET + "Liquor_Licenses/FeatureServer/0"], "status = 'Active'",
                   ("address_id", "type"), ("dba", "account_name"), "street_address", "=DETROIT", "MI", "zip_code", None),
    "det_food": ([DET + "food_service_establishment_inspections/FeatureServer/0"], "establishment_status = 'Open'",
                 ("establishment_id",), ("establishment_name",), "address", "=DETROIT", "MI", "zip_code", None),
    "alameda_food": (["https://services5.arcgis.com/ROBnTHSNjoZ2Wm1P/arcgis/rest/services/Restaurant_Inspections/FeatureServer/0"],
                     "Activity_Date >= '%s'" % (TODAY - datetime.timedelta(days=730)).isoformat(),
                     ("Facility_ID",), ("Facility_Name",), "Address", "City", "CA", "Zip", "Activity_Date"),
    "miami_dade_biz": (["https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/Local_Business_Tax_Feature_Layer_View/FeatureServer/0"],
                       "ACCSTATUS = 'Active' AND RCPTSTATUS = 'Active'",
                       ("RECEIPTNO",), ("BUSNAME",), "BUSADDR", "BUSCITY", "FL", "ZIPCODE", None),
    "longbeach_biz": (["https://services6.arcgis.com/yCArG7wGXGyWLqav/arcgis/rest/services/Business_Licenses_Public_View/FeatureServer/0"],
                      "LICSTATUS = 'Active' AND HOMEBASED = 'No' AND OUTSIDECITY = 'No' AND DBANAME IS NOT NULL"
                      " AND CLASSDESC NOT LIKE 'Rental%'",
                      ("LICENSENO",), ("DBANAME",), "SITELOCATION", "=LONG BEACH", "CA", "ZIP", None),
    "broward_biz": (["https://services.arcgis.com/JMAJrTsHNLrSsWf5/arcgis/rest/services/TaxDatabase2021/FeatureServer/0"],
                    "Year >= %d" % (TODAY.year - 1),
                    ("Account__",), ("DBA_Name", "Business_Name"), "Business_Address_Line_1", "Business_City", "FL",
                    "Business_Zip", None),
    "tucson_biz": (["https://services3.arcgis.com/9coHY2fvuFjG9HQX/arcgis/rest/services/BUSLIC/FeatureServer/9"],
                   "LIC_STATUS = 'Active' AND HOME_OCCUPATION <> 'T'",
                   ("ACC_NUM",), ("ACC_NAME",), "ADDRESS", "CITY", "AZ", "ZIP_CODE", None),
    "bellevue_biz": (["https://services1.arcgis.com/EYzEZbDhXZjURPbP/arcgis/rest/services/Business_Licenses_(All)/FeatureServer/3"],
                     "CancelDate IS NULL AND PhysicalCity = 'BELLEVUE'",
                     ("BusinessId",), ("Dba", "LegalEntityName"), "PhysicalAddressLine1", "=BELLEVUE", "WA",
                     "PhysicalPostalCode", None),
    "saccounty_biz": (["https://services1.arcgis.com/5NARefyPVtAeuJPU/arcgis/rest/services/Business_Licenses/FeatureServer/0"],
                      "ExpirationDate > timestamp '%s 00:00:00' AND Location = 'Commercial'" % TODAY.isoformat(),
                      ("Record_number",), ("Business_Name",), ("stNumber", "StName"), "CityState", "CA", "Zip", None),
    "chesapeake_biz": (["https://services1.arcgis.com/OAphVRUvJVpBRovs/arcgis/rest/services/Business_Licenses/FeatureServer/1"],
                       "OUTDATE = '0001-01-01' AND RESIDENCECOMMERCE = 'Commercial'",
                       ("ACCOUNTNUMBER",), ("TRADENAME",), "ADDRESS", "=CHESAPEAKE", "VA", "ZIPCODE", None),
}


def text(v):
    return "" if v is None else " ".join(str(v).split())


def main():
    """Each source is written to its own file, so one city's server being down leaves the others fresh
    and that city on last run's file."""
    only = os.environ.get("LAYERS", "").split()
    failed = []
    for source, (layers, where, ids, names, street, city, state, zip_field, dated) in sorted(SOURCES.items()):
        if only and source not in only:
            continue
        streets = street if isinstance(street, tuple) else (street,)
        fields = ",".join(f for f in ids + names + streets + (zip_field, dated, None if city.startswith("=") else city) if f)
        out = Writer(source)
        newest = {}
        try:
            for layer in layers:
                as_of = edited(layer) or TODAY.isoformat()
                for a, (lat, lng) in features(layer, where=where, fields=fields):
                    name = next((text(a.get(n)) for n in names if text(a.get(n))), "")
                    # "SACRAMENTO, CA" is a town with its state attached
                    town = city[1:] if city.startswith("=") else text(a.get(city)).split(",")[0]
                    stamp = a.get(dated) if dated else None
                    when = (day(stamp) if isinstance(stamp, (int, float))
                            else stamp[:10] if isinstance(stamp, str) and stamp[:4].isdigit() else as_of)
                    key = "-".join(text(a.get(i)) for i in ids)
                    row = (source, key, name,
                           address(" ".join(text(a.get(f)) for f in streets).strip(), town,
                                   ("%s %s" % (state, text(a.get(zip_field))[:5])).strip()),
                           lat, lng, "open", when)
                    # a layer with a row for every inspection: keep each place's newest
                    if key not in newest or when > newest[key][7]:
                        newest[key] = row
            for row in newest.values():
                out.row(*row)
            out.close()
        except (Exception, SystemExit) as e:
            out.f.close()
            os.remove(out.path + ".part")
            failed.append("%s: %s" % (source, str(e)[:120]))
    # the single file every source used to share
    old = os.path.join(EVIDENCE, "city_layers.csv")
    if not failed and not only and os.path.exists(old):
        os.remove(old)
    if failed:
        raise SystemExit("city_layers, sources that failed: " + "; ".join(failed))


if __name__ == "__main__":
    main()
