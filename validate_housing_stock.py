"""Compare full-tract SF Planning unit counts with ACS occupancy estimates."""
import csv
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs"
RESULT = ROOT / "results"
# Outward-rounded envelope covering the six full TIGER polygons, with padding.
WEST, EAST, SOUTH, NORTH = -122.414, -122.399, 37.791, 37.804
GEOIDS = ("06075010701", "06075010702", "06075011300",
          "06075011800", "06075061101", "06075061102")


def indexed_csv(path, column):
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    index = {r[column]: r for r in rows}
    if len(index) != len(rows):
        raise ValueError(f"Duplicate key in {path.name}")
    return index


def main():
    ogr = shutil.which("ogr2ogr") or "/Applications/QGIS.app/Contents/MacOS/ogr2ogr"
    if ogr.startswith("/Applications/QGIS.app/"):
        resources = Path(ogr).parents[1] / "Resources/qgis"
        os.environ.update(GDAL_DATA=str(resources / "gdal"), PROJ_DATA=str(resources / "proj"))
    candidates = indexed_csv(INPUT / "full_tract_candidates.csv", "ludb_id")
    features = []
    for key, r in candidates.items():
        if not key or r["data_as_of"] != "2026-08-17T00:00:00.000" or int(r["resunits"]) < 0:
            raise ValueError(f"Invalid inventory record: {key}")
        point = [float(r["centroid_1"]), float(r["centroid_l"])]
        features.append(dict(type="Feature", properties={"record_id": key},
                             geometry=dict(type="Point", coordinates=point)))
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        db = folder / "join.gpkg"
        selected = ",".join(f"'{g}'" for g in GEOIDS)
        subprocess.run([ogr, "-f", "GPKG", db, f"/vsizip/{INPUT}/tl_2024_06_tract.zip",
                        "-where", f"GEOID IN ({selected})", "-select", "GEOID", "-t_srs",
                        "EPSG:4326", "-nln", "tracts", "-nlt", "PROMOTE_TO_MULTI"], check=True)
        sql = "SELECT GEOID, ST_MinX(geom) AS w, ST_MaxX(geom) AS e, ST_MinY(geom) AS s, ST_MaxY(geom) AS n FROM tracts"
        def query(sql):
            data = subprocess.check_output([ogr, "-f", "CSV", "/vsistdout/", db,
                                           "-dialect", "sqlite", "-sql", sql], text=True)
            return list(csv.DictReader(data.splitlines()))
        bounds = query(sql)
        if {r["GEOID"] for r in bounds} != set(GEOIDS) or any(
            float(r["w"]) < WEST or float(r["e"]) > EAST or float(r["s"]) < SOUTH
            or float(r["n"]) > NORTH for r in bounds
        ):
            raise ValueError("Candidate query does not cover the full study tracts.")
        points = folder / "points.geojson"
        points.write_text(json.dumps(dict(type="FeatureCollection", features=features)))
        subprocess.run([ogr, "-update", db, points, "-nln", "points"], check=True)
        matches = query("SELECT p.record_id, t.GEOID FROM points p JOIN tracts t ON ST_Intersects(p.geom,t.geom)")
    counts, units = Counter(), Counter()
    seen = set()
    for row in matches:
        key, tract = row["record_id"], row["GEOID"]
        if key in seen:
            raise ValueError(f"Multiple tract assignments: {key}")
        seen.add(key)
        counts[tract] += 1
        units[tract] += int(candidates[key]["resunits"])
    old = indexed_csv(RESULT / "tract_summary.csv", "GEOID")
    acs = indexed_csv(INPUT / "acs2024_b25002_six_tracts.csv", "GEO_ID")
    if set(old) != set(GEOIDS) or set(acs) != {"1400000US"+g for g in GEOIDS}:
        raise ValueError("Missing or unexpected tract.")
    output = []
    for g in GEOIDS:
        r = acs["1400000US"+g]
        total, occupied, vacant = [int(r[f"B25002_E00{i}"]) for i in (1, 2, 3)]
        if min(occupied, vacant) < 0 or occupied + vacant != total or occupied != int(old[g]["tract_occupied_units_acs"]):
            raise ValueError(f"ACS consistency check failed: {g}")
        neighborhood = int(old[g]["chinatown_resunits"])
        output.append([g, neighborhood, counts[g], units[g], units[g]-neighborhood, total,
                       int(r["B25002_M001"]), occupied, vacant, units[g]-total])
    target = RESULT / "tract_stock_validation.csv"
    with target.with_suffix(".tmp").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["GEOID","chinatown_resunits","full_tract_records","full_tract_resunits",
                         "geography_change_units","acs_total_units","acs_total_moe90","acs_occupied_units",
                         "acs_vacant_units","landuse_minus_acs_total"])
        writer.writerows(output)
    target.with_suffix(".tmp").replace(target)


if __name__ == "__main__":
    main()
