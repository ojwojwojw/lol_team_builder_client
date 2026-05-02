# LOL Team Builder

리그 오브 레전드 내전 팀 밸런싱을 위한 데스크톱 클라이언트와 FastAPI 서버를 함께 관리하는 저장소입니다.

## 프로젝트 구조

- `client/`
  데스크톱 클라이언트 코드가 들어 있습니다.
- `client/application/`
  계정 조회, 최근 전적 요약, 팀 생성, 결과 포맷팅 같은 애플리케이션 흐름을 담당합니다.
- `client/api_clients/`
  서버 API 통신을 담당합니다.
- `client/domain/`
  팀 밸런싱 계산, 포지션 규칙, 도메인 상수를 담당합니다.
- `client/repositories/`
  로컬 JSON 데이터와 설정 파일 입출력을 담당합니다.
- `client/ui/`
  윈도우, 다이얼로그, 위젯, UI 테마를 담당합니다.
- `client/tools/riot_loader.py`
  저장된 Riot 계정 또는 수동 입력으로 최근 경기 데이터를 적재하는 도구입니다.
- `server/`
  FastAPI 서버와 백엔드 모듈이 들어 있습니다.
- `patch_notes/`
  날짜별 패치노트를 보관합니다.

## 주요 기능

- 10명을 기준으로 밸런스 있는 5:5 팀을 생성합니다.
- 최근 경기 전적을 기반으로 승률, KDA, 포지션 통계, 챔피언 통계를 분석합니다.
- 최근 폼과 포지션 적합도를 팀 계산에 반영합니다.
- 라인 밸런스 경고와 완화 규칙 적용 여부를 함께 안내합니다.
- Riot API 기반 계정 및 경기 데이터를 클라이언트 도구에서 적재할 수 있습니다.

## 실행 가이드

### 가상환경 활성화

```powershell
cd C:\Users\wjddn\OneDrive\Desktop\projects\team_builder
.\.venv\Scripts\activate
```

### 클라이언트 실행

```powershell
python client\main.py
```

### Riot 데이터 로더 실행

```powershell
python -m client.tools.riot_loader
```

### 서버 실행

```powershell
python -m uvicorn server.main:app --reload
```

### 클라이언트 빌드

```powershell
pyinstaller client\main.spec
```

## 데이터 및 산출물

- 클라이언트 런타임 데이터는 `client/data/` 아래에 저장됩니다.
- `dist/`는 빌드 산출물 디렉토리이며 Git 추적 대상에서 제외됩니다.
- 클라이언트 오류 로그는 `client/team_builder_client_error.log`에 기록되며 Git 추적 대상에서 제외됩니다.
