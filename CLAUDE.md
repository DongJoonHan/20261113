# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Pytest 수행 결과를 웹에서 보여주는 프로그램이다. 요구사항(README.md 기준):

- 각 차수(테스트 실행 회차)의 결과를 **폴더별로** 나누어 관리한다.
- 차수에 걸친 **트렌드**(성공/실패 추이)를 보여준다.
- 성공과 실패를 **표**로 표시한다.

## 현재 상태

아직 소스 코드가 없고 README.md만 있다. 기술 스택, 빌드/실행/테스트 명령, 디렉터리 구조는 정해지지 않았다.
구현을 시작하면서 결정한 내용(스택, 실행 방법, 결과 폴더 규칙, 아키텍처)을 이 파일에 추가한다.

## 작업 시 참고

- 사용자와의 대화 및 문서는 한국어를 기본으로 한다.
- 요구사항이 바뀌면 README.md와 이 파일을 함께 갱신한다.

## 소스코드 품질

- 순환복잡도는 10 이하여야 한다.
- 코드 라인수는 50라인 이하여야 한다.
- TDD 방식으로 개발해야 한다.
- 주석은 20% 이상 달아야 하며, Doxygen 방식을 사용한다.
- 테스트 커버리지는 Branch 커버리지 100%를 달성해야 한다.
- 테스트는 Pytest 사용한다.
- 정적분석은 Ruff 사용하고, 위반사항은 0개를 유지한다.

## 디렉터리 / 명령

- 소스는 `src/`, 테스트는 `tests/` (`test_*.py`)에 둔다. 도구 설정은 [pyproject.toml](pyproject.toml)에 있다.
- 정적분석: `ruff check .` / `ruff format --check .` (순환복잡도 10 초과 시 C901로 실패)
- 테스트: `pytest` (branch 커버리지 100% 미만이면 실패), 단일 테스트: `pytest tests/test_x.py::test_name`
- Ruff로 강제되지 않는 규칙(함수 50라인, 주석 20%)은 리뷰 시 직접 확인한다.

## 브랜치 / CI 정책

- `main`에 직접 push 금지. 작업은 별도 브랜치에서 하고 PR로 병합한다.
- PR과 `main` 병합 시 [.github/workflows/ci.yml](.github/workflows/ci.yml)이 Ruff 정적분석과 Pytest를 실행한다.
- `Static Analysis (Ruff)`, `Test (Pytest)` 두 체크가 통과해야 병합할 수 있다.
