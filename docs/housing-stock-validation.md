# Comparing housing stock across sources

## Where each original column comes from

The historical commit contains the original table. The six columns below retain their original meaning. [Original tract summary at c643f78](https://github.com/gojungle0420-maker/sfchinatown-landuse-housing/blob/c643f7874c1a2197108fa8045ce323081c003f6c/results/tract_summary.csv) · [Comparison by tract](../results/tract_stock_validation.csv).

| Original field | Source field or calculation | Geographic support and interpretation |
|---|---|---|
| GEOID | [2024 TIGER/Line tract polygons](https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_06_tract.zip), GEOID | 11-character tract identifier assigned to each city's land-use point by spatial intersection. |
| chinatown_landuse_records | Count of distinct ludb_id from [SF Planning Land Use](https://data.sfgov.org/d/c5ge-t6pj) | Land-use records with centroids inside the [Chinatown Analysis Neighborhood](https://data.sfgov.org/d/j2bu-swwd), grouped by tract. One record can cover multiple parcels. |
| chinatown_resunits | Sum of resunits from [SF Planning Land Use](https://data.sfgov.org/d/c5ge-t6pj) | Recorded units across those selected records, including the nine units on the grouped record. Snapshot dated August 17, 2026. |
| tract_occupied_units_acs | [ACS B25003_001E](https://api.census.gov/data/2024/acs/acs5/groups/B25003.html) | Estimated occupied housing units in the entire tract, 2020–2024. |
| tract_renter_occupied_acs | [ACS B25003_003E](https://api.census.gov/data/2024/acs/acs5/groups/B25003.html) | Estimated renter-occupied housing units in the entire tract, 2020–2024. |
| tract_renter_pct_2020_2024 | 100 × B25003_003E / B25003_001E, rounded to two decimals | Renter share among occupied units. Vacant units are outside the tenure denominator. |

## Independent geography and occupancy checks

Run `python3 validate_housing_stock.py` from the repository root using the same GDAL installation as the spatial join. The script rebuilds the comparison offline using two saved extracts.

1. **Select all six full tract polygons first.** Use the six GEOIDs independently verified against the city's [2020 neighborhood crosswalk](https://data.sfgov.org/d/sevw-6tgi). In EPSG:4326, check every polygon's bounds against the candidate envelope. Independently query SF Planning for centroids with longitude between −122.414 and −122.399 and latitude between 37.791 and 37.804. The endpoint returned 2,963 rows, matching a separate count query. Save the IDs, coordinates, unit counts and source dates. [Saved DataSF extract](../inputs/full_tract_candidates.csv).
2. **Assign centroids directly to tracts.** Intersect every candidate with the six full TIGER polygons without applying a neighborhood filter. Count a grouped land-use record once. Reject repeated IDs, ambiguous tract assignments, missing unit counts, negative counts or unexpected snapshot dates. Records without usable coordinates cannot enter this geographic comparison.
3. **Align the ACS measure.** Extract the six tract rows from the Census Bureau's 2020–2024 occupancy-status summary file. The last six ACS source columns contain estimates and published 90% margins of error for total, occupied and vacant units. Verify total = occupied + vacant in every tract, and verify the occupied estimate equals the original B25003 denominator. [Official B25002 download](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b25002.dat) · [Saved six-row extract](../inputs/acs2024_b25002_six_tracts.csv) · [B25002 variable definitions](https://api.census.gov/data/2024/acs/acs5/groups/B25002.html).

| Tract | Neighborhood units | Full-tract land-use units | ACS total ± 90% MOE | ACS occupied | ACS vacant | Land use minus ACS total |
|---|---:|---:|---:|---:|---:|---:|
| 107.01 | 1,296 | 1,296 | 2,064 ± 250 | 1,792 | 272 | −768 |
| 107.02 | 842 | 842 | 793 ± 107 | 660 | 133 | +49 |
| 113.00 | 1,826 | 1,826 | 1,587 ± 120 | 1,362 | 225 | +239 |
| 118.00 | 571 | 571 | 801 ± 86 | 654 | 147 | −230 |
| 611.01 | 738 | 738 | 1,151 ± 170 | 862 | 289 | −413 |
| 611.02 | 600 | 600 | 1,095 ± 103 | 928 | 167 | −495 |
| **Six tracts** | **5,873** | **5,873** | **7,491** | **6,258** | **1,233** | **−1,618** |

The geography change adds zero units in each tract under the published centroid rule. Using all housing units expands the ACS comparator by 1,233. The signed aggregate difference changes from −385 against occupied units to −1,618 against all units. Differences run in both directions across tracts.

SF Planning describes an administrative inventory built from an assessor baseline, supplemental research, completed projects and parcel changes. ACS estimates housing status over a five-year survey period and publishes sampling margins. The total-unit margin shown above applies only to the ACS estimate. Source coverage, unit classification and changes between reference periods are possible contributors. These comparisons establish neither an exact cause nor a count of missing homes. A follow-up audit could start in tract 107.01, request an inventory aligned to 2024, and reconcile large buildings and grouped records against independent address or completion records. [SF Planning source methodology](https://data.sfgov.org/d/c5ge-t6pj).
