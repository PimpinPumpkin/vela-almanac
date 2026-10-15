"""Shared pieces for evidence adapters.

Every adapter writes one CSV with the same eight columns:
source, source_id, name, address, lat, lng, state, date
state is open or closed. date is ISO (YYYY-MM-DD) and means "open as of" or
"closed on". lat and lng may be blank when the address ends in a ZIP code;
such rows are matched by address. Rows with neither, or with no date or
name, are dropped and counted.
"""
import csv
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("ALMANAC_DATA", os.path.join(ROOT, "data"))
CACHE = os.path.join(DATA, "cache")
EVIDENCE = os.path.join(CACHE, "evidence")
# Records kept from month to month but not used by the build yet. Some
# registers only publish their last few weeks; holding each month's copy lets
# the records add up until there are enough to test.
HELD = os.path.join(CACHE, "held")

_contact = os.environ.get("ALMANAC_CONTACT")
UA = "VelaAlmanac/0.1 (open US places dataset build; https://github.com/PimpinPumpkin/vela-almanac%s)" % (
    "; " + _contact if _contact else "")

COLUMNS = ["source", "source_id", "name", "address", "lat", "lng", "state", "date"]


_CONTEXT = None


def _context():
    """The default trust store plus lib/extra-ca.pem: public intermediate certificates that
    some government servers fail to send (gis.nola.gov). Verification stays on."""
    global _CONTEXT
    if _CONTEXT is None:
        import ssl
        _CONTEXT = ssl.create_default_context()
        extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extra-ca.pem")
        if os.path.exists(extra):
            _CONTEXT.load_verify_locations(extra)
    return _CONTEXT


def get(url, tries=4):
    """Fetch a URL with the project User-Agent. Returns bytes."""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120, context=_context()) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            if getattr(e, "code", None) == 404 or attempt == tries - 1:
                raise
            print("retry %s: %s" % (url[:80], e), file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def download(url, path):
    """Fetch a URL to a file once; later runs reuse the file."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".part", "wb") as f:
        f.write(get(url))
    os.replace(path + ".part", path)
    return path


_PLACE = re.compile(
    r"^(.*\b(?:street|st|avenue|ave|av|road|rd|drive|dr|boulevard|blvd|highway|hwy|route|rte|lane|ln|way|court|ct|"
    r"place|pl|terrace|ter|parkway|pkwy|pike|circle|cir|trail|trl|plaza|square|sq|broadway|main|north|south|east|west|"
    r"n|s|e|w|ne|nw|se|sw|(?:suite|ste|unit|apt|bldg|#)\s*[\w-]+|\d+)\.?)\s+([A-Za-z][A-Za-z .'-]+?),\s*([A-Z]{2})\s+(\d{5})",
    re.I)


def street_city(text):
    """("street", "town", "ST", "12345") from "810 Bridge Street Humboldt, KS 66748", where nothing
    separates the street from the town. The town is what follows the last street word, direction,
    unit or number. None when the text does not end in a state and ZIP or cannot be split."""
    m = _PLACE.match(" ".join((text or "").split()))
    return (m.group(1), m.group(2), m.group(3).upper(), m.group(4)) if m else None


def address(*parts):
    return ", ".join(p.strip() for p in parts if p and p.strip())


from geocode import locate  # noqa: E402  (same folder)


class Writer:
    """Writes evidence rows, dropping and counting the unusable ones."""

    def __init__(self, name, held=False):
        """held=True writes to the held folder and keeps the rows already there."""
        folder = HELD if held else EVIDENCE
        os.makedirs(folder, exist_ok=True)
        self.held = held
        self.path = os.path.join(folder, name + ".csv")
        self.f = open(self.path + ".part", "w", newline="")
        self.w = csv.writer(self.f)
        self.w.writerow(COLUMNS)
        self.name = name
        self.kept = {}
        self.ids = set()
        self.dropped = {}
        self.opened = []

    def drop(self, why):
        self.dropped[why] = self.dropped.get(why, 0) + 1

    def row(self, source, source_id, name, addr, lat, lng, state, date, since=None):
        """since: the day the business opened at this address, where the register says so
        (a certificate of occupancy, a license's first issue). It goes to a file of its
        own, since/<name>.csv, and never changes what the row itself says."""
        if lat in (None, "") and lng in (None, ""):
            if not re.search(r"\d{5}(-\d{4})?\s*$", addr or ""):
                return self.drop("no position and no ZIP")
            lat = lng = ""
        else:
            try:
                lat, lng = "%.6f" % float(lat), "%.6f" % float(lng)
            except (TypeError, ValueError):
                return self.drop("no position")
            if not (17 < float(lat) < 72 and -180 < float(lng) < -64):
                return self.drop("no position")
        if not date or len(date) != 10:
            return self.drop("no date")
        if not name:
            return self.drop("no name")
        # an id must name one record; a register that repeats one keeps its first row
        if (source, source_id) in self.ids:
            return self.drop("same id twice")
        self.ids.add((source, source_id))
        self.w.writerow([source, source_id, name.strip(), addr, lat, lng, state, date])
        if since and re.match(r"(19[5-9]|20)\d\d-\d\d-\d\d$", str(since)[:10]) and str(since)[:10] <= date:
            self.opened.append((source, source_id, str(since)[:10]))
        key = (source, state)
        self.kept[key] = self.kept.get(key, 0) + 1

    def close(self, geocode=False):
        """Finish the file. With geocode=True, rows that have an address but no
        position are sent to the Census geocoder first (US addresses only)."""
        self.f.close()
        if geocode:
            self._geocode()
        if self.held:
            self._keep_earlier()
        os.replace(self.path + ".part", self.path)
        if self.opened and not self.held:
            folder = os.path.join(EVIDENCE, "since")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, self.name + ".csv.part"), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(("source", "source_id", "since"))
                w.writerows(self.opened)
            os.replace(os.path.join(folder, self.name + ".csv.part"), os.path.join(folder, self.name + ".csv"))
            print("opening dates: %d" % len(self.opened))
        for (source, state), n in sorted(self.kept.items()):
            print("%s %s: %d" % (source, state, n))
        for why, n in sorted(self.dropped.items()):
            print("dropped, %s: %d" % (why, n))

    def _geocode(self):
        with open(self.path + ".part", newline="") as f:
            rows = list(csv.reader(f))
        head, rows = rows[0], rows[1:]
        a, lat, lng = head.index("address"), head.index("lat"), head.index("lng")
        found = locate([r[a] for r in rows if not r[lat]], os.path.join(CACHE, "geocode"), UA)
        placed = 0
        for r in rows:
            if not r[lat] and r[a] in found:
                r[lat], r[lng] = ("%.6f" % float(v) for v in found[r[a]])
                placed += 1
        with open(self.path + ".part", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows(rows)
        missing = sum(1 for r in rows if not r[lat])
        print("geocoded: %d placed, %d left with an address only" % (placed, missing))

    def _keep_earlier(self):
        """Add back rows from earlier runs that this run did not see again."""
        if not os.path.exists(self.path):
            return
        with open(self.path + ".part", newline="") as f:
            new = list(csv.reader(f))
        have = {(r[0], r[1]) for r in new[1:]}
        with open(self.path, newline="") as f:
            old = [r for r in list(csv.reader(f))[1:] if (r[0], r[1]) not in have]
        with open(self.path + ".part", "w", newline="") as f:
            csv.writer(f).writerows(new + old)
        print("held: %d rows from this run, %d kept from earlier" % (len(new) - 1, len(old)))
