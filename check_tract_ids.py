"""Compare San Francisco TIGER tract IDs to the project's ACS table."""
import csv
import struct
from pathlib import Path
from zipfile import ZipFile

root = Path.cwd()
with (root / "results/acs_tracts.csv").open(encoding="utf-8-sig", newline="") as stream:
    acs = [row["GEOID"] for row in csv.DictReader(stream)]

# The .dbf file stores one attribute row for each tract polygon in the ZIP.
with ZipFile(root / "inputs/tl_2024_06_tract.zip") as archive:
    table = archive.read("tl_2024_06_tract.dbf")

count, start, width = struct.unpack_from("<IHH", table, 4)
fields = {}
offset = 1  # Byte zero marks deleted records.
for pos in range(32, start, 32):
    if table[pos] == 13:
        break
    name = table[pos:pos + 11].split(b"\0")[0].decode("ascii")
    length = table[pos + 16]
    fields[name] = slice(offset, offset + length)
    offset += length

boundary = []
for i in range(count):
    pos = start + i * width
    row = table[pos:pos + width]
    if row[:1] == b" " and row[fields["COUNTYFP"]] == b"075":
        boundary.append(row[fields["GEOID"]].decode("ascii").strip())

print(f"ACS 표 {len(acs)}개 | 샌프란시스코 경계 {len(boundary)}개")
if not acs or len(set(acs)) != len(acs) or len(set(boundary)) != len(boundary):
    raise SystemExit("빈 표 또는 중복 지역 번호를 확인하세요.")
if set(acs) != set(boundary):
    raise SystemExit(f"ACS에만 있음 {sorted(set(acs)-set(boundary))}, 경계에만 있음 {sorted(set(boundary)-set(acs))}")
print(f"지역 번호 {len(acs)}개 모두 일치")
