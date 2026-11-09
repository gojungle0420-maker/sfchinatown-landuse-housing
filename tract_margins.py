"""Calculate approximate ACS renter-share margins for the six study tracts."""
import csv
from math import sqrt
from pathlib import Path

root = Path.cwd()
source, = (root / "inputs").glob("*B25003*.csv")
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.reader(stream)
    headers = next(reader)
    rows = {row[0].strip(): row for row in reader}

def number(label, index):
    return int(rows[label][index].replace("±", "").replace(",", ""))

with (root / "results/tract_summary.csv").open(newline="") as stream:
    study = list(csv.DictReader(stream))

print("Tract 번호 | 임차 비율 | 90% 오차범위(근사)")
for row in study:
    code = row["GEOID"]
    whole, fraction = str(int(code[5:9])), code[9:]
    name = whole if fraction == "00" else f"{whole}.{fraction}"
    prefix = f"Census Tract {name}; San Francisco County; California!!"
    index = headers.index(prefix + "Margin of Error")
    total = int(row["tract_occupied_units_acs"])
    renters = int(row["tract_renter_occupied_acs"])
    share = renters / total
    a = number("Renter occupied", index)
    b = number("Total:", index)
    term = a**2 - (share*b)**2
    if share == 1:
        moe = a / total
    elif term < 0:
        moe = sqrt(a**2 + (share*b)**2) / total
    else:
        moe = sqrt(term) / total
    print(f"{name:>6} | {100*share:.2f}% | ±{100*moe:.2f}%p")
