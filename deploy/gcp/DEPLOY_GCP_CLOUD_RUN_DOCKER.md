# GCP Cloud Run + Firestore 배포 준비 가이드

이 문서는 `아직 Docker 컨테이너도 없고, Firestore도 만들지 않은 상태`에서 시작해서,
현재 프로젝트를 `Cloud Run + Firestore` 구조로 배포하기 전까지의 준비와 배포 순서를 한 번에 정리한 문서입니다.

이 문서에는 `실제 비밀값`, `실제 관리자 비밀번호`, `서비스 계정 키 파일 내용`은 넣지 않습니다.  
GitHub에 올려도 되는 값만 문서에 남기고, 나머지는 `직접 로컬에서 입력`하는 방식으로 진행합니다.

중요:
- 로컬용 소스와 배포용 소스를 따로 두지 않습니다.
- 같은 코드베이스를 사용하고, Firestore 연결만 환경변수로 분기합니다.
- 로컬 개발: `TEAM_BUILDER_FIRESTORE_EMULATOR_HOST=127.0.0.1:8080`
- 배포 환경: `TEAM_BUILDER_FIRESTORE_EMULATOR_HOST` 를 아예 설정하지 않음

공식 참고:
- Cloud Run deploy: https://cloud.google.com/run/docs/deploying
- Cloud Run container contract: https://cloud.google.com/run/docs/container-contract
- Cloud Run source deploy: https://cloud.google.com/run/docs/deploying-source-code
- Artifact Registry Docker auth: https://cloud.google.com/artifact-registry/docs/docker/authentication
- Cloud Build build containers: https://cloud.google.com/build/docs/building/build-containers
- Firestore IAM: https://cloud.google.com/firestore/docs/security/iam
- Firestore roles: https://cloud.google.com/iam/docs/roles-permissions/firestore

## 1. 현재 권장 아키텍처

- 메인 앱: 로컬 `PyQt5` 데스크톱 앱
- 운영 도구: 로컬 `riot_loader`
- API 서버: `FastAPI`
- 컨테이너 실행 환경: `Cloud Run`
- 저장소: `Cloud Firestore`
- 이미지 저장소: `Artifact Registry`

운영 방향:
- 팀 생성 알고리즘은 로컬에서 실행
- 서버는 Firestore에 저장된 Riot 데이터 조회/관리 역할
- Riot API 키는 서버 상주보다 `관리자 로컬 도구에서 직접 입력`하는 방식 권장

## 2. GitHub에 올리면 안 되는 정보

절대 문서나 소스에 직접 넣지 말 것:
- `TEAM_BUILDER_JWT_SECRET` 실제 값
- 관리자 초기 비밀번호 실제 값
- Riot API 키
- 서비스 계정 키 JSON
- 개인 PC 절대 경로가 들어간 비밀 파일

권장:
- 문서에는 항상 `CHANGE_ME`, `YOUR_PROJECT_ID` 같은 자리표시자만 사용
- 실제 값은 PowerShell 변수나 Cloud Run 환경변수로만 입력

## 3. 사전 준비 체크리스트

아래가 모두 준비되어 있어야 합니다.

- GCP 프로젝트 생성
- 결제 계정 연결
- Firestore API / Cloud Run API / Artifact Registry API / Cloud Build API 사용 가능
- `gcloud CLI` 설치
- Docker Desktop 설치
- 프로젝트 로컬 코드 준비

## 4. 로컬 PC 준비

### 4-1. gcloud CLI 로그인

PowerShell에서는 `.cmd` 형식이 더 안정적일 수 있습니다.

```powershell
gcloud.cmd auth login
gcloud.cmd config set project YOUR_PROJECT_ID
```

### 4-2. 프로젝트 확인

```powershell
gcloud.cmd config get-value project
```

### 4-3. Docker Desktop은 선택 사항

이번 문서의 기본 경로는 `로컬 Docker 없이 Cloud Build 원격 빌드` 입니다.

즉 아래가 가능합니다.
- 로컬 Docker Desktop이 없어도 배포 가능
- Dockerfile은 그대로 유지
- 이미지는 GCP가 대신 빌드

로컬 Docker는 아래 경우에만 선택적으로 사용하면 됩니다.
- 배포 전에 내 PC에서 컨테이너를 직접 띄워보고 싶을 때
- 이미지 빌드 결과를 로컬에서 검증하고 싶을 때

## 5. GCP 콘솔에서 먼저 할 일

### 5-1. 프로젝트 생성

GCP 콘솔에서 새 프로젝트를 만듭니다.

