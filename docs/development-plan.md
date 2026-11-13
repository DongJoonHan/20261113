# 개발 계획

Pytest 결과를 차수별로 저장하고, 웹에서 표와 트렌드 차트로 보여주는 프로그램의 개발 계획이다.
이슈와 마일스톤은 GitHub에서 관리한다.

## 기술 스택

| 영역 | 선택 | 이유 |
|---|---|---|
| 언어 | Python 3.12 | Pytest 생태계와 같은 언어 |
| 결과 입력 | JUnit XML (`pytest --junitxml`) | pytest 기본 기능이라 플러그인이 필요 없음, 표준 라이브러리로 파싱 가능 |
| API | FastAPI REST API (`/api/v1`, JSON, OpenAPI 자동 문서) | CI·외부 도구에서 결과 등록/조회, 웹 UI와 같은 서비스 계층 사용 (#10) |
| 웹 | FastAPI + Jinja2 (서버 렌더링) | 화면 로직을 Python에 두어 Pytest로 branch 커버리지 100% 검증 가능 |
| 차트 | Chart.js (CDN) | 트렌드 선 그래프용, 빌드 도구 불필요 |
| 저장소 | 파일 시스템 (`results/<차수>/`) | 요구사항이 "폴더별 관리", DB 불필요 |
| 품질 | Ruff, Pytest, pytest-cov | CLAUDE.md 규칙 |

## 구조

```
src/pytest_report_viewer/
  storage.py    # 차수 폴더 저장/목록 (#3)
  parser.py     # JUnit XML → 테스트 결과 모델 (#1)
  models.py     # TestCase, Run, RunSummary 데이터클래스
  trend.py      # 차수별 집계 (#4)
  compare.py    # 차수 비교 (#6), 테스트 이력/Flaky (#7)
  service.py    # API와 웹이 함께 쓰는 조회/등록 로직
  api/          # REST API 라우트 /api/v1 (#10)
  web/          # 웹 화면 라우트 + Jinja2 템플릿 (#2, #5, #8)
  app.py        # FastAPI 앱: api + web 라우터 등록
  cli.py        # `import` / `serve` 명령
tests/          # 모듈별 test_*.py, fixtures/ 에 샘플 XML
results/        # 차수 데이터 (git 제외)
```

흐름: `pytest --junitxml=report.xml` → `POST /api/v1/runs` (또는 `cli import report.xml`) → `results/<차수>/` 저장 → 웹 화면 또는 `GET /api/v1/...` 조회

계층: `api/`, `web/` → `service.py` → `storage`/`parser`/`trend`/`compare`. 라우트에는 로직을 두지 않는다.

### REST API (`/api/v1`) — 상세는 #10

| 메서드 | 경로 | 마일스톤 |
|---|---|---|
| POST / GET | `/runs` | M1 |
| GET / DELETE | `/runs/{run_id}` | M1 |
| GET | `/runs/{run_id}/tests` | M1 (필터는 M2 #8) |
| GET | `/trend` | M1 |
| GET | `/runs/{run_id}/tests/detail?nodeid=` | M2 (#5) |
| GET | `/runs/{run_id}/compare?base=` | M2 (#6) |
| GET | `/tests/history?nodeid=`, `/tests/flaky` | M3 (#7) |

CI 연동 예: `curl -F file=@report.xml -F commit=$GITHUB_SHA http://<host>/api/v1/runs`

## 마일스톤

### M0 개발 기반
- CI 워크플로를 `main`에 반영하고 브랜치 보호 적용 (진행 중: push 권한 문제)
- #9 함수 50라인 · 주석 20% 검사 스크립트를 CI에 추가

### M1 MVP: 결과를 차수별로 저장하고 웹에서 본다
순서는 의존 관계를 따른다.
1. #1 테스트 결과 분석: JUnit XML 파싱, 성공/실패/에러/스킵 분류
2. #3 차수별 결과 수집: 차수 폴더 생성, 메타데이터, 목록 조회
3. #4 트렌드 집계: 차수별 성공률·건수·소요시간
4. #10 REST API: 차수 등록/목록/조회/삭제, 테스트 목록, 트렌드
5. #2 웹 페이지: 차수 목록, 차수별 성공/실패 표, 트렌드 차트 (#10과 같은 서비스 계층 사용)

완료 기준: 실제 pytest 결과 3차수를 API로 등록하고, 웹과 API에서 표와 트렌드를 확인할 수 있다.

### M2 분석 강화
- #5 실패 테스트 상세 (메시지, traceback)
- #6 차수 간 비교 (신규 실패, 해결, 추가/삭제)
- #8 결과 표 필터/검색

### M3 고급 분석
- #7 테스트별 이력, Flaky 테스트 탐지

## 작업 방식

- 이슈 하나당 브랜치 하나 (`feature/<이슈번호>-<설명>`), PR 본문에 `Closes #<번호>`
- TDD: 실패하는 테스트 작성 → 구현 → 리팩터링
- PR은 Ruff 위반 0개, branch 커버리지 100%, CI 통과 후 병합
- 웹 화면은 FastAPI `TestClient`로 응답 HTML을 검증해 커버리지에 포함

## 위험 요소

| 위험 | 대응 |
|---|---|
| 웹 화면의 JS(차트, 필터)는 Pytest 커버리지 밖 | JS는 데이터 표시만 맡기고 필터·집계 로직은 서버(Python)에서 처리 |
| JUnit XML 형식 차이 (pytest 버전, xunit1/xunit2) | 여러 버전의 샘플 XML을 테스트 fixture로 보관 |
| 차수가 많아지면 매 요청마다 전체 폴더 파싱 | 차수별 요약(`summary.json`)을 수집 시점에 저장 |
| API 인증 없이 외부 노출 시 누구나 등록/삭제 가능 | 기본은 내부망 전제, 외부 노출 시 `POST`/`DELETE`에 API 토큰 적용 (#10 미결정) |
| 대용량 XML 업로드 | 업로드 크기 제한, 초과 시 `413` |
