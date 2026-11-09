# sfchinatown-landuse-housing
A Python-based geospatial data pipeline integrating parcel, land use, zoning, and Census data to analyze housing conditions in San Francisco's Chinatown.


샌프란시스코시 토지이용 자료에서 중심점이 차이나타운 분석 경계 안에 있는 레코드를 골라, 지리 단위별 주택 수를 집계합니다.

![샌프란시스코 차이나타운 필지 999개의 용도지역별 색상 지도와 범례](results/chinatown-zoning.svg)

[개별 필지의 주택 수와 용도지역 살펴보기](results/chinatown_parcels.geojson)
### RM-4 주택의 절반 가까이가 3개 필지에 분포합니다

지도에 포함된 차이나타운 단일 필지 999개 중 RM-4는 36개(3.6%)이며, 이곳에 전체 5,864호의 19.1%인 1,120호가 기록돼 있습니다. RM-4 안에서도 주택 분포는 고르지 않습니다. 주택 수가 가장 많은 3개 필지에 508호(45.4%)가 모여 있으며, 필지당 평균은 31.1호, 중앙값은 13.5호입니다.
2020–2024년 ACS 추정치 기준, 분석 대상 6개 tract 전체 거주 가구의 90.83%가 임차가구였다

### Tract 113.00에서는 RM-4 필지에 가장 많은 주택이 기록됐습니다

샌프란시스코 차이나타운 분석 경계에 중심점이 포함된 tract 113.00의 단일 필지 202개에는 주택 1,826호가 기록돼 있습니다. RM-4는 28필지로 분석 대상 필지의 13.9%를 차지하며, 이곳에 주택 628호(34.4%)가 모여 있습니다. 필지 수가 가장 많은 CRNC는 77필지에 440호입니다. 필지당 평균 주택 수는 RM-4에서 22.4호, CRNC에서 5.7호입니다.

필지 지도(5,864호)와 tract 요약표(5,873호)의 차이는 모두 tract 611.01에서 발생합니다. 이 구역의 여러 필지를 묶은 기록 1건(9호)은 tract 합계에 포함했으며, 개별 필지별 배분을 알 수 없어 단일 필지 지도에서는 제외했습니다.

### 차이나타운 분석 대상 6개 tract의 임차가구 비율

![차이나타운 분석 대상 6개 Census tract의 임차가구 비율을 보여주는 지도와 파란색 범례](results/chinatown-renter-share.svg)

2020–2024년 ACS 추정치 기준, 6개 tract의 임차가구 비율은 80.45%에서 98.62%까지 분포합니다. 각 색은 해당 tract 전체의 거주 가구 중 임차가구가 차지하는 비율을 나타냅니다.


## 첫 실행

Python 3이 있는 환경에서 이 폴더를 열고 아래 명령을 실행하세요. 추가 패키지나 API 키는 필요 없습니다.

    python3 analyze.py

inputs/snapshot.json에 포함된 고정 입력을 읽습니다. results/summary.csv는 지리 단위별 레코드 수, 값이 알려진 주택 수의 합계, 주택 수 누락 건수를 담습니다. results/chinatown.geojson에는 분석 경계와 선택한 중심점이 있습니다.

## 자료와 방법

- [SF Planning 토지이용 자료](https://data.sfgov.org/d/c5ge-t6pj)의 원본 ID(ludb_id), 중심점 경위도, 주택 수(resunits), 지리 단위(geography_type)를 사용합니다. 입력 자료의 기준일은 2026-08-17입니다.
- [DataSF Analysis Neighborhoods](https://data.sfgov.org/d/j2bu-swwd)의 nhood가 Chinatown인 다각형을 사용합니다. fetch.py는 경계의 외접 사각형 안에 중심점이 있는 후보를 내려받습니다. analyze.py는 다각형 내부 검사를 한 번 더 수행합니다. 중심점이 없는 레코드는 조회에서 제외됩니다. 경계에 걸친 필지는 면적 비례로 나누지 않습니다.
- 검증 결과는 후보 2,168건 중 내부 1,000건입니다. 단일 필지 999건에 5,864호, 여러 필지를 묶은 레코드 1건에 9호가 기록됐습니다. 합계는 원자료에 기록된 주택 수이며, 입주 가구 수나 임차 가구 수를 측정하지 않습니다.
- 새로운 공개 자료로 갱신하려면 인터넷과 curl이 있는 환경에서 python3 fetch.py 다음에 python3 analyze.py를 실행합니다. 입력 파일이 교체되므로 기존 결과를 재현하려면 먼저 현재 버전을 Git에 커밋하세요.

## 용도지역 지도 열기

저장소 전체를 내려받은 뒤 QGIS에서 `chinatown_zoning.qgz`를 엽니다. 지도는 `results/chinatown_parcels.geojson`을 상대 경로로 읽습니다. 색은 용도지역 코드입니다. 필지를 클릭하면 해당 필지의 주택 수와 그 필지가 속한 tract 전체의 ACS 임차가구 비율을 확인할 수 있습니다.

## Census와 토지이용 연결하기

프로젝트 최상위 폴더에서 아래 순서로 실행합니다. Python 3과 GDAL의 ogr2ogr가 필요합니다. macOS에서는 기본 위치에 설치한 QGIS의 ogr2ogr도 사용할 수 있습니다.

~~~bash
python3 analyze.py
python3 prepare_acs.py
python3 check_tract_ids.py
python3 join_tracts.py
python3 join_acs.py
python3 match_parcel_ids.py
python3 build_parcel_map.py
~~~

처음 다섯 명령은 저장소에 포함된 입력을 사용합니다. 마지막 두 명령은 인터넷과 curl을 사용해 DataSF에서 필지 번호, 활성 경계, 용도지역을 조회합니다. 시 자료가 갱신되면 새로 만든 지도는 저장된 지도와 달라질 수 있습니다. [DataSF 필지와 용도지역](https://data.sfgov.org/d/acdm-wktn)

2024 TIGER/Line 경계와 2020–2024 ACS 표 B25003을 11자리 GEOID로 연결합니다. 샌프란시스코의 tract 번호 244개가 일치했고, 차이나타운의 토지이용 중심점은 그중 6개 tract에 분포합니다. [TIGER/Line 경계](https://www2.census.gov/geo/tiger/TIGER2024/TRACT/) · [ACS B25003](https://api.census.gov/data/2024/acs/acs5/groups/B25003.html)

- **필지 지도**에는 단일 필지 999건의 경계와 주택 5,864호가 담겨 있습니다. 용도지역은 시 필지 자료의 zoning_code를 사용합니다.
- **구역별 요약표** `results/tract_summary.csv`에는 여러 필지에 걸친 1건(9호)도 포함해 총 5,873호가 집계됩니다. 각 행의 주택 수는 차이나타운 경계 안에 중심점이 있는 토지이용 기록의 합입니다.
- **임차가구 비율**은 tract 전체의 ACS 임차가구 추정치를 전체 점유 주택 추정치로 나눈 값입니다. 같은 tract의 필지는 이 값을 공유합니다.
