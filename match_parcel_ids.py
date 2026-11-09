"""Look up map parcel IDs for the single-parcel land-use records."""
import csv
import json
from pathlib import Path
from fetch import read_api

root = Path(__file__).resolve().parent
points = json.loads((root / "results/landuse_points_with_acs.geojson").read_text())
ids = [f["properties"]["ludb_id"] for f in points["features"]
       if f["properties"]["geography_type"] == "parcel"]
if not ids or len(ids) != len(set(ids)):
    raise ValueError("토지이용 기록 번호를 확인하세요.")

lookup = {}
for start in range(0, len(ids), 50):
    batch = ids[start:start + 50]
    values = ",".join("'" + key.replace("'", "''") + "'" for key in batch)
    rows = read_api("c5ge-t6pj.json", **{"$select": "ludb_id,mapblklot",
                                       "$where": f"ludb_id in ({values})",
                                       "$limit": 50000})
    for row in rows:
        key = row["ludb_id"]
        if key in lookup:
            raise ValueError(f"원자료에 중복된 기록 번호: {key}")
        lookup[key] = row.get("mapblklot", "")

target = root / "results/parcel_ids.csv"
temp = target.with_suffix(".tmp")
with temp.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["ludb_id", "mapblklot", "status"])
    for key in ids:
        parcel = lookup.get(key, "")
        status = "matched" if parcel else ("missing_id" if key in lookup else "not_found")
        writer.writerow([key, parcel, status])
temp.replace(target)
matched = sum(bool(lookup.get(key)) for key in ids)
print(f"단일 필지 기록 {len(ids)}건 | 번호 있음 {matched}건 | 번호 미확인 {len(ids)-matched}건")
