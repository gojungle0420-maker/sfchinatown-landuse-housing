"""Join single-parcel land-use records to active mapped parcel boundaries."""
import csv
import json
from collections import defaultdict
from pathlib import Path

from fetch import read_api

results = Path(__file__).resolve().parent / "results"
points = json.loads((results / "landuse_points_with_acs.geojson").read_text())
records = {f["properties"]["ludb_id"]: f["properties"] for f in points["features"]
           if f["properties"]["geography_type"] == "parcel"}
with (results / "parcel_ids.csv").open(newline="") as stream:
    rows = list(csv.DictReader(stream))
ids = {r["mapblklot"]: r["ludb_id"] for r in rows if r["status"] == "matched"}
if len(ids) != len(rows) or len(ids) != len(records) or set(ids.values()) != set(records):
    raise ValueError("필지 번호의 누락 또는 중복을 확인하세요.")

keys = sorted(ids)
features = []
audit = []
for start in range(0, len(keys), 25):
    batch = keys[start:start + 25]
    values = ",".join("'" + key.replace("'", "''") + "'" for key in batch)
    data = read_api("acdm-wktn.geojson", **{
        "$where": f"active = true AND mapblklot IN ({values})", "$limit": 50000})
    candidates = defaultdict(dict)
    if len(data["features"]) >= 50000:
        raise ValueError("조회 한도에 도달했습니다.")
    for f in data["features"]:
        p = f["properties"]
        signature = json.dumps([f["geometry"], p.get("zoning_code"), p.get("zoning_district")], sort_keys=True)
        candidates[p["mapblklot"]][signature] = f
    for key in batch:
        group = list(candidates[key].values())
        record = records[ids[key]]
        if len(group) != 1 or not group[0]["geometry"]:
            reason = "multiple_candidates" if len(group) > 1 else "missing_boundary"
            audit.append([key, ids[key], reason, record["resunits"]])
            continue
        feature = group[0]
        p = feature["properties"]
        p["parcel_data_as_of"] = p.pop("data_as_of", None)
        p.update(record)
        features.append(feature)

collection = {"type": "FeatureCollection", "features": features}
(results / "chinatown_parcels.geojson").write_text(json.dumps(collection), encoding="utf-8")
with (results / "parcel_join_review.csv").open("w", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["mapblklot", "ludb_id", "reason", "resunits"])
    writer.writerows(audit)
print(f"지도에 표시 {len(features)}건 | 경계 확인 필요 {len(audit)}건")
