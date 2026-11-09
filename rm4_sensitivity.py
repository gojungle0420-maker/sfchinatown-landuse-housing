"""Compare RM-4 density with and without the three parcels with the most housing units."""
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
    sql = """SELECT mapblklot, CAST(resunits AS INTEGER) AS units,
                    ST_Area(geom)/10000.0 AS hectares
             FROM parcels WHERE zoning_code = 'RM-4'
             ORDER BY units DESC, mapblklot"""
    data = subprocess.check_output([ogr, "-f", "CSV", "/vsistdout/", db,
                                    "-dialect", "sqlite", "-sql", sql], text=True)
rows = list(csv.DictReader(io.StringIO(data)))
for label, sample in [("RM-4 전체", rows), ("상위 3개 제외", rows[3:])]:
    area = sum(float(r["hectares"]) for r in sample)
    units = sum(int(r["units"]) for r in sample)
    print(f"{label}: {len(sample)}필지 | {units:,}호 | {area:.3f} ha | {units/area:.1f}호/ha")