예:
- 프로젝트 이름: `lol-team-builder`
- 프로젝트 ID: 직접 정하거나 자동 생성

### 5-2. 결제 계정 연결

Cloud Run과 Artifact Registry는 결제 계정 연결이 되어 있어야 안정적으로 진행됩니다.

### 5-3. Firestore 데이터베이스 생성

Firestore는 콘솔에서 먼저 만드는 편이 가장 쉽습니다.

권장 설정:
- 모드: `Native mode`
- 데이터베이스 ID: `(default)`
- 리전: Cloud Run과 같은 리전 또는 가장 가까운 리전

현재 프로젝트는 Firestore 문서 컬렉션을 그대로 쓰는 구조라 `Native mode` 기준이 맞습니다.

## 6. 필요한 API 활성화

```powershell
gcloud.cmd services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  firestore.googleapis.com
```

## 7. 배포 변수 준비

아래 값들은 실제 배포 전에 한 번 정해두면 편합니다.

```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$REGION = "asia-northeast3"
$REPOSITORY = "team-builder-repo"
$SERVICE_NAME = "team-builder-api"
$SERVICE_ACCOUNT_NAME = "team-builder-runner"
$SERVICE_ACCOUNT_EMAIL = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
$IMAGE = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:latest"
$JWT_SECRET = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
```

## 8. Artifact Registry 준비

이미지 저장소를 한 번만 생성하면 됩니다.

```powershell
gcloud.cmd artifacts repositories create $REPOSITORY `
  --repository-format=docker `
  --location=$REGION
```

Docker가 Artifact Registry에 push 할 수 있도록 인증:

```powershell
gcloud.cmd auth configure-docker "${REGION}-docker.pkg.dev"
```

## 9. Cloud Run 서비스 계정 준비

권장: 기본 계정 대신 전용 서비스 계정을 따로 만들어 사용

```powershell
gcloud.cmd iam service-accounts create $SERVICE_ACCOUNT_NAME `
  --display-name "Team Builder Cloud Run"
```

Firestore 읽기/쓰기 권한 부여:

```powershell
gcloud.cmd projects add-iam-policy-binding $PROJECT_ID `
  --member "serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role "roles/datastore.user"
```

## 10. 컨테이너 이미지 준비 방식

현재 프로젝트는 `Dockerfile` 이 이미 있으므로, 아래 두 방식 중 하나를 선택할 수 있습니다.

### 권장: Cloud Build 원격 빌드

- 로컬 Docker Desktop 불필요
- 현재 사용자 환경에 가장 잘 맞음
- Dockerfile 기준으로 이미지 빌드 가능

### 선택: 로컬 Docker 빌드

- Docker Desktop이 정상 동작할 때만 사용
- 배포 전 로컬 컨테이너 테스트에 유용

아래 문서에서는 `Cloud Build 원격 빌드`를 기본 경로로 먼저 설명합니다.

## 11. Cloud Build로 원격 빌드

현재 프로젝트 루트에서 아래 명령을 실행하면, GCP가 `Dockerfile`을 사용해 이미지를 원격 빌드하고 Artifact Registry에 push 합니다.

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
gcloud.cmd builds submit --tag $IMAGE
```

이 방식은 로컬 Docker Desktop이 없어도 동작합니다.

## 12. 선택: 로컬 Docker 빌드

현재 프로젝트는 루트의 [Dockerfile](../../Dockerfile) 기준으로 이미 Cloud Run에 맞는 컨테이너를 만들 수 있습니다.

중요:
- Cloud Run은 컨테이너가 `0.0.0.0` 에서 리스닝해야 함
- `PORT` 환경변수를 사용해야 함
- 멀티 아키텍처 이미지라면 `linux/amd64` 가 포함되어야 함

### 12-1. 일반 x64 Windows 환경

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
docker build -t $IMAGE .
```

### 12-2. ARM 기반 로컬 환경

ARM 기반 PC라면 Cloud Run 호환을 위해 `linux/amd64` 를 명시하는 편이 안전합니다.

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
docker build --platform linux/amd64 -t $IMAGE .
```

### 12-3. 로컬 컨테이너 테스트

배포 전에 로컬에서 한 번 띄워보는 걸 권장합니다.

```powershell
docker run --rm -p 8000:8000 `
  -e TEAM_BUILDER_FIRESTORE_PROJECT=YOUR_PROJECT_ID `
  -e TEAM_BUILDER_FIRESTORE_DATABASE="(default)" `
  -e TEAM_BUILDER_JWT_SECRET=CHANGE_ME_TO_A_LONG_RANDOM_SECRET `
  $IMAGE
