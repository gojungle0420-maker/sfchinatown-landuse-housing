# Data sources, geography and interpretation

## Why these six tracts?

The study uses San Francisco’s **Analysis Neighborhoods** definition of Chinatown. The city constructed those reporting areas by grouping 2010 Census tracts. That choice gives the study a documented boundary that another researcher can apply. Other definitions of Chinatown may cover a different area. [City boundary and methodology](https://data.sfgov.org/d/j2bu-swwd).

The pipeline selects land-use records by their published centroid, then assigns the selected points to 2024 TIGER/Line tract polygons. An independent check uses the city’s 2020 census tract assignments. Filtering that table to Chinatown returns exactly the six GEOIDs below. The two methods agree on tract membership. A point near the neighborhood edge determines inclusion of its entire record and, for single parcels, its full mapped area. [City crosswalk](https://data.sfgov.org/d/sevw-6tgi) · [Filtered source rows](https://data.sfgov.org/resource/sevw-6tgi.csv?neighborhoods_analysis_boundaries=Chinatown&%24select=name%2Cgeoid%2Cneighborhoods_analysis_boundaries&%24order=geoid).

| Tract | GEOID | Included land-use records | Recorded housing units |
|---|---|---:|---:|
| 107.01 | 06075010701 | 177 | 1,296 |
| 107.02 | 06075010702 | 185 | 842 |
| 113.00 | 06075011300 | 202 | 1,826 |
| 118.00 | 06075011800 | 103 | 571 |
| 611.01 | 06075061101 | 242 | 738 |
| 611.02 | 06075061102 | 91 | 600 |
| Total | | 1,000 | 5,873 |

## Sources and measures

| Source | Unit, vintage and use |
|---|---|
| [SF Planning land use](https://data.sfgov.org/d/c5ge-t6pj) | The saved records carry an August 17, 2026 reference date. `ludb_id` identifies a record, `geography_type` distinguishes single- and multi-parcel observations, and `resunits` counts recorded housing units. The analysis uses the housing portion of the land-use inventory. |
| [DataSF parcel boundaries](https://data.sfgov.org/d/acdm-wktn) | Active parcel geometry, `mapblklot` mapped parcel ID, `zoning_code`, and `zoning_district`. The output retains the parcel reference date in `parcel_data_as_of`. A mapped parcel ID can represent condominium lots sharing a footprint. The script checks for conflicting geometries or zoning before accepting a match. |
| [2024 TIGER/Line tracts](https://www2.census.gov/geo/tiger/TIGER2024/TRACT/) | California tract polygons filtered to San Francisco County. The join preserves leading zeros in the 11-character GEOID. ACS and TIGER/Line supplied the same 244 county tract IDs. |
| [2020–2024 ACS five-year table B25003](https://api.census.gov/data/2024/acs/acs5/groups/B25003.html) | Tenure of occupied housing units. Divide renter-occupied units (B25003_003E) by total occupied units (B25003_001E). The six-tract share uses summed counts. Calculate approximate 90% margins using the corresponding M fields and the Census proportion formula. [Census guidance](https://www2.census.gov/programs-surveys/acs/tech_docs/statistical_testing/2024_Instructions_for_Stat_Testing_ACS.pdf). |

**What the denominators measure.** The tract summary counts 5,873 recorded housing units. The map covers 5,864 of them on 999 single-parcel records. The remaining nine units belong to one grouped record in tract 611.01, where assigning them to individual parcels would require additional evidence. Parcel density uses the full area of the matched parcels, including parcels with zero units. Streets and other land outside those polygons contribute no area. ACS counts occupied units over a different reference period. Subtracting these two sources would not yield a vacancy estimate.

## Zoning codebook

These are the 17 values present in the released parcel layer. The names below follow its district-name field, with capitalization standardized. They describe the recorded planning designation. Existing unit counts come independently from the land-use inventory. Compound codes retain their own group so every parcel and its area enter the zoning totals once. [City parcel source](https://data.sfgov.org/d/acdm-wktn) · [City zoning districts](https://data.sfgov.org/d/3i4a-hu95) · [Observed counts by code](../results/zoning_summary.csv).

| Recorded code | District name or interpretation |
|---|---|
| CRNC | Chinatown Residential Neighborhood Commercial |
| CCB | Chinatown Community Business |
| CVR | Chinatown Visitor Retail |
| CRNC&#124;CVR | Both CRNC and CVR appear on the parcel record |
| CRNC&#124;RM-4 | Both CRNC and RM-4 appear on the parcel record |
| NCD | Neighborhood Commercial District. This dataset contains two named districts under this code, Broadway and North Beach. |
| RM-1 | Residential, Mixed, Low Density |
| RM-2 | Residential, Mixed, Moderate Density |
| RM-3 | Residential, Mixed, Medium Density |
| RM-4 | Residential, Mixed, High Density |
| RC-3 | Residential, Commercial, Medium Density |
| RC-4 | Residential, Commercial, High Density |
| RH-3 | Residential, House, Three-Family |
| C-2 | Community Business |
| C-3-G | Downtown, General |
| C-3-O | Downtown, Office |
| P | Public |

## Research extensions

1. **Freeze the parcel inputs.** Archive the exact API responses used for the parcel join with retrieval dates, queries and checksums. A subsequent release could then distinguish changes to city data from changes to the code.
2. **Measure boundary sensitivity.** Compare centroid inclusion with parcel–neighborhood polygon overlap in EPSG:3310. Report how many parcels cross the boundary, their units, and how district density rankings change under a majority-area rule.
3. **Distinguish existing stock from new production.** Link dated zoning histories and housing completions to stable parcel identifiers. Document lot splits and mergers, then compare additions over common time windows. The present cross-section measures observed stock under recorded designations.

## Housing-stock validation

For the source of every column in the original tract summary, a full-tract centroid aggregation and the comparison with ACS total, occupied and vacant units, see the [housing-stock validation](housing-stock-validation.md).
