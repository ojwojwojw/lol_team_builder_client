# GCP Compute Engine + Docker 배포 가이드

이 문서는 `Firestore`를 저장소로 사용하는 현재 서버를 GCP Compute Engine VM에 Docker로 배포하는 절차입니다.

## 아키텍처

- FastAPI 서버: Docker 컨테이너에서 실행
- 저장소: Firestore
- 인증 정보:
  - JWT 시크릿: `TEAM_BUILDER_JWT_SECRET`
  - Riot API 키: `TEAM_BUILDER_RIOT_API_KEY`
  - Firestore 서비스 계정 JSON: `/opt/team_builder/secrets/service-account.json`
- Nginx: 외부 `80` 포트를 받아 `127.0.0.1:8000`으로 프록시

## 필요한 파일

- `Dockerfile`
- `server/requirements-server.txt`
- `deploy/gcp/compute-engine/bootstrap_vm.sh`
- `deploy/gcp/compute-engine/team-builder-api.service`
- `deploy/gcp/compute-engine/nginx-team-builder.conf`

## server.env 예시

VM에서 `/opt/team_builder/server.env` 파일을 아래처럼 맞춥니다.

```env
TEAM_BUILDER_JWT_SECRET=replace-with-a-long-random-secret
TEAM_BUILDER_CORS_ORIGINS=
TEAM_BUILDER_RIOT_API_KEY=
TEAM_BUILDER_FIRESTORE_PROJECT=your-gcp-project-id
TEAM_BUILDER_FIRESTORE_DATABASE=(default)
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/service-account.json
```

`TEAM_BUILDER_RIOT_API_KEY`를 넣으면 클라이언트가 Riot 토큰을 직접 보내지 않아도 됩니다.

## 로컬에서 먼저 할 일

### 1. Docker Desktop 실행

```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker version
```

### 2. gcloud 로그인 및 프로젝트 선택

PowerShell 실행 정책 문제를 피하려면 `gcloud.cmd`를 쓰는 편이 안전합니다.

```powershell
gcloud.cmd auth login
gcloud.cmd config set project YOUR_PROJECT_ID
```

## VM 생성 후 배포 절차

이미 VM을 만들었다면 `VM 생성` 단계는 건너뛰고 아래부터 진행하면 됩니다.

### 1. HTTP 태그 확인 또는 추가

```powershell
gcloud.cmd compute instances add-tags vm-ojw-1 `
  --zone=YOUR_ZONE `
  --tags=http-server
```

### 2. 방화벽 열기

```powershell
gcloud.cmd compute firewall-rules create team-builder-allow-http `
  --allow tcp:80 `
  --target-tags=http-server
```

### 3. 프로젝트 복사

```powershell
gcloud.cmd compute scp --recurse C:\Users\wjddn\OneDrive\Desktop\projects\team_builder vm-ojw-1:/tmp --zone=YOUR_ZONE
```

### 4. VM 접속

```powershell
gcloud.cmd compute ssh vm-ojw-1 --zone=YOUR_ZONE
```

### 5. 프로젝트 위치 정리

```bash
sudo mkdir -p /opt
sudo mv /tmp/team_builder /opt/team_builder
sudo chown -R $USER:$USER /opt/team_builder
cd /opt/team_builder
```

### 6. VM 초기 설정

```bash
chmod +x deploy/gcp/compute-engine/bootstrap_vm.sh
./deploy/gcp/compute-engine/bootstrap_vm.sh
```

### 7. Firestore 서비스 계정 파일 배치

서비스 계정 JSON 파일을 VM의 아래 경로에 둡니다.

```bash
/opt/team_builder/secrets/service-account.json
```

### 8. 환경변수 설정

```bash
nano /opt/team_builder/server.env
```

### 9. Docker 이미지 빌드

```bash
cd /opt/team_builder
sudo docker build -t team-builder-api .
```

### 10. systemd 서비스 등록

```bash
sudo cp /opt/team_builder/deploy/gcp/compute-engine/team-builder-api.service /etc/systemd/system/team-builder-api.service
sudo systemctl daemon-reload
sudo systemctl enable team-builder-api
sudo systemctl start team-builder-api
sudo systemctl status team-builder-api
```

### 11. 서버 로컬 헬스체크

```bash
curl http://127.0.0.1:8000/health
```

### 12. Nginx 연결

```bash
sudo cp /opt/team_builder/deploy/gcp/compute-engine/nginx-team-builder.conf /etc/nginx/sites-available/team-builder
sudo ln -s /etc/nginx/sites-available/team-builder /etc/nginx/sites-enabled/team-builder
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 13. 외부 접속 확인

```bash
curl ifconfig.me
curl http://YOUR_VM_EXTERNAL_IP/health
```

## 운영 명령어

서비스 재시작:

```bash
sudo systemctl restart team-builder-api
```

로그 확인:

```bash
sudo journalctl -u team-builder-api -f
```

컨테이너 확인:

```bash
sudo docker ps
```

코드 수정 후 재배포:

```bash
cd /opt/team_builder
sudo docker build -t team-builder-api .
sudo systemctl restart team-builder-api
```

## Firestore 로컬 테스트

로컬 에뮬레이터를 쓸 경우 서버 실행 전에 아래 값을 넣습니다.

```powershell
$env:FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
$env:TEAM_BUILDER_FIRESTORE_PROJECT="team-builder-local"
$env:TEAM_BUILDER_FIRESTORE_DATABASE="(default)"
```
