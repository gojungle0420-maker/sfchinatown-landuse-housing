"""Compare full-tract SF Planning unit counts with ACS occupancy estimates."""
import csv
import gzip
import json
import io
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs"
RESULT = ROOT / "results"
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
    with gzip.open(INPUT / "city_landuse_20260817.csv.gz", "rt", newline="") as stream:
        inventory = list(csv.DictReader(stream))
    by_id = {r["ludb_id"]: r for r in inventory}
    if not inventory or len(by_id) != len(inventory):
        raise ValueError("Empty inventory or duplicate record IDs")
    tracts = json.loads((INPUT / "sf_tracts_2020.geojson").read_text())
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        db = folder / "join.gpkg"
        points = folder / "points.csv"
        with points.open("w", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["record_id", "x", "y"])
            for key, r in by_id.items():
                if not key or r["data_as_of"] != "2026-08-17T00:00:00.000" or int(r["resunits"]) < 0:
                    raise ValueError(f"Invalid inventory record: {key}")
                writer.writerow([key, float(r["centroid_1"]), float(r["centroid_l"])])
        subprocess.run([ogr, "-f", "GPKG", db, points, "-oo", "X_POSSIBLE_NAMES=x",
                        "-oo", "Y_POSSIBLE_NAMES=y", "-a_srs", "EPSG:4326", "-nln", "points"], check=True)
        subprocess.run([ogr, "-update", db, INPUT / "sf_tracts_2020.geojson",
                        "-nln", "tracts", "-nlt", "PROMOTE_TO_MULTI"], check=True)
        selected = ",".join(f"'{g}'" for g in GEOIDS)
        subprocess.run([ogr, "-update", db, f"/vsizip/{INPUT}/tl_2024_06_tract.zip",
                        "-where", f"GEOID IN ({selected})", "-select", "GEOID", "-t_srs",
                        "EPSG:4326", "-nln", "comparison", "-nlt", "PROMOTE_TO_MULTI"], check=True)

        def assignments(layer):
            sql = f"""SELECT p.record_id, t.GEOID FROM {layer} t
                      JOIN rtree_points_geom i ON i.maxx >= ST_MinX(t.geom)
                          AND i.minx <= ST_MaxX(t.geom) AND i.maxy >= ST_MinY(t.geom)
                          AND i.miny <= ST_MaxY(t.geom)
                      JOIN points p ON p.fid = i.id WHERE ST_Intersects(p.geom, t.geom)"""
            data = subprocess.check_output([ogr, "-f", "CSV", "/vsistdout/", db,
                                            "-dialect", "sqlite", "-sql", sql], text=True)
            lookup = {}
            for row in csv.DictReader(io.StringIO(data)):
                key = row["record_id"]
                if key in lookup:
                    raise ValueError(f"Multiple tract assignments in {layer}: {key}")
                lookup[key] = row["GEOID"]
            return lookup
        city = assignments("tracts")
        vintage_check = assignments("comparison")
    study = {key: g for key, g in city.items() if g in GEOIDS}
    if study != vintage_check:
        raise ValueError("2020 and 2024 study-tract assignments differ. Review boundary changes.")
    counts = Counter(study.values())
    units = Counter()
    for key, g in study.items():
        units[g] += int(by_id[key]["resunits"])
    print(f"City records {len(inventory):,}; assigned {len(city):,}; unmatched {len(inventory)-len(city):,}")
    crosswalk = RESULT / "city_landuse_tract_crosswalk.csv.gz"
    with crosswalk.with_suffix(".tmp").open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                writer.writerow(["ludb_id", "GEOID", "resunits"])
                for key in sorted(by_id):
                    writer.writerow([key, city.get(key, ""), by_id[key]["resunits"]])
    crosswalk.with_suffix(".tmp").replace(crosswalk)
    print(f"Study records {len(study):,}; 2020 and 2024 assignments match by record ID.")
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
                       int(r["B25002_M001"]), occupied, vacant, units[g]-total, units[g]-int(old[g]["tract_occupied_units_acs"])])
    target = RESULT / "tract_stock_validation.csv"
    with target.with_suffix(".tmp").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["GEOID","chinatown_resunits","full_tract_records","full_tract_resunits",
                         "geography_change_units","acs_total_units","acs_total_moe90","acs_occupied_units",
                         "acs_vacant_units","landuse_minus_acs_total","landuse_minus_acs_occupied"])
        writer.writerows(output)
    target.with_suffix(".tmp").replace(target)
    with target.open(newline="") as stream:
        metrics = {row["GEOID"]: row for row in csv.DictReader(stream)}
    polygons = []
    for feature in tracts["features"]:
        g = feature["properties"]["GEOID"]
        if g in metrics:
            feature["properties"].update({k: int(v) for k, v in metrics[g].items() if k != "GEOID"})
            polygons.append(feature)
    if len(polygons) != 6 or {p["properties"]["GEOID"] for p in polygons} != set(GEOIDS):
        raise ValueError("Six distinct study polygons required")
    map_path = RESULT / "tract_stock_validation.geojson"
    map_path.write_text(json.dumps({"type": "FeatureCollection", "features": polygons}) + "\n")



if __name__ == "__main__":
    main()
