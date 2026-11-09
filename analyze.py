"""Summarize land-use records whose published center falls in Chinatown."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def inside_ring(x, y, ring):
    # 동쪽으로 그은 선이 경계와 홀수 번 교차하면 내부입니다.
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
        if (ay > y) != (by > y):
            crossing = ax + (y - ay) * (bx - ax) / (by - ay)
            if x < crossing:
                inside = not inside
    return inside


def main():
    snapshot = json.loads((ROOT / "inputs/snapshot.json").read_text())
    boundary = snapshot["boundary"]
    polygons = boundary["geometry"]["coordinates"]
    features = [boundary]
    totals = defaultdict(lambda: [0, 0, 0])
    seen = set()
    for row in snapshot["rows"]:
        x, y = float(row["centroid_1"]), float(row["centroid_l"])
        if not any(inside_ring(x, y, rings[0]) and
                   not any(inside_ring(x, y, hole) for hole in rings[1:])
                   for rings in polygons):
            continue
        key = row["ludb_id"]
        if key in seen:
            raise ValueError(f"중복 ID: {key}")
        seen.add(key)
        counts = totals[row["geography_type"]]
        counts[0] += 1
        if row.get("resunits") is None:
            counts[2] += 1
        else:
            units = int(row["resunits"])
            if units < 0:
                raise ValueError(f"음수 주택 수: {key}")
            counts[1] += units
        features.append({"type": "Feature", "properties": row,
                         "geometry": {"type": "Point", "coordinates": [x, y]}})
    if not seen:
        raise ValueError("경계 안의 레코드가 없습니다.")
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["geography_type", "records", "known_residential_units", "missing_unit_records"])
        for category, counts in sorted(totals.items()):
            writer.writerow([category, *counts])
    (output / "chinatown.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": features}), encoding="utf-8")
    print(f"완료: 차이나타운 경계 안 {len(seen)}건 → results/")


if __name__ == "__main__":
    main()
