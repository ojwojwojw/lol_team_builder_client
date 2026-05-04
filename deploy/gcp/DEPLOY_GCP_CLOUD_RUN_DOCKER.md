# GCP Cloud Run + Firestore + Docker 배포 가이드

이 문서는 현재 프로젝트를 `Cloud Run + Firestore + Docker` 구조로 배포하는 기준 문서입니다.

점검 기준:
- Cloud Run은 컨테이너가 `PORT` 환경변수로 주어진 포트에서 `0.0.0.0` 으로 리스닝해야 합니다.
- Cloud Run에 배포하는 컨테이너 이미지는 `linux/amd64` 를 포함해야 합니다.
- Firestore 서버 클라이언트는 Firestore 보안 규칙이 아니라 `IAM 권한`으로 접근합니다.

공식 참고:
- Cloud Run deploy: https://cloud.google.com/run/docs/deploying
- Cloud Run container contract: https://cloud.google.com/run/docs/container-contract
- Cloud Run build containers: https://cloud.google.com/run/docs/building/containers
- Artifact Registry Docker auth: https://cloud.google.com/artifact-registry/docs/docker/authentication
- Firestore server IAM: https://cloud.google.com/firestore/docs/security/iam
- Firestore IAM roles: https://cloud.google.com/iam/docs/roles-permissions/firestore

## 1. 현재 배포 구조

- 실행 환경: `Cloud Run`
- 서버: `FastAPI`
- 이미지 저장소: `Artifact Registry`
- 영속 저장소: `Cloud Firestore`
- 관리자 적재 도구: 로컬 `riot_loader`
- Riot API 키 운영: 로컬 관리자 직접 입력 또는 로컬 스케줄러 적재

즉, Cloud Run 서버는 Firestore에 저장된 데이터를 읽고 쓰는 역할에 집중하고, Riot API 대량 적재는 로컬 관리자 도구가 담당하는 구조를 권장합니다.

## 2. 사전 준비

- GCP 프로젝트 생성
- 결제 계정 연결
- `gcloud CLI` 설치 및 로그인
- Docker Desktop 설치 및 실행
- Firestore 데이터베이스 생성
- Cloud Run / Artifact Registry / Cloud Build API 활성화

## 3. 먼저 정할 값

예시는 아래 값을 기준으로 설명합니다.

```text
PROJECT_ID=your-project-id
REGION=asia-northeast3
REPOSITORY=team-builder-repo
SERVICE_NAME=team-builder-api
SERVICE_ACCOUNT=team-builder-runner
IMAGE=asia-northeast3-docker.pkg.dev/your-project-id/team-builder-repo/team-builder-api:latest
```

## 4. Docker 실행 확인

```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker version
```

## 5. GCP 로그인 및 프로젝트 선택

PowerShell에서는 `.ps1` 정책 문제를 피하려고 `.cmd` 형식을 쓰는 편이 안전합니다.

```powershell
gcloud.cmd auth login
gcloud.cmd config set project YOUR_PROJECT_ID
```

## 6. 필요한 API 활성화

```powershell
gcloud.cmd services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  firestore.googleapis.com
```

## 7. Firestore 데이터베이스 생성

Firebase 콘솔 또는 GCP 콘솔에서 Firestore 데이터베이스를 생성합니다.

권장:
- 모드: `Native mode`
- 리전: 가능하면 Cloud Run과 같은 리전, 또는 가장 가까운 지원 리전
- 데이터베이스 ID: 기본값 `(default)`

현재 프로젝트는 Firestore `문서 컬렉션` 구조와 Python 서버 클라이언트를 사용하므로 `Native mode` 기준이 맞습니다.

## 8. Artifact Registry 저장소 생성

한 번만 만들면 됩니다.

```powershell
gcloud.cmd artifacts repositories create team-builder-repo `
  --repository-format=docker `
  --location=asia-northeast3
```

Docker가 Artifact Registry에 push 할 수 있도록 인증 헬퍼를 붙입니다.

```powershell
gcloud.cmd auth configure-docker asia-northeast3-docker.pkg.dev
```

## 9. Cloud Run용 서비스 계정 생성

기본 서비스 계정을 써도 되지만, 포트폴리오와 운영 관리 측면에서는 별도 서비스 계정을 권장합니다.

```powershell
gcloud.cmd iam service-accounts create team-builder-runner `
  --display-name "Team Builder Cloud Run"
