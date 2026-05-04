# Local Test Guide

이 문서는 현재 프로젝트를 `Firestore Emulator` 기준으로 로컬 테스트하는 순서를 정리한 체크리스트입니다.

## 목적

아래 4가지를 로컬에서 확인할 수 있습니다.

1. FastAPI 서버 실행
2. 메인 클라이언트에서 서버 요청
3. `riot_loader` 로 Riot 데이터 적재
4. Firestore Emulator 상태 확인

## 중요한 개념

### 1. 같은 소스코드를 사용한다

로컬용 소스와 배포용 소스를 따로 두지 않습니다.

- 로컬 개발: `TEAM_BUILDER_FIRESTORE_EMULATOR_HOST=127.0.0.1:8080`
- 배포 환경: `TEAM_BUILDER_FIRESTORE_EMULATOR_HOST` 를 설정하지 않음

즉, 같은 코드베이스가 환경변수에 따라
- 로컬에서는 Firestore Emulator
- 배포에서는 실제 Firestore
를 바라보게 됩니다.

### 2. 클라이언트 로그인 상태는 Firestore와 별개로 로컬에 저장된다

메인 클라이언트와 `riot_loader` 는 로그인 토큰을 아래 파일에 저장합니다.

- [client/data/config.json](client/data/config.json)

여기에는 아래 값이 들어갑니다.

- `auth_token`
- `auth_username`

즉 Firestore Emulator 데이터를 지워도, 클라이언트 로컬에는 예전 토큰이 남아 있을 수 있습니다.

그래서 에뮬레이터를 초기화한 뒤에는:
- 서버에서 실제 `admin` 문서가 없어졌는데
- 클라이언트가 여전히 `admin`으로 로그인했던 흔적을 갖고 있을 수 있습니다.

보통은 서버 요청 시 401이 나면서 토큰이 정리되지만,
테스트를 깔끔하게 하려면 에뮬레이터 초기화와 함께 `config.json`의 `auth_token`도 같이 비우는 게 좋습니다.

### 3. Emulator 데이터는 기본적으로 영구 저장이 아니다

Firestore Emulator는 기본적으로 메모리성 테스트 DB에 가깝습니다.

아래처럼 실행하면:

```powershell
firebase.cmd emulators:start --only firestore --project demo-team-builder-local --import .\firebase-emulator-data --export-on-exit
```

종료 시점에 데이터를 `firebase-emulator-data` 폴더로 내보내고, 다음 실행 때 다시 가져옵니다.

정리:
- `--import` 없이 실행하면: 보통 재시작 시 데이터가 사라진다고 생각하는 편이 안전
- `--export-on-exit` 없이 종료하면: 저장되지 않음
- 강제 종료되면: export가 안 될 수 있음
- `firebase-emulator-data` 폴더가 없으면: 이전 데이터가 남지 않은 상태

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
$env:TEAM_BUILDER_FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="demo-team-builder-local"
$env:TEAM_BUILDER_FIRESTORE_DATABASE="(default)"
$env:TEAM_BUILDER_JWT_SECRET="local-dev-secret"
python -m uvicorn server.main:app --reload
```

선택:

```powershell
$env:TEAM_BUILDER_RIOT_API_KEY="여기에_라이엇_API_키"
```

헬스체크:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 3. 관리자 계정 생성

PowerShell 창 3:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/auth/bootstrap-admin" `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin12345"}'
```

이미 계정이 있으면 `409` 응답이 나올 수 있습니다.

## 4. 메인 클라이언트 실행

PowerShell 창 4:

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
python client\main.py
```

서버 주소는:

```text
http://127.0.0.1:8000
```

## 5. Riot Loader 실행

PowerShell 창 5:

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
python -m client.tools.riot_loader
```

로그인:

- 아이디: `admin`
- 비밀번호: `admin12345`
- 서버 주소: `http://127.0.0.1:8000`

## 6. Firestore 상태 확인

### Emulator UI

브라우저에서:

```text
http://127.0.0.1:4000
```

여기서 아래 컬렉션을 확인할 수 있습니다.

- `app_users`
- `riot_accounts`
- `matches`
- `match_participants`

### Firestore 모니터 도구

PowerShell 창 6:

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
$env:TEAM_BUILDER_FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="demo-team-builder-local"
python server\tools\firestore_monitor.py
```

또는 `riot_loader` 안의 `Firestore 관리` 팝업을 쓰는 편이 더 편합니다.

## 7. 에뮬레이터를 껐다 켰을 때 데이터가 안 남는 경우

아래를 확인하세요.

1. `firebase-emulator-data` 폴더가 실제로 생겼는지
2. Emulator를 `Ctrl+C`로 정상 종료했는지
3. `--import .\firebase-emulator-data --export-on-exit` 옵션을 계속 사용했는지
4. 프로젝트 루트에서 실행했는지

현재 폴더에 `firebase-emulator-data` 가 없다면, 이전 export가 안 된 상태일 가능성이 큽니다.

## 8. 에뮬레이터 초기화 후 admin이 없는데 로그인된 것처럼 보일 때

이건 대부분 클라이언트 로컬 토큰 때문입니다.

확인 파일:

- [client/data/config.json](client/data/config.json)

여기서 아래 항목을 비우면 됩니다.

```json
"auth_token": "",
"auth_username": ""
```

또는 아래 방법을 사용할 수 있습니다.

- 로그인 창의 `저장 세션 초기화` 버튼
- 앱 안의 `로그아웃` 버튼

추천 순서:

1. Emulator 초기화
2. `client/data/config.json` 의 `auth_token` / `auth_username` 비우기
3. 서버 재실행
4. `/auth/bootstrap-admin` 으로 admin 다시 생성
5. 메인 클라이언트 / `riot_loader` 재로그인

## 9. 완전 초기화 순서

테스트 상태를 완전히 새로 만들고 싶을 때:

1. Firestore Emulator 종료
2. `firebase-emulator-data` 폴더 삭제
3. `client/data/config.json` 에서 `auth_token`, `auth_username` 비우기
4. Emulator 재실행
5. 서버 재실행
6. admin 재생성

## 10. 자주 막히는 문제

### Emulator가 바로 종료될 때

```powershell
firebase.cmd emulators:start --only firestore --project demo-team-builder-local --debug
```

### PowerShell 실행 정책 문제

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### firebase / npm 인식이 안 될 때

```powershell
firebase.cmd --version
npm.cmd -v
```

### 서버 import 오류가 날 때

```powershell
pip install -r server\requirements.txt
```
