# 장애 리포트

날짜: 2026-05-05  
프로젝트: LOL Team Builder  
주제: 배포 서버에서 최근 매치 조회가 비어 보이던 문제

## 1. 한 줄 요약

문제의 핵심은 이것이었다.

- 경기 상세 원본은 `matches` 컬렉션에 있었음
- 그런데 실제 최근 매치 조회는 `match_participants` 컬렉션을 보고 있었음
- 어떤 계정들은 `matches`만 있고 `match_participants`가 비어 있거나 불완전했음
- 그래서 Firestore에 데이터가 있는데도 최근 매치 목록이 빈 것처럼 보였음

즉, **원본 데이터는 있었지만 조회용 인덱스가 비어 있던 문제**였다.

## 2. 실제 조회 흐름

메인 클라이언트에서 계정을 선택하면 다음 API가 호출된다.

- `GET /matches/recent/by-riot-id`

이 라우터는 여기로 연결된다.

- [match_controller.py](../server/backend/controllers/match_controller.py)
  - `router = APIRouter(dependencies=[Depends(get_current_user)])`
  - `get_recent_matches_by_riot_id(...)`

그다음 서비스 계층은 여기다.

- [match_service.py](../server/backend/services/match_service.py)
  - `get_recent_matches_by_riot_id(...)`

그리고 실제 Firestore 조회는 여기서 일어난다.

- [match_store.py](../server/backend/stores/match_store.py)
  - `get_recent_matches_by_riot_id(...)`
  - `get_recent_matches_by_puuid(...)`

중요한 점:

- 최근 매치 목록은 `matches`를 직접 읽지 않는다
- `match_participants` 컬렉션을 읽는다

즉 사용자가 보는 최근 매치 목록의 실제 조회 대상은:

- `matches` 아님
- `match_participants` 맞음

## 3. 실제 저장 구조

### 3-1. `matches`

역할:
- 경기 1판의 원본 상세 저장

저장되는 것:
- `match_id`
- `game_start_timestamp`
- `teams`
- `participants`
- `raw_json`

관련 코드:
- [match_store.py](../server/backend/stores/match_store.py)
  - `_match_collection()`
  - `store_match_bundle(...)`

### 3-2. `match_participants`

역할:
- 최근 매치 목록을 빠르게 읽기 위한 참가자 단위 인덱스

저장되는 것:
- `match_id`
- `puuid`
- `riot_id_game_name`
- `riot_id_tagline`
- `champion_name`
- `kills / deaths / assists`
- `team_position`
- `game_start_timestamp`

관련 코드:
- [match_store.py](../server/backend/stores/match_store.py)
  - `_participant_index_collection()`
  - `_build_participant_index_payload(...)`

### 3-3. 왜 두 컬렉션이 따로 있는가

`matches`만으로도 경기 원본은 볼 수 있다.  
하지만 “이 유저의 최근 경기 10개”를 빠르게 찾으려면 경기별 문서를 전부 훑는 것보다 참가자 기준 인덱스가 훨씬 편하다.

그래서 구조가 이렇게 나뉘었다.

- `matches`: 원본 상세 저장
- `match_participants`: 최근 매치 조회용 인덱스

## 4. 문제를 만든 실제 소스

문제를 만든 핵심 코드는 `store_recent_matches(...)` 안의 기존 스킵 로직이었다.

관련 코드:
- [riot_service.py](../server/backend/services/riot_service.py)

기존 흐름은 대략 이랬다.

1. Riot API에서 최근 `match_id` 목록을 가져온다
2. `get_existing_match_ids(requested_match_ids)`로 Firestore의 `matches` 존재 여부를 확인한다
3. `matches`에 이미 있으면 그 경기는 스킵한다
4. 새 경기만 `store_match_bundle(...)`로 저장한다

문제는 여기다.

### 저장 여부 판단 기준이 `matches`만 보고 있었다

`get_existing_match_ids(...)`는 `matches` 컬렉션만 본다.

즉:

- `matches`에 문서가 있으면 “이미 저장된 경기”로 판단
- 하지만 `match_participants`가 있는지는 확인하지 않음

그래서 이런 상태가 가능했다.

- `matches`: 있음
- `match_participants`: 없음

그런데 적재 코드는 이 경기를 “이미 저장됨”으로 보고 그냥 건너뛰었다.

## 5. 실제로 어떤 상황이 벌어졌는가

예를 들어 어떤 유저의 최근 5경기 중 하나가 `KR_123` 라고 하자.

Firestore 상태:

- `matches/KR_123` 존재
- `match_participants/KR_123_<puuid>` 문서들은 없음

이때 `riot_loader`로 다시 적재하면:

1. `get_existing_match_ids(["KR_123", ...])`
2. `KR_123`는 `matches`에 있으므로 existing으로 판정
3. `store_match_bundle("KR_123", ...)`는 호출되지 않음
4. 따라서 `match_participants`도 다시 안 만들어짐

그 결과:

- 상세 경기 원본은 Firestore에 있음
- 최근 매치 목록 조회는 여전히 실패