```

Firestore 읽기/쓰기 권한 부여:

```powershell
gcloud.cmd projects add-iam-policy-binding YOUR_PROJECT_ID `
  --member "serviceAccount:team-builder-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" `
  --role "roles/datastore.user"
```

## 10. Docker 이미지 빌드

### 일반 Windows / x64 환경

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
docker build -t asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest .
```

### ARM 기반 로컬 환경

Cloud Run은 `linux/amd64` 이미지를 요구합니다.  
공식 문서도 Apple Silicon 환경에서는 `--platform linux/amd64` 를 명시하라고 안내합니다.

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
docker build --platform linux/amd64 -t asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest .
```

## 11. 이미지 푸시

```powershell
docker push asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest
```

## 12. Cloud Run 배포

이 프로젝트는 기본적으로 `PORT=8000` 을 사용하도록 Dockerfile이 맞춰져 있습니다.  
따라서 Cloud Run에도 `--port 8000` 으로 맞춥니다.

```powershell
gcloud.cmd run deploy team-builder-api `
  --image asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest `
  --platform managed `
  --region asia-northeast3 `
  --allow-unauthenticated `
  --port 8000 `
  --service-account team-builder-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com `
  --set-env-vars TEAM_BUILDER_FIRESTORE_PROJECT=YOUR_PROJECT_ID,TEAM_BUILDER_FIRESTORE_DATABASE=(default),TEAM_BUILDER_JWT_SECRET=CHANGE_ME_TO_A_LONG_RANDOM_SECRET
```

비용을 낮게 시작하려면 추가로 아래 옵션을 고려할 수 있습니다.

```powershell
  --min-instances 0 `
  --cpu 1 `
  --memory 512Mi
```

### 선택 환경변수

브라우저 기반 호출이 필요할 때만 CORS를 넣으면 됩니다.

```powershell
gcloud.cmd run services update team-builder-api `
  --region asia-northeast3 `
  --update-env-vars TEAM_BUILDER_CORS_ORIGINS=https://your-client-origin.example
```

Riot API 키를 서버에 상시 넣고 싶다면:

```powershell
gcloud.cmd run services update team-builder-api `
  --region asia-northeast3 `
  --update-env-vars TEAM_BUILDER_RIOT_API_KEY=YOUR_RIOT_API_KEY
```

다만 현재 프로젝트 컨셉상, Riot API 키는 서버 상주보다 `관리자 로컬 도구에서 직접 입력`하는 운영 방식이 더 잘 맞습니다.

## 13. 배포 확인

서비스 URL 확인:

```powershell
gcloud.cmd run services describe team-builder-api `
  --region asia-northeast3 `
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

## 14. 최초 관리자 생성

배포 후 한 번만 관리자 계정을 만들면 됩니다.

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "https://YOUR_CLOUD_RUN_URL/auth/bootstrap-admin" `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"CHANGE_ME_ADMIN_PASSWORD"}'
```

이미 계정이 있으면 `409` 응답이 나올 수 있습니다.

## 15. 운영 권장 방식

현재 프로젝트에 가장 잘 맞는 운영 흐름은 아래와 같습니다.

1. Cloud Run 서버는 Firestore 저장/조회 API로 사용
2. 메인 클라이언트는 저장된 전적 데이터를 조회
3. `riot_loader` 는 관리자만 사용
4. Riot API 키는 로컬 관리자 PC에서 입력
5. 친구들 전적은 수동 적재 또는 로컬 스케줄러 적재

이 방식이면:
- Cloud Run 비용을 낮게 유지하기 쉽고
- Firestore에는 친구 데이터가 축적되고
- 서버에 민감한 Riot API 키를 상시 두지 않아도 됩니다

## 16. 자주 점검할 것

- Cloud Run 로그

```powershell
gcloud.cmd run services logs read team-builder-api --region asia-northeast3
```

- Firestore 권한 문제
  - 서비스 계정에 `roles/datastore.user` 가 있는지 확인
- CORS 문제
  - 브라우저 호출이라면 `TEAM_BUILDER_CORS_ORIGINS` 값을 확인
- 이미지 아키텍처 문제
  - ARM 로컬 환경이면 `docker build --platform linux/amd64` 로 다시 빌드

## 17. 관련 문서

- 루트 README: [../../README.md](../../README.md)
- 로컬 테스트: [../../local_test_guild.md](../../local_test_guild.md)
- 최신 패치노트: [../../patch_notes/PATCH_NOTES_2026-05-05.md](../../patch_notes/PATCH_NOTES_2026-05-05.md)
