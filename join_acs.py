"""Attach tract tenure estimates to points and summarize Chinatown land-use records."""
import csv
import json
from collections import Counter
from pathlib import Path

results = Path(__file__).resolve().parent / "results"
with (results / "acs_tracts.csv").open(encoding="utf-8", newline="") as stream:
    acs = {}
    for row in csv.DictReader(stream):
        key = row["GEOID"]
        if key in acs:
            raise ValueError(f"중복 ACS 지역 번호: {key}")
        acs[key] = row

points = json.loads((results / "landuse_points_with_tract.geojson").read_text())
counts = Counter()
units = Counter()
for feature in points["features"]:
    props = feature["properties"]
    key = props["GEOID"]
    rate = acs[key]["renter_pct"]
    props["tract_renter_pct_2020_2024"] = float(rate) if rate else None
    counts[key] += 1
    units[key] += int(props["resunits"])

with (results / "tract_summary.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["GEOID", "chinatown_landuse_records", "chinatown_resunits",
                     "tract_occupied_units_acs", "tract_renter_occupied_acs",
                     "tract_renter_pct_2020_2024"])
    for key in sorted(counts):
        row = acs[key]
        writer.writerow([key, counts[key], units[key], row["occupied_units"],
                         row["renter_occupied"], row["renter_pct"]])

(results / "landuse_points_with_acs.geojson").write_text(json.dumps(points), encoding="utf-8")
print(f"ACS 연결 완료: {len(counts)}개 tract, 중심점 {sum(counts.values()):,}개, 주택 {sum(units.values()):,}호")
