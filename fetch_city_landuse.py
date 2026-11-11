"""Download every record in the dated SF Planning release, without a spatial filter."""
import csv
import gzip
from pathlib import Path
from tempfile import TemporaryDirectory

from fetch import read_api

ROOT = Path(__file__).resolve().parent
FIELDS = ["ludb_id", "centroid_1", "centroid_l", "resunits", "data_as_of"]
DATE = "2026-08-17T00:00:00.000"
DEST = ROOT / "inputs/city_landuse_20260817.csv.gz"


def main():
    where = f"data_as_of = '{DATE}'"
    resource = "c5ge-t6pj.json"
    expected = int(read_api(resource, **{"$select": "count(*) as n", "$where": where})[0]["n"])
    if expected == 0:
        raise ValueError("The dated release is unavailable. Use the committed snapshot.")
    seen = set()
    with TemporaryDirectory(dir=DEST.parent) as temp:
        path = Path(temp) / DEST.name
        with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for offset in range(0, expected, 25000):
                rows = read_api(resource, **{"$select": ",".join(FIELDS), "$where": where,
                                "$order": "ludb_id", "$limit": 25000, "$offset": offset})
                for row in rows:
                    key = row["ludb_id"]
                    if key in seen:
                        raise ValueError(f"Repeated source ID: {key}")
                    seen.add(key)
                    writer.writerow(row)
        if len(seen) != expected:
            raise ValueError(f"Expected {expected} distinct records, received {len(seen)}")
        path.replace(DEST)
    print(f"Saved {expected:,} city records")


if __name__ == "__main__":
    main()
