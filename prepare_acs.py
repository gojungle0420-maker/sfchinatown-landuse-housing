"""Convert the downloaded 2024 ACS B25003 table to one row per SF tract."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source, = (ROOT / "inputs").glob("ACSDT5Y2024.B25003-*.csv")
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.reader(stream)
    headers = next(reader)
    rows = {row[0].strip(): row for row in reader}

records = {}
for index, header in enumerate(headers):
    if not header.endswith("!!Estimate"):
        continue
    match = re.fullmatch(r"Census Tract (\d{1,4})(?:\.(\d{1,2}))?; San Francisco County; California!!Estimate", header)
    if not match:
        raise ValueError(f"예상과 다른 지역 이름: {header}")
    whole, fraction = match.groups()
    geoid = "06075" + whole.zfill(4) + (fraction or "").ljust(2, "0")
    total, owners, renters = [
        int(rows[label][index].replace(",", ""))
        for label in ("Total:", "Owner occupied", "Renter occupied")
    ]
    if geoid in records or owners + renters != total:
        raise ValueError(f"지역 번호 또는 가구 합계를 확인하세요: {geoid}")
    share = round(100 * renters / total, 2) if total else ""
    records[geoid] = [geoid, total, owners, renters, share]

if not records:
    raise ValueError("tract 열을 찾지 못했습니다.")
target = ROOT / "results" / "acs_tracts.csv"
target.parent.mkdir(exist_ok=True)
with target.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["GEOID", "occupied_units", "owner_occupied", "renter_occupied", "renter_pct"])
    writer.writerows(records.values())
print(f"완료: {len(records)}개 tract → results/acs_tracts.csv")
