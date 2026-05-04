# Local Test Guide

이 문서는 현재 프로젝트를 `Firestore Emulator` 기준으로 로컬 테스트하는 순서를 정리한 체크리스트입니다.

## 목적

아래 4가지를 로컬에서 확인할 수 있습니다.

1. FastAPI 서버 실행
2. 클라이언트에서 서버 요청 전송
3. `riot_loader`로 Riot 데이터 적재
4. Firestore 상태 조회

## 사전 준비

아래 프로그램이 설치되어 있어야 합니다.

- Python 가상환경
- Node.js
- Firebase CLI
- Java

PowerShell에서 확인:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
node -v
npm.cmd -v
firebase.cmd --version
java -version
```

## 1. Firestore Emulator 실행

PowerShell 창 1:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
firebase.cmd emulators:start --only firestore --project demo-team-builder-local --import .\firebase-emulator-data --export-on-exit
```

정상 실행되면 보통 아래 주소를 사용합니다.

- Firestore Emulator: `127.0.0.1:8080`
- Emulator UI: `http://127.0.0.1:4000`

## 2. FastAPI 서버 실행

PowerShell 창 2:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
pip install -r server\requirements.txt
$env:FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="demo-team-builder-local"
$env:TEAM_BUILDER_FIRESTORE_DATABASE="(default)"
$env:TEAM_BUILDER_JWT_SECRET="local-dev-secret"
python -m uvicorn server.main:app --reload
```

Riot API 키를 서버에 숨기고 테스트하려면 추가:

```powershell
$env:TEAM_BUILDER_RIOT_API_KEY="여기에_라이엇_API_키"
```

헬스체크:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 3. 관리자 계정 생성

PowerShell 창 3 또는 같은 창에서 별도 실행:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/auth/bootstrap-admin" `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin12345"}'
```

이미 계정이 있으면 `409` 응답이 나올 수 있으며, 그 경우 기존 계정을 그대로 쓰면 됩니다.

## 4. 클라이언트 실행

PowerShell 창 3:

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
python client\main.py
```

클라이언트 설정에서 서버 주소를 아래로 맞춥니다.

```text
http://127.0.0.1:8000
```

## 5. Riot Loader 실행

PowerShell 창 4:

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
python -m client.tools.riot_loader
```

로그인:

- 아이디: `admin`
- 비밀번호: `admin12345`
- 서버 주소: `http://127.0.0.1:8000`

`riot_loader` 테스트 순서:

1. `1. PUUID 조회`
2. `2. 매치 ID 조회`
3. `3. 한 경기 상세 조회`
4. `4. 최근 경기 DB 적재`

주의:

- 현재 `riot_loader` UI는 `Riot API Key` 입력칸을 비우면 진행을 막습니다.
- 서버 환경변수에 Riot 키를 넣었더라도, 현재 UI 테스트에서는 입력칸에도 키를 넣는 편이 안전합니다.

## 6. Firestore 상태 확인

### 브라우저 UI

브라우저에서:

```text
http://127.0.0.1:4000
```

여기서 컬렉션과 문서를 확인할 수 있습니다.

예상 컬렉션:

- `app_users`
- `riot_accounts`
- `matches`
- `match_participants`

### Firestore 모니터 GUI

PowerShell 창 6:

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
$env:FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="demo-team-builder-local"
python server\tools\firestore_monitor.py
```

이 도구에서 볼 수 있는 것:

- 컬렉션별 문서 수
- 컬렉션별 대략적인 JSON 크기
- 문서 ID 목록
- 선택 문서의 JSON 상세

## 7. 종료 후 데이터 유지

에뮬레이터를 아래처럼 실행했기 때문에:

```powershell
firebase.cmd emulators:start --only firestore --project demo-team-builder-local --import .\firebase-emulator-data --export-on-exit
```

종료 시 데이터가 `firebase-emulator-data` 폴더로 저장되고, 다음 실행 때 다시 불러옵니다.

## 문제 해결

### emulator가 바로 종료될 때

```powershell
firebase.cmd emulators:start --only firestore --project demo-team-builder-local --debug
```

### PowerShell에서 명령이 막힐 때

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### firebase/nmp가 인식되지 않을 때

```powershell
firebase.cmd --version
npm.cmd -v
```

### 서버 import 에러가 날 때

먼저 의존성 설치:

```powershell
pip install -r server\requirements.txt
```
