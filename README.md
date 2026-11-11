# Housing density and zoning in San Francisco’s Chinatown

## A. SUMMARY

This dataset links San Francisco’s August 17, 2026 land-use inventory to parcel boundaries, zoning districts and Census tracts. It measures where housing is concentrated in Chinatown and uses the 2020–2024 American Community Survey (ACS) to describe renter occupancy across six tracts.

The inventory contains **5,873 housing units in 1,000 land-use records**. The parcel map covers 999 single-parcel records with 5,864 units. One record in tract 611.01 groups several parcels and accounts for the remaining nine units. [Parcel map data](results/chinatown_parcels.geojson) · [Tract summary](results/tract_summary.csv)

## B. HOW THE DATASET IS CREATED

| Stage | Method | Validation |
|---|---|---|
| **Stage 1. Define Chinatown** | Retrieve the city’s Chinatown Analysis Neighborhood polygon and land-use records in its bounding box. Keep records whose published centroid falls inside the polygon. | 1,000 of 2,168 candidate records fall inside the boundary. |
| **Stage 2. Assign Census tracts** | Intersect each centroid with 2024 TIGER/Line tract polygons. Join ACS estimates by the 11-digit tract GEOID. | Each point matches one tract. The six GEOIDs match the city’s Chinatown crosswalk. |
| **Stage 3. Build the parcel map** | Join single-parcel records to active city parcel boundaries by mapped parcel ID. Retain the zoning code and district name. | All 999 records match. Count the grouped nine-unit record once in the tract table. |
| **Stage 4. Calculate density and tenure** | Divide each zoning category’s total units by its mapped parcel area in hectares, measured in California Albers (EPSG:3310). Divide renter-occupied units by occupied units for each tract. | Report 17 zoning categories. Check full-tract housing totals against ACS occupancy table B25002. |

[Source data, study-area definition and zoning codebook](docs/data-guide.md) · [Field-level sources and housing-stock validation](docs/housing-stock-validation.md)

## C. UPDATE PROCESS

SF Planning updates its public land-use inventory quarterly. This repository contains a dated snapshot. To reproduce the published results, use the committed inputs and parcel layer. [SF Planning inventory and update schedule](https://data.sfgov.org/d/c5ge-t6pj)

To refresh the land-use inputs, run `python3 fetch.py` before Stage 1. This replaces `inputs/snapshot.json`. After the tract and ACS joins, run `match_parcel_ids.py`, `build_parcel_map.py` and `zoning_density.py` in that order. Live downloads require internet access and curl. The ACS estimates and full-tract validation use separate, dated inputs.

## D. HOW TO USE THIS DATASET

### Compare housing by zoning district

The five categories below contain the most recorded housing units. CRNC has the largest stock. RM-4 has **1.84 times** the housing density of CRNC. Removing the three RM-4 parcels with the most units reduces its density to 327.2 units/ha, or 1.55 times the CRNC density. [All 17 categories](results/zoning_summary.csv)

| District | Parcels | Housing units | Hectares | Units/ha |
|---|---:|---:|---:|---:|
| CRNC | 233 | 1,485 | 7.023 | 211.5 |
| RM-4 | 36 | 1,120 | 2.883 | 388.5 |
| CCB | 139 | 785 | 4.032 | 194.7 |
| NCD | 130 | 662 | 4.411 | 150.1 |
| RM-2 | 126 | 559 | 3.094 | 180.7 |

![Chinatown parcels colored by zoning district, with a legend for all 17 categories](results/chinatown-zoning.svg)

### Interpret tract estimates

Across the six tracts, the ACS estimates 5,684 renter households among 6,258 occupied housing units (**90.83%**). Each map color describes a whole tract. Sampling uncertainty varies by tract. For example, tract 107.02 has an estimated renter share of 80.45% with an approximate 90% margin of error of ±19.77 percentage points.

![Renter share among occupied housing units in the six study tracts](results/chinatown-renter-share.svg)

### Limits and join checks

- **Parcel joins.** Grouped records can match several parcels. Assigning the full unit count to each parcel would duplicate housing units. Preserve the land-use record ID and check match counts before aggregating.
- **Boundary and density.** Centroid inclusion assigns each selected parcel’s full area to the study. Density describes housing on those parcels under their recorded zoning. Estimating the effect of rezoning requires historical zoning and development records.
- **Housing totals.** The 2026 city inventory records 5,873 units even when aggregated over the six full tracts. The 2020–2024 ACS estimates 7,491 total units, including 1,233 vacant units. The sources differ in timing and collection method. The gap alone cannot identify missing units. [Comparison by tract](results/tract_stock_validation.csv)

### Reproduce the published outputs

Run from the repository root with Python 3 and GDAL’s `ogr2ogr` on your path, or QGIS installed in its default macOS location.

```bash
python3 analyze.py
python3 prepare_acs.py
python3 check_tract_ids.py
python3 join_tracts.py
python3 join_acs.py
python3 zoning_density.py
python3 tract_margins.py
python3 rm4_sensitivity.py
python3 validate_housing_stock.py
```
To inspect the styled layers, open either QGIS project from a full checkout. [Verified revision](https://github.com/gojungle0420-maker/sfchinatown-landuse-housing/commit/13663ae) · [Zoning project](chinatown_zoning.qgz) · [Tenure project](chinatown_renter_share.qgz)

## E. LICENSE

The project code and accompanying documentation use the MIT License. Retain the copyright and permission notices when redistributing them. Source datasets are distributed under their respective providers’ terms. [MIT License](LICENSE) · [Data sources and attribution](docs/data-guide.md)
