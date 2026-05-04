# GCP Cloud Run + Firestore + Docker 배포 가이드

이 문서는 현재 프로젝트를 `Cloud Run + Firestore` 구조로 배포하는 최소 절차를 정리합니다.

## 구조

- FastAPI 서버: Docker 이미지로 빌드
- 실행 환경: Cloud Run
- 저장소: Firestore
- 로컬 수집 도구: `riot_loader`
- Riot API 키 운영: admin이 로컬에서 관리하고 수동/스케줄 적재

즉, 실서비스 서버는 Firestore에 저장된 데이터만 읽고 응답하고, Riot 적재는 관리자가 별도로 수행하는 구조를 권장합니다.

## 준비물

- GCP 프로젝트
- 결제 계정 연결
- `gcloud` CLI
- Docker Desktop
- Firestore 사용 설정
- Cloud Run / Artifact Registry API 활성화

## 1. 로컬에서 Docker 실행

```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker version
```

## 2. GCP 로그인 및 프로젝트 선택

PowerShell에서는 `.cmd` 형태가 더 안정적일 수 있습니다.

```powershell
gcloud.cmd auth login
gcloud.cmd config set project YOUR_PROJECT_ID
```

## 3. 필요한 API 활성화

```powershell
gcloud.cmd services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com
```

## 4. Firestore 준비

Firebase 콘솔 또는 GCP 콘솔에서 Firestore 데이터베이스를 생성합니다.

- 모드: Native
- 리전: Cloud Run과 같은 리전 권장

## 5. Artifact Registry 저장소 생성

예시는 서울 리전 `asia-northeast3` 기준입니다.

```powershell
gcloud.cmd artifacts repositories create team-builder-repo `
  --repository-format=docker `
  --location=asia-northeast3
```

```powershell
gcloud.cmd auth configure-docker asia-northeast3-docker.pkg.dev
```

## 6. Docker 이미지 빌드

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
docker build -t asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest .
```

## 7. 이미지 푸시

```powershell
docker push asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest
```

## 8. Cloud Run 배포

```powershell
gcloud.cmd run deploy team-builder-api `
  --image asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/team-builder-repo/team-builder-api:latest `
  --platform managed `
  --region asia-northeast3 `
  --allow-unauthenticated `
  --port 8000 `
  --set-env-vars TEAM_BUILDER_FIRESTORE_PROJECT=YOUR_PROJECT_ID,TEAM_BUILDER_FIRESTORE_DATABASE="(default)",TEAM_BUILDER_JWT_SECRET=CHANGE_ME_TO_A_LONG_RANDOM_SECRET,TEAM_BUILDER_CORS_ORIGINS=
```

## 9. 서비스 계정 권한

Cloud Run 서비스 계정이 Firestore에 읽고 쓸 수 있어야 합니다.

최소한 아래 역할 중 하나가 필요합니다.

- `Cloud Datastore User`
- 또는 더 넓은 Firestore 접근 권한

## 10. 배포 후 확인

```powershell
gcloud.cmd run services describe team-builder-api --region asia-northeast3
```

배포 URL이 나오면:

```powershell
curl https://YOUR_CLOUD_RUN_URL/health
```

## 운영 권장 방식

현재 프로젝트에는 아래 운영 방식이 잘 맞습니다.

1. Cloud Run 서버는 Firestore 저장 데이터만 조회
2. Riot API 키는 admin이 로컬에서만 보관
3. `riot_loader`로 수동 적재
4. 필요하면 로컬 스케줄러로 하루 1~2회 적재

이 방식이면 Cloud Run 비용을 낮게 유지하면서도, Firestore에 친구들 데이터를 축적할 수 있습니다.
