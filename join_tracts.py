"""Assign exactly one Census tract to each land-use point using GDAL."""
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

root = Path.cwd()
ogr = shutil.which("ogr2ogr") or "/Applications/QGIS.app/Contents/MacOS/ogr2ogr"
if ogr.startswith("/Applications/QGIS.app/"):
    resources = Path(ogr).parents[1] / "Resources/qgis"
    os.environ["GDAL_DATA"] = str(resources / "gdal")
    os.environ["PROJ_DATA"] = str(resources / "proj")
results = root / "results"
features = json.loads((results / "chinatown.geojson").read_text())["features"]
points = [f for f in features if f["geometry"]["type"] == "Point"]
archive = root / "inputs/tl_2024_06_tract.zip"
with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    db = folder / "analysis.gpkg"
    subprocess.run([ogr, "-f", "GPKG", db, f"/vsizip/{archive}", "-nln", "tracts",
                    "-nlt", "MULTIPOLYGON", "-where", "COUNTYFP = '075'", "-select", "GEOID",
                    "-t_srs", "EPSG:4326"], check=True)
    source = folder / "points.geojson"
    source.write_text(json.dumps({"type": "FeatureCollection", "features": points}))
    subprocess.run([ogr, "-update", db, source, "-nln", "points"], check=True)
    sql = ("SELECT p.ludb_id, t.GEOID FROM points p LEFT JOIN tracts t "
           "ON ST_Intersects(p.geom, t.geom)")
    subprocess.run([ogr, "-update", db, db, "-dialect", "sqlite", "-sql", sql,
                    "-nln", "matches", "-nlt", "NONE"], check=True)
    with sqlite3.connect(db) as conn:
        matches = list(conn.execute("SELECT ludb_id, GEOID FROM matches"))

lookup = dict(matches)
if (not points or len(matches) != len(points) or len(lookup) != len(points)
        or any(not geoid for geoid in lookup.values())):
    raise SystemExit("누락 또는 중복 연결이 있습니다. 경계에 놓인 점을 확인하세요.")
for point in points:
    props = point["properties"]
    props["GEOID"] = lookup[props["ludb_id"]]
target = results / "landuse_points_with_tract.geojson"
temp = target.with_suffix(".tmp")
temp.write_text(json.dumps({"type": "FeatureCollection", "features": points}))
temp.replace(target)
print(f"중심점 {len(points):,}개 → tract {len(set(lookup.values()))}개")
print(f"주택 수 합계 {sum(int(f['properties']['resunits']) for f in points):,}호")
