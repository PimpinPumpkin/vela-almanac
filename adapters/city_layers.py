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
import csv
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import EVIDENCE, Writer, address, street_city

TODAY = datetime.date.today()
NOW_MS = int(datetime.datetime(TODAY.year, TODAY.month, TODAY.day).timestamp() * 1000)
MKE = "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/regulation/license/MapServer/"
DET = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/"

# source: layers, filter, id fields, name fields (first one filled wins), street, city (a field or a fixed name),
# state, ZIP field, and a date field when the rows carry their own
PHX = "https://maps.phoenix.gov/pub/rest/services/Public/LIQUOR_RACMap/MapServer/%d"
ANC = "https://services2.arcgis.com/Ce3DhLRthdwbHlfF/arcgis/rest/services/LiquorLicenses_Hosted/FeatureServer/0"
ANC_RETAIL = ("LicenseType LIKE '%Eating Place%' OR LicenseType LIKE '%Dispensary' OR LicenseType LIKE '%Package Store%'"
              " OR LicenseType LIKE 'Retail Community-Brewery%' OR LicenseType LIKE 'Retail Community-Winery%'"
              " OR LicenseType LIKE 'Retail Community-Distillery%' OR LicenseType LIKE '%Pub' OR LicenseType LIKE '%Golf Course'"
              " OR LicenseType LIKE '%Theater'")
# registers that write a business as "Legal Name (Trade Name)"
BRACKET_TRADE_NAME = {"nn_biz"}

