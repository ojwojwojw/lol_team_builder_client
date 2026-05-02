# Riot Open API Match Collector

## 개요
- 라이엇 Open API를 사용해 친구들의 최근 대전기록을 수집하고, SQLite DB에 저장하는 FastAPI 기반 프로젝트입니다.
- 테스트는 로컬에서 진행하며, 소규모 배포도 고려합니다.

## 주요 기능
- 소환사명으로 소환사 정보 조회
- 친구들의 최근 매치 기록 수집 및 저장
- 친구들끼리 함께한 매치 필터링

## 실행 방법
1. `requirements.txt`의 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```
2. `main.py`의 `RIOT_API_KEY`에 본인 라이엇 API 키 입력
3. 서버 실행
   ```bash
   uvicorn main:app --reload
   ```
4. 테스트 엔드포인트
   - `GET /test_summoner/{summoner_name}`

## TODO
- 친구 목록 관리
- 매치 리스트/상세 정보 적재
- 친구들끼리 한 매치 필터링
- 주기적 데이터 갱신
