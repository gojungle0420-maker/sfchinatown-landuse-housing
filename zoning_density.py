"""Housing units per hectare of mapped single-parcel land, by zoning code."""
import csv
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ogr = shutil.which("ogr2ogr") or "/Applications/QGIS.app/Contents/MacOS/ogr2ogr"
if ogr.startswith("/Applications/QGIS.app/"):
    resources = Path(ogr).parents[1] / "Resources/qgis"
    os.environ["GDAL_DATA"] = str(resources / "gdal")
    os.environ["PROJ_DATA"] = str(resources / "proj")
source = Path("results/chinatown_parcels.geojson")
with tempfile.TemporaryDirectory() as folder:
    db = Path(folder) / "parcels.gpkg"
    subprocess.run([ogr, "-f", "GPKG", db, source, "-t_srs", "EPSG:3310",
                    "-nln", "parcels", "-nlt", "PROMOTE_TO_MULTI"], check=True)
    sql = """SELECT zoning_code, count(*) AS parcels, sum(CAST(resunits AS INTEGER)) AS units,
                    sum(ST_Area(geom))/10000.0 AS hectares
             FROM parcels GROUP BY zoning_code ORDER BY zoning_code"""
    data = subprocess.check_output([ogr, "-f", "CSV", "/vsistdout/", db,
                                    "-dialect", "sqlite", "-sql", sql], text=True)
rows = sorted(csv.DictReader(io.StringIO(data)), key=lambda r: (-int(r["units"]), r["zoning_code"]))
summary = []
for row in rows:
    area = float(row["hectares"])
    units = int(row["units"])
    print(f"{row['zoning_code']:12} | {row['parcels']:>3}필지 | {area:6.2f} ha | {units/area:6.1f}호/ha")
    summary.append([row["zoning_code"], row["parcels"], units, f"{area:.3f}", f"{units/area:.1f}"])

target = source.with_name("zoning_summary.csv")
with target.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["zoning_code", "parcel_count", "housing_units", "parcel_area_ha", "units_per_ha"])
    writer.writerows(summary)
print(f"저장 완료: {target} ({len(summary)}개 용도지역)")
