# 패치 노트

날짜: 2026-05-05
프로젝트: LOL Team Builder

## 요약

이번 작업에서는 Firestore 기반 구조를 더 단순하게 정리하고, 남아 있던 SQLite 의존 소스를 완전히 제거했습니다. 또한 배포 문서를 `Cloud Run + Firestore + Docker` 기준으로 정리하고, 로컬 Firestore Emulator 테스트 문서를 추가했습니다. 마지막으로 서버의 `stores`, `services`, `controllers`, `queries` 계층에 함수 단위 역할 설명을 보강해 유지보수 가독성을 높였습니다.

## 상세 변경 사항

### 1. SQLite 의존 소스 완전 제거

- 서버에서 더 이상 사용하지 않는 SQLite 전용 모듈을 삭제했습니다.
- 삭제 대상:
  - `server/backend/database.py`
  - `server/backend/queries/match_read_query.py`
  - `server/backend/queries/match_write_query.py`
  - `server/tools/common.py`
  - `server/tools/db_query_shell.py`
  - `server/tools/db_viewer.py`
- `server/backend/config.py` 에서 `TEAM_BUILDER_DB_PATH` 와 `riot_matches.db` 관련 설정도 제거했습니다.

### 2. Firestore 저장 계층 역할 분리

- 기존 `server/backend/firestore_store.py` 하나에 몰려 있던 저장 책임을 `stores` 패키지로 분리했습니다.
- 새 구조:
  - `server/backend/stores/firestore_client.py`
  - `server/backend/stores/user_store.py`
  - `server/backend/stores/riot_account_store.py`
  - `server/backend/stores/match_store.py`
- `auth`, `match`, `riot` 서비스가 새 저장 계층을 사용하도록 import 경로를 정리했습니다.

### 3. 로컬 Firestore 테스트 흐름 정리

- Firestore Emulator용 설정 파일을 프로젝트 루트에 추가했습니다.
  - `.firebaserc`
  - `firebase.json`
  - `firestore.rules`
- 로컬 테스트 절차를 `local_test_guild.md` 문서로 정리했습니다.
- Firestore 내용을 확인할 수 있도록 다음 도구를 유지했습니다.
  - `server/tools/firestore_query_shell.py`
  - `server/tools/firestore_viewer.py`

### 4. 관리자 최초 생성 UX 개선

- 로그인 다이얼로그에서 최초 관리자 생성 모드일 때 기본 아이디 `admin` 을 자동 제안하도록 변경했습니다.
- 아이디를 비워둔 채 최초 관리자 생성을 눌러도 기본값이 자동 적용되도록 정리했습니다.
- 관련 파일:
  - `client/ui/login_dialog.py`

### 5. 배포 문서와 흔적 정리

- 기존 Compute Engine 배포 문서와 설정 파일을 제거했습니다.
- `Cloud Run + Firestore + Docker` 기준 문서를 새로 추가했습니다.
  - `deploy/gcp/DEPLOY_GCP_CLOUD_RUN_DOCKER.md`
- `README.md` 의 배포 안내 링크도 새 문서 기준으로 교체했습니다.
- Firebase 디버그 로그는 `.gitignore` 에 추가했습니다.

### 6. 함수 단위 역할 주석 보강

- 저장 계층, 서비스 계층, 컨트롤러 계층, 쿼리 계층에 함수 역할을 설명하는 한글 docstring/주석을 추가했습니다.
- 특히 아래 파일들에 설명을 집중적으로 보강했습니다.
  - `server/backend/stores/*`
  - `server/backend/services/auth_service.py`
  - `server/backend/services/match_service.py`
  - `server/backend/services/riot_service.py`
  - `server/backend/controllers/*`
  - `server/backend/queries/riot_api_query.py`

## 영향

- 서버 구조가 Firestore 기준으로 더 명확해져 이후 유지보수와 확장이 쉬워졌습니다.
- 로컬 테스트 환경에서 Firestore Emulator를 기준으로 서버/클라이언트/적재/조회 흐름을 재현하기 쉬워졌습니다.
- SQLite와 Compute Engine 잔존 흔적이 정리되어 현재 프로젝트 방향이 더 선명해졌습니다.
- 함수 단위 설명이 추가되어 코드 온보딩 속도와 읽기 편의성이 좋아졌습니다.