```

확인:

```powershell
curl http://127.0.0.1:8000/health
```

참고:
- 실제 Firestore에 붙이려면 로컬에서 GCP 인증이 되어 있어야 함
- 또는 서비스 계정 키 파일을 `GOOGLE_APPLICATION_CREDENTIALS` 로 지정해야 함
- 서비스 계정 키 파일은 Git에 올리면 안 됨

## 13. 이미지 푸시

`Cloud Build`를 사용했다면 이 단계는 이미 끝난 상태입니다.  
로컬 Docker로 빌드한 경우에만 직접 push 하면 됩니다.

```powershell
docker push $IMAGE
```

## 14. Cloud Run 배포 전 필수 환경변수 체크리스트

필수:
- `TEAM_BUILDER_FIRESTORE_PROJECT`
- `TEAM_BUILDER_FIRESTORE_DATABASE`
- `TEAM_BUILDER_JWT_SECRET`

선택:
- `TEAM_BUILDER_CORS_ORIGINS`
- `TEAM_BUILDER_RIOT_API_KEY`

현재 프로젝트 컨셉상 권장:
- `TEAM_BUILDER_RIOT_API_KEY` 는 서버에 상시 두지 않아도 됨
- Riot 적재는 `riot_loader` 가 로컬에서 담당

## 15. Cloud Run 배포

현재 Dockerfile은 `PORT=8000` 기본값을 사용하므로, Cloud Run에서도 `--port 8000` 으로 맞춥니다.

```powershell
gcloud.cmd run deploy $SERVICE_NAME `
  --image $IMAGE `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --port 8000 `
  --service-account $SERVICE_ACCOUNT_EMAIL `
  --min-instances 0 `
  --cpu 1 `
  --memory 512Mi `
  --set-env-vars "TEAM_BUILDER_FIRESTORE_PROJECT=$PROJECT_ID,TEAM_BUILDER_FIRESTORE_DATABASE=(default),TEAM_BUILDER_JWT_SECRET=$JWT_SECRET"
```

브라우저에서 직접 호출하는 클라이언트가 필요하면 추가:

```powershell
gcloud.cmd run services update $SERVICE_NAME `
  --region $REGION `
  --update-env-vars TEAM_BUILDER_CORS_ORIGINS=https://your-client-origin.example
```

## 16. 배포 후 확인

서비스 URL 확인:

```powershell
gcloud.cmd run services describe $SERVICE_NAME `
  --region $REGION `
  --format="value(status.url)"
```

헬스체크:

```powershell
curl https://YOUR_CLOUD_RUN_URL/health
```

정상 응답:

```json
{"status":"ok"}
```

## 17. 최초 관리자 생성

배포 후 관리자 계정을 한 번만 만들면 됩니다.

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "https://YOUR_CLOUD_RUN_URL/auth/bootstrap-admin" `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"CHANGE_ME_ADMIN_PASSWORD"}'
```

이미 계정이 있으면 `409` 응답이 나올 수 있습니다.

## 18. 운영 권장 방식

현재 프로젝트에서 가장 잘 맞는 운영 흐름:

1. 메인 클라이언트는 Firestore에 저장된 데이터를 읽음
2. Cloud Run 서버는 Firestore 조회/관리 API 역할
3. `riot_loader` 는 관리자만 사용
4. Riot API 키는 로컬 관리자 PC에서만 사용
5. 친구들 데이터는 수동 적재 또는 로컬 스케줄러 적재

이 방식의 장점:
- Cloud Run 비용을 낮게 유지하기 쉬움
- Firestore에는 친구 데이터가 축적됨
- 민감한 Riot API 키를 서버에 상시 두지 않아도 됨

## 19. GitHub에 올리지 말아야 할 파일 예시

아래 파일은 절대 커밋하지 않는 걸 권장합니다.

- `service-account.json`
- `gcp-service-account.json`
- `*.service-account.json`
- `.env`
- `server/.jwt_secret`
- Riot API 키가 들어 있는 임시 메모 파일

필요하면 `.gitignore` 에 패턴을 추가해 두는 것이 안전합니다.

## 20. 관련 문서

- 루트 README: [../../README.md](../../README.md)
- 로컬 테스트 가이드: [../../local_test_guild.md](../../local_test_guild.md)
- 최신 패치노트: [../../patch_notes/PATCH_NOTES_2026-05-05.md](../../patch_notes/PATCH_NOTES_2026-05-05.md)