SOURCES = {
    # Phoenix has a layer for each license series. Bars, stores, hotels, restaurants and
    # microbreweries (series 3, 6, 7, 9, 10, 11, 12) are premises a person walks into; producers,
    # wholesalers, clubs and special licenses are kept apart so they never add a place.
    "phx_liquor": ([PHX % i for i in (1, 4, 5, 7, 8, 9, 10)],
                   "LICENSE_STATUS = 'ACTIVE' AND JURISDICTION = 'INSIDE PHOENIX'",
                   ("STATE_LICENSE", "ACCOUNT_ID"), ("BUSINESS_NAME",), "BUSINESS_ADDRESS", "=PHOENIX", "AZ", "ZIP_CODE", None),
    "phx_liquor_trade": ([PHX % i for i in (0, 2, 3, 6, 11, 12, 13)],
                         "LICENSE_STATUS = 'ACTIVE' AND JURISDICTION = 'INSIDE PHOENIX'",
                         ("STATE_LICENSE", "ACCOUNT_ID"), ("BUSINESS_NAME",), "BUSINESS_ADDRESS", "=PHOENIX", "AZ", "ZIP_CODE", None),
    "nash_beer": (["https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Beer_Permit_Locations_Feature_Layer_view/FeatureServer/0"],
                  "Status = 'ISSUED'", ("Permit__",), ("Business_Name",), "Address", "City", "TN", "ZIP", None),
    "mke_food": ([MKE + "9"], "EXPIRATION_DATE > timestamp '%s 00:00:00'" % TODAY.isoformat(),
                 ("LICENSE_ID",), ("TRADE_NAME", "CORP_NAME"), "ENTITY_ADDRESS", "=MILWAUKEE", "WI", None, None),
    "mke_liquor": ([MKE + "0"], "EXPIRATION_DATE > timestamp '%s 00:00:00'" % TODAY.isoformat(),
                   ("LICENSE_ID",), ("TRADE_NAME", "CORP_NAME"), "ENTITY_ADDRESS", "=MILWAUKEE", "WI", None, None),
    # the same split for Anchorage, by license type
    "anc_liquor": ([ANC], "ExpirationYear >= '%d' AND (%s)" % (TODAY.year, ANC_RETAIL),
                   ("LicenseNumber",), ("Establishment",), "ServiceLocation", "=ANCHORAGE", "AK", None, None),
    "anc_liquor_trade": ([ANC], "ExpirationYear >= '%d' AND NOT (%s)" % (TODAY.year, ANC_RETAIL),
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
    "riverside_food": (["https://services1.arcgis.com/pWmBUdSlVpXStHU6/arcgis/rest/services/Food/FeatureServer/0"],
                       "Status = 'Active' AND Program_Type LIKE 'Retail Food - Permanent%'",
                       ("Establishment_ID",), ("Establishment_Name",), "Site_Address", "City__State__Zip", "CA", None, None),
    "cdph_ca_facilities": (["https://services5.arcgis.com/FlidZxdI0LGC9vAw/arcgis/rest/services/CDPH_LC_Facilities_Data/FeatureServer/0"],
                           "FAC_STATUS_TYPE_CODE = 'OPEN'",
                           ("FACID",), ("FACNAME",), "ADDRESS", "CITY", "CA", "ZIP", None),
    "co_tobacco": (["https://services3.arcgis.com/66aUo8zsujfVXRIT/arcgis/rest/services/PSD_TRAC_DOR_Licensed_Tobacco_Retailers/FeatureServer/0"],
                   "EXPIRES >= '%s'" % TODAY.isoformat(),
                   ("license_no",), ("DOING_BUSINESS_AS", "LICENSEE_NAME"), "STREET_ADDRESS", "CITY", "CO", "ZIP", None),
    "lac_biz": (["https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Business_License/FeatureServer/0"],
                "Business_Category NOT LIKE 'Apartment%'",
                ("Business_Name", "Address"), ("Business_Name",), "Address", "City", "CA", "Zip", None),
    # Maricopa County's terms say the layer is for county use and that outside use needs written
    # leave from its GIS office. The owner decided on 2026-10-12 to use it; see SOURCES.md.
    "maricopa_food": (["https://services.arcgis.com/ykpntM6e3tHvzKRJ/arcgis/rest/services/Restaurant_(External)/FeatureServer/0"],
                      "Status = 'Issued'",
                      ("LicenseNumber",), ("CompanyName",), "BusinessAddress", "City", "AZ", "Zip", None),
    # Virginia Beach asks that anything built on its data carry the city's disclaimer (NOTICE has
    # it). The table lists licenses as issued, so only those begun in the last two years are read.
    "vb_biz": (["https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Business_Licenses_view/FeatureServer/0"],
               "Business_State = 'VA' AND Business_City = 'VIRGINIA BEACH'"
               " AND Business_Classification NOT LIKE 'Community Event%' AND Business_Classification NOT LIKE 'Non-License%'"
               " AND Business_Classification NOT LIKE 'Nonstore%' AND Business_Classification NOT LIKE '%Rental%'"
               " AND Business_Classification NOT LIKE 'Construction%' AND Business_Classification NOT LIKE '%OOT'",
               ("OBJECTID",), ("Trade_Name",), "Business_Address", "Business_City", "VA", "Business_ZipCode", "Begin_Date"),
    "anaheim_biz": (["https://services3.arcgis.com/hPs600I3X0RTaaaq/arcgis/rest/services/ActiveBusinessLicenses/FeatureServer/0"],
                    "casestatus = 'Active'",
                    ("casenumber",), ("businessname",), "address", "=ANAHEIM", "CA", None, None),
    "tucson_liquor": (["https://services3.arcgis.com/9coHY2fvuFjG9HQX/arcgis/rest/services/Liquor_Licenses_Active_and_Pending_HFL/FeatureServer/16"],
                      "LICENSESTATUS = 'Active'",
                      ("LICENSENO",), ("BUSINESSNAME",), "BUSINESSADDRESS", "=TUCSON", "AZ", None, None),
    # the address comes whole: "291 N HUBBARDS LN, 130 Liquor, ST MATTHEWS, KY 40207"
    "lou_tobacco": (["https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/tobacco_licenses/FeatureServer/0"],
                    "License_Status = 'Active' AND Business_Type = 'Retailer'",
                    ("License_NO",), ("Business_Name",), "Address", "=", "KY", None, None),
    # stores authorized for the WIC nutrition program, as each state health department maps them
    "wic_fl": (["https://services1.arcgis.com/CY1LXxl9zlJeBuRZ/arcgis/rest/services/WIC_Vendors/FeatureServer/0"],
               "1=1", ("VENDOR_NAME", "PHYSADDRESS"), ("VENDOR_NAME",), "PHYSADDRESS", "PHYSCITY", "FL", "PHYSZIP", None),
    "wic_az": (["https://services1.arcgis.com/mpVYz37anSdrK4d8/arcgis/rest/services/WIC_Vendors/FeatureServer/1"],
               "1=1", ("VENDOR_NAME", "ADDRESS"), ("VENDOR_NAME",), "ADDRESS", "CITY", "AZ", "ZIPCODE", None),
    "wic_va": (["https://services8.arcgis.com/0xEpEhgj2AqvWPLe/arcgis/rest/services/WICRetailers/FeatureServer/0"],
               "1=1", ("Vendor_Name", "Address"), ("Vendor_Name",), "Address", "City", "VA", "ZipCode", None),
    "glendale_az_biz": (["https://services1.arcgis.com/9fVTQQSiODPjLUTa/arcgis/rest/services/Glendale_Business_Licenses/FeatureServer/0"],
                        "LicenseStatus = 'VALID' AND State = 'AZ'",
                        ("OBJECTID",), ("BusinessName",), "AddressLine1", "City", "AZ", "ZipCode", None),
    "wic_nj": (["https://services7.arcgis.com/Z0rixLlManVefxqY/arcgis/rest/services/wic_stores_6_24/FeatureServer/0"],
               "1=1", ("USER_Name", "USER_Address"), ("USER_Name",), "USER_Address", "USER_City", "NJ", "USER_Zip", None),
    # contractors, peddlers, direct sellers and short-term rentals work from no shop
    "nn_biz": (["https://services6.arcgis.com/SiUAoHzWN11AIADA/arcgis/rest/services/TEST/FeatureServer/0"],
               "LicenseStatus = 'Active' AND BusinessDescriptorCategory IN ('Retail', 'Repair, Personal, Business', "
               "'Professional', 'Wholesale Merchant', 'Barber & Beauty Schools')",
               ("BusinessName", "BusinessLocationAddress"), ("BusinessName",), "BusinessLocationAddress",
               "=NEWPORT NEWS", "VA", None, None),
    "sac_tobacco": (["https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/Tobacco_Retail_Points/FeatureServer/0"],
                    "LICENSE_STATUS = 'Licensed'",
                    ("LICENSE_NUMBER",), ("RETAILER_NAME",), "RETAILER_ADDRESS", "=SACRAMENTO", "CA", None, None),
    # shops the state agriculture department permits, as Fairfax County maps them
    "fairfax_food": (["https://services1.arcgis.com/ioennV6PpG5Xodq0/arcgis/rest/services/VDACS_Retail_Food_Establishments/FeatureServer/0"],
                     "1=1", ("VDACS_FIRM_NAME", "ADDRESS_1"), ("VDACS_FIRM_NAME",), "ADDRESS_1", "CITY", "VA", "ZIP_CODE", None),
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


def split_shared_file():
    """Every source used to share city_layers.csv. Cut it into one file per source, so a source whose
    server is down today still has last run's rows and nothing is counted twice."""
    shared = os.path.join(EVIDENCE, "city_layers.csv")
    if not os.path.exists(shared):
        return
    with open(shared, newline="") as f:
        rows = list(csv.reader(f))
    for source in sorted({r[0] for r in rows[1:]}):
        own = os.path.join(EVIDENCE, source + ".csv")
        if not os.path.exists(own):
            with open(own, "w", newline="") as f:
                csv.writer(f).writerows([rows[0]] + [r for r in rows[1:] if r[0] == source])
    os.remove(shared)


def main():
    """Each source is written to its own file, so one city's server being down leaves the others fresh
    and that city on last run's file."""
    only = os.environ.get("LAYERS", "").split()
    failed = []
    split_shared_file()
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
                    # "SPEEDY CHICKEN LLC (POPEYE'S)": the sign on the door is in the brackets
                    if source in BRACKET_TRADE_NAME:
                        name = re.sub(r"^(.+?)\s*\(([^()]{2,})\)?\s*$", r"\1 dba \2", name) if "(" in name else name
                    # "SACRAMENTO, CA" is a town with its state attached
                    town = city[1:] if city.startswith("=") else text(a.get(city)).split(",")[0]
                    stamp = a.get(dated) if dated else None
                    when = (day(stamp) if isinstance(stamp, (int, float))
                            else stamp[:10] if isinstance(stamp, str) and stamp[:4].isdigit()
                            else "%s-%s-%s" % (stamp[6:10], stamp[:2], stamp[3:5])
                            if isinstance(stamp, str) and re.match(r"\d\d/\d\d/\d{4}$", stamp) else as_of)
                    key = "-".join(text(a.get(i)) for i in ids)
                    where_ = " ".join(text(a.get(f)) for f in streets).strip()
                    zip5 = text(a.get(zip_field))[:5]
                    # an address given as two lines: "1221 E Orangethorpe Ave" / "Fullerton, Ca 92831"
                    two = re.match(r"(.+?)\s*[\r\n]+\s*([^,\r\n]+),\s*[A-Za-z]{2}\s+(\d{5})", str(a.get(streets[0]) or ""))
                    # one line with commas: "291 N HUBBARDS LN, 130 Liquor, ST MATTHEWS, KY 40207"
                    if not two and not zip_field:
                        two = re.match(r"([^,]+),(?:[^,]*,)?\s*([^,]+),\s*[A-Za-z]{2}\s+(\d{5})", where_)
                    one = None if two or zip_field else street_city(where_)
                    if one:
                        two = re.match(r"(.*)\|(.*)\|(.*)", "%s|%s|%s" % (one[0], one[1], one[3]))
                    if two:
                        where_, town, zip5 = " ".join(two.group(1).split()), two.group(2).strip(), two.group(3)
                        if city.startswith("=") and city[1:] and town.upper() != city[1:]:
                            continue  # licensed here, located in another town
                    row = (source, key, name,
                           address(where_, town, ("%s %s" % (state, zip5)).strip()),
                           lat, lng, "open", when)
                    # a layer with a row for every inspection: keep each place's newest
                    if key not in newest or when > newest[key][7]:
                        newest[key] = row
            for row in newest.values():
                out.row(*row)
            # rows with no point of their own go to the Census geocoder
            out.close(geocode=any(row[4] is None for row in newest.values()))
        except (Exception, SystemExit) as e:
            out.f.close()
            os.remove(out.path + ".part")
            failed.append("%s: %s" % (source, str(e)[:120]))
    if failed:
        print("city_layers, sources that failed: " + "; ".join(failed), file=sys.stderr)
        # prepare.sh reads the names from this file, so the watch report flags the one source,
        # not every source this reader writes
        note = os.environ.get("ALMANAC_FAILED")
        if not note:
            raise SystemExit(1)
        with open(note, "a") as f:
            f.writelines(x.split(":")[0].split(" (")[0] + "\n" for x in failed)


if __name__ == "__main__":
    main()