이게 바로 “Firestore에 데이터는 있는데 최근 매치가 비어 보이던” 이유였다.

## 6. 처음 수정과 한계

첫 번째 수정은 조회 쪽 완화였다.

커밋:
- `ae546ec`
- `Fix Firestore recent match lookup`

여기서 바꾼 것:

1. `match_participants` 조회에서 Firestore `order_by(...)` 의존을 줄였다
2. Riot ID로 못 찾으면 계정의 `puuid`로 한 번 더 찾도록 fallback을 넣었다

이 수정은 “조회 조건 때문에 못 찾는 문제”를 줄이는 데는 도움이 됐다.

하지만 이걸로는 아래 문제를 해결하지 못했다.

- `match_participants` 문서 자체가 없는 경우

즉 **조회 코드를 고쳐도, 조회 대상 컬렉션이 비어 있으면 여전히 못 찾는다.**

## 7. 최종 해결책

최종적으로는 “기존 경기 문서에서 참가자 인덱스를 다시 만드는 복구 로직”을 넣었다.

커밋:
- `fcf3482`
- `Rebuild Firestore participant indexes`

추가된 핵심 함수:

- [match_store.py](../server/backend/stores/match_store.py)
  - `rebuild_participant_indexes(match_ids)`

이 함수가 하는 일:

1. `matches/{match_id}` 문서를 읽는다
2. 안에 들어 있던 `participants` 배열을 꺼낸다
3. 각 참가자를 `match_participants` 문서로 다시 써 준다

그리고 적재 로직도 바뀌었다.

- [riot_service.py](../server/backend/services/riot_service.py)
  - `store_recent_matches(...)`

이제 기존 경기인 경우에도:

- 그냥 스킵하지 않고
- `rebuild_participant_indexes([match_id])`
- 를 호출해서 인덱스를 다시 만든다

즉 지금은 다음처럼 동작한다.

### 새 경기
- Riot API에서 상세 조회
- `store_match_bundle(...)`
- `matches` 저장
- `match_participants` 저장

### 기존 경기
- `matches`는 이미 있으므로 상세 재조회는 안 함
- 대신 `rebuild_participant_indexes(...)`
- `match_participants`를 복구함

## 8. 왜 JWT / 권한 문제는 아니었는가

이 부분도 다시 코드 기준으로 보면 명확하다.

### 8-1. 매치 조회 라우터는 로그인 보호가 걸려 있다

관련 코드:
- [match_controller.py](../server/backend/controllers/match_controller.py)
  - `router = APIRouter(dependencies=[Depends(get_current_user)])`

즉 로그인 실패면 최근 매치 조회 API 자체가 통과되지 않는다.

### 8-2. 토큰 문제면 빈 목록이 아니라 401이 나와야 한다

관련 코드:
- [security.py](../server/backend/security.py)
  - `get_current_user(...)`
  - `decode_access_token(...)`

여기서 실패하는 경우:

- Bearer 토큰 없음
- 토큰 만료
- 토큰 서명 불일치
- 토큰 `sub`에 해당하는 사용자가 없음
- 사용자가 비활성 상태

이 경우는 응답이:

- “매치 0건”

이 아니라

- `401 Unauthorized`

가 되어야 한다.

### 8-3. 이번 실제 증상은 인증 성공 후 조회만 비어 있었다

실제 현상은 이랬다.

- 로그인 됨
- 계정 검색 됨
- Firestore 데이터 있음
- 최근 매치만 안 보임

이 패턴은 JWT/권한 문제와 맞지 않는다.

## 9. 재발 방지 포인트

앞으로는 아래를 항상 같이 봐야 한다.

### 9-1. 저장 컬렉션과 조회 컬렉션을 구분해서 생각할 것

- `matches`가 있다고 해서 최근 매치 조회가 가능한 것은 아니다
- 최근 매치 조회는 `match_participants`가 있어야 한다

### 9-2. 스킵 조건은 원본 문서만 보면 안 된다

기존처럼:

- “`matches` 있네? 그럼 스킵”

만 하면 안 된다.

최소한:

- 조회 인덱스가 있는지
- 인덱스를 다시 만들어야 하는지

도 같이 고려해야 한다.

### 9-3. 운영자가 확인할 때 봐야 할 컬렉션

최근 매치가 안 보이면 아래 둘을 같이 봐야 한다.

1. `matches`
2. `match_participants`

`matches`만 보고 “데이터 있음”이라고 판단하면 놓칠 수 있다.

## 10. 최종 결론

이번 장애의 본질은 다음 한 문장으로 정리할 수 있다.

> 최근 매치 조회는 `match_participants`를 보는데, 적재 스킵 로직은 `matches`만 보고 있었다.

그래서:

- 원본 경기 문서는 있었고
- 사용자는 데이터가 있다고 생각했지만
- 조회용 인덱스는 비어 있었고
- 클라이언트는 최근 매치를 못 보여줬다

최종 해결은:

1. 조회 쿼리 완화
2. 기존 경기 문서에서 `match_participants`를 복구하는 로직 추가

이 두 단계로 끝냈다.
