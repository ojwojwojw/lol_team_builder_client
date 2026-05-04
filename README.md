# LOL Team Builder

리그 오브 레전드 내전 밸런싱을 돕는 데스크톱 클라이언트와 FastAPI 서버 프로젝트입니다.

현재 서버 저장소는 `SQLite`가 아니라 `Firestore`를 사용합니다. 최근 경기 데이터와 Riot 계정 메타데이터, 앱 사용자 계정은 Firestore에 저장됩니다.

## 프로젝트 구조

- `client/`
  - 데스크톱 클라이언트 코드
- `client/domain/`
  - 팀 생성 알고리즘과 밸런스 계산 로직
- `client/tools/`
  - Riot 데이터 적재용 보조 도구
- `server/`
  - FastAPI 서버
- `deploy/gcp/`
  - GCP 배포 관련 문서와 설정

## 현재 서버 아키텍처

- 앱 사용자 계정 저장: `app_users`
- Riot 계정 메타데이터 저장: `riot_accounts`
- 경기 요약/원본 저장: `matches`
- 참가자 인덱스 저장: `match_participants`

Riot API 키는 요청 바디로 넘길 수도 있고, 서버 환경변수 `TEAM_BUILDER_RIOT_API_KEY`에 넣어 숨길 수도 있습니다.

## 로컬 실행

### 1. 가상환경 활성화

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
```

### 2. 서버 의존성 설치

```powershell
pip install -r server\requirements.txt
```

### 3. Firestore 접속 환경변수 설정

실서비스 Firestore를 쓸 때:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="your-gcp-project-id"
$env:TEAM_BUILDER_FIRESTORE_DATABASE="(default)"
$env:TEAM_BUILDER_JWT_SECRET="replace-with-a-long-random-secret"
$env:TEAM_BUILDER_RIOT_API_KEY="your-riot-api-key"
```

로컬 테스트에서 Firestore Emulator를 쓸 때:

```powershell
$env:FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="team-builder-local"
$env:TEAM_BUILDER_FIRESTORE_DATABASE="(default)"
$env:TEAM_BUILDER_JWT_SECRET="local-dev-secret"
$env:TEAM_BUILDER_RIOT_API_KEY="your-riot-api-key"
```

### 4. 서버 실행

```powershell
python -m uvicorn server.main:app --reload
```

### 5. 클라이언트 실행

```powershell
python client\main.py
```

## Firestore 관련 메모

- Firestore 인증은 기본적으로 `GOOGLE_APPLICATION_CREDENTIALS` 또는 GCP 기본 인증 정보를 사용합니다.
- `FIRESTORE_EMULATOR_HOST`가 설정되어 있으면 로컬 에뮬레이터를 사용합니다.
- `get_recent_matches_by_riot_id` 같은 일부 조회는 Firestore에서 복합 인덱스를 요구할 수 있습니다.

## 배포 문서

- Compute Engine + Docker: [deploy/gcp/DEPLOY_GCP_COMPUTE_ENGINE_DOCKER.md](deploy/gcp/DEPLOY_GCP_COMPUTE_ENGINE_DOCKER.md)
