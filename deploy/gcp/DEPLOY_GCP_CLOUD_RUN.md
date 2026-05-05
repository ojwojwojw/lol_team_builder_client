# GCP Cloud Run + Firestore 배포 가이드

이 문서는 현재 프로젝트의 백엔드를 `Cloud Run + Firestore` 구조로 배포할 때 참고하는 간단한 안내 문서입니다.

현재 기준:
- 메인 제품은 `PyQt5` 데스크톱 앱
- 백엔드는 `FastAPI`
- 저장소는 `Cloud Firestore`
- 배포 대상은 `Google Cloud Run`

## 핵심 개념

- 팀 생성 알고리즘은 로컬 데스크톱 앱에서 실행됩니다.
- Cloud Run 서버는 계정/최근 경기/상세 경기 조회용 보조 API입니다.
- 데이터는 Firestore에 저장됩니다.

## 필수 환경변수

- `TEAM_BUILDER_FIRESTORE_PROJECT`
- `TEAM_BUILDER_FIRESTORE_DATABASE`
- `TEAM_BUILDER_JWT_SECRET`
- `TEAM_BUILDER_RIOT_API_KEY`

로컬 에뮬레이터를 쓸 때만:
- `TEAM_BUILDER_FIRESTORE_EMULATOR_HOST`

배포 환경에서는 `TEAM_BUILDER_FIRESTORE_EMULATOR_HOST`를 설정하지 않습니다.

## GCP 준비

1. 프로젝트 생성
2. 결제 계정 연결
3. Firestore 생성
4. Cloud Run API 활성화
5. 서비스 계정 준비

## 배포 방향

- Firestore는 `(default)` / Native mode 기준
- 서버는 Cloud Run에 배포
- 데스크톱 앱은 별도 배포

## Secret Manager 권장 방식

- `TEAM_BUILDER_RIOT_API_KEY`는 Cloud Run 일반 평문 환경변수보다 `Secret Manager` 연동 방식으로 주입하는 것을 권장합니다.
- 운영 환경에서는 Riot API 키를 코드 저장소나 클라이언트에 두지 않고, GCP에서만 관리합니다.
- 로컬 개발에서는 `.env` 또는 셸 환경변수를 사용하고, 운영 배포에서는 같은 변수명을 Secret Manager로 연결하면 됩니다.

## 참고 문서

- 루트 README: [../../README.md](../../README.md)
- 영문 README: [../../README_EN.md](../../README_EN.md)
- 로컬 테스트 가이드: [../../local_test_guild.md](../../local_test_guild.md)
