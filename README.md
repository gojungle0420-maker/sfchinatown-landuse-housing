# sfchinatown-landuse-housing
A Python-based geospatial data pipeline integrating parcel, land use, zoning, and Census data to analyze housing conditions in San Francisco's Chinatown.

샌프란시스코시 토지이용 자료에서 중심점이 차이나타운 분석 경계 안에 있는 레코드를 골라, 지리 단위별 주택 수를 집계합니다.

## 첫 실행

Python 3이 있는 환경에서 이 폴더를 열고 아래 명령을 실행하세요. 추가 패키지나 API 키는 필요 없습니다.

    python3 analyze.py

inputs/snapshot.json에 포함된 고정 입력을 읽습니다. results/summary.csv는 지리 단위별 레코드 수, 값이 알려진 주택 수의 합계, 주택 수 누락 건수를 담습니다. results/chinatown.geojson에는 분석 경계와 선택한 중심점이 있습니다.

## 자료와 방법

- [SF Planning 토지이용 자료](https://data.sfgov.org/d/c5ge-t6pj)의 원본 ID(ludb_id), 중심점 경위도, 주택 수(resunits), 지리 단위(geography_type)를 사용합니다. 입력 자료의 기준일은 2026-08-17입니다.
- [DataSF Analysis Neighborhoods](https://data.sfgov.org/d/j2bu-swwd)의 nhood가 Chinatown인 다각형을 사용합니다. fetch.py는 경계의 외접 사각형 안에 중심점이 있는 후보를 내려받습니다. analyze.py는 다각형 내부 검사를 한 번 더 수행합니다. 중심점이 없는 레코드는 조회에서 제외됩니다. 경계에 걸친 필지는 면적 비례로 나누지 않습니다.
- 검증 결과는 후보 2,168건 중 내부 1,000건입니다. 단일 필지 999건에 5,864호, 여러 필지를 묶은 레코드 1건에 9호가 기록됐습니다. 합계는 원자료에 기록된 주택 수이며, 입주 가구 수나 임차 가구 수를 측정하지 않습니다.
- 새로운 공개 자료로 갱신하려면 인터넷과 curl이 있는 환경에서 python3 fetch.py 다음에 python3 analyze.py를 실행합니다. 입력 파일이 교체되므로 기존 결과를 재현하려면 먼저 현재 버전을 Git에 커밋하세요.
- 다음 분석에서는 2020 Census tract와 분석 동네 대응표를 확인한 뒤 기존 ACS 임차가구 자료의 조사 기간과 분모를 기록합니다. 이번 결과는 토지이용 자료만 집계합니다.
