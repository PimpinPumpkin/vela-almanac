#!/usr/bin/env python3
"""City of San Diego: active business tax certificates.

biz_sandiego  a business with an active tax certificate that has not
              expired, open as of the day the file was read. Positions
              come with the data.

Every business in the city holds one, so the file has people working
from home beside the shops; nothing here creates a place. Only the trade
name and address are read, never the owner's name.

ODC Public Domain Dedication and License, as stated on the dataset page.
https://data.sandiego.gov/datasets/business-tax-certificates/
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://seshat.datasd.org/business_tax_certificates/sd_businesses_active_datasd.csv"


def main():
    today = datetime.date.today().isoformat()
    out = Writer("biz_sandiego")
    for r in csv.DictReader(io.StringIO(get(URL).decode("utf-8-sig", "replace"))):
        if r.get("account_status") != "Active" or (r.get("date_cert_expiration") or "")[:10] < today:
            out.drop("not in force")
            continue
        if r.get("address_po_box") or r.get("address_pmb_box"):
            out.drop("a mailbox")
            continue
        street = " ".join(x for x in (r.get("address_no"), r.get("address_pd"), r.get("address_road"), r.get("address_sfx")) if x)
        out.row("biz_sandiego", (r.get("account_key") or "").split(".")[0], r.get("dba_name"),
                address(street, r.get("address_city"), "CA %s" % (r.get("address_zip") or "")[:5]),
                r.get("lat"), r.get("lng"), "open", today)
    out.close()


if __name__ == "__main__":
    main()
