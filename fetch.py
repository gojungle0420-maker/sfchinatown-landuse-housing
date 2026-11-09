"""Download the Chinatown boundary and candidate land-use records."""
import json
from pathlib import Path
from urllib.parse import urlencode
import subprocess

BASE = "https://data.sfgov.org/resource/"
INPUT = Path(__file__).resolve().parent / "inputs"


def read_api(resource, **params):
    url = BASE + resource + "?" + urlencode(params)
    data = subprocess.check_output(["curl", "-fsSL", "--max-time", "90", url])
    return json.loads(data)


def main():
    boundary = read_api("j2bu-swwd.geojson", nhood="Chinatown")
    feature, = boundary["features"]
    geometry = feature["geometry"]
    assert geometry["type"] == "MultiPolygon"
    vertices = [point for poly in geometry["coordinates"] for point in poly[0]]
    xs, ys = zip(*vertices)
    where = (f"centroid_1 between {min(xs)} and {max(xs)} AND "
             f"centroid_l between {min(ys)} and {max(ys)}")
    fields = "ludb_id,centroid_l,centroid_1,resunits,residentia,geography_type,data_as_of"
    rows = read_api("c5ge-t6pj.json", **{"$select": fields, "$where": where,
                    "$order": "ludb_id", "$limit": 50000})
    if not rows or len(rows) >= 50000:
        raise ValueError("조회 범위와 다운로드 한도를 확인하세요.")
    INPUT.mkdir(exist_ok=True)
    target = INPUT / "snapshot.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(dict(boundary=feature, rows=rows)), encoding="utf-8")
    temporary.replace(target)
    print(f"후보 레코드 {len(rows)}건 저장")


if __name__ == "__main__":
    main()
