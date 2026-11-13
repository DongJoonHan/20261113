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
- 개발 계획과 기술 스택은 [docs/development-plan.md](docs/development-plan.md)를 따른다.

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

## 테스트 케이스 (검증)

- 시스템 테스트 케이스는 `tester` 서브에이전트([.claude/agents/tester.md](.claude/agents/tester.md))가 `system-test-cases` 스킬([.claude/skills/system-test-cases/SKILL.md](.claude/skills/system-test-cases/SKILL.md)) 규칙으로 생성한다.
- 산출물: `docs/test-cases/system-test-cases.xlsx` (기능 / 비기능 / 추적성 시트)
- 마일스톤을 마칠 때 해당 범위의 테스트 케이스를 갱신한다.

## 커밋 / PR 규칙

- 이슈 하나당 브랜치 하나: `feature/<이슈번호>-<설명>`, `chore/<이슈번호>-<설명>`
- 커밋 제목에 이슈 번호: `test(#3): ...`, `feat(#3): ...`, 본문에 `Refs #N` (마지막 커밋은 `Closes #N`)
- TDD 순서로 커밋: test(red) → feat(green) → refactor
- PR은 merge commit으로 병합해 커밋별 이슈 추적을 유지한다

## 릴리즈 절차

마일스톤 하나를 마치면 릴리즈한다 (M1 → v0.1.0, M2 → v0.2.0, M3 → v1.0.0).

1. `tester` 서브에이전트로 해당 범위의 시스템 테스트 케이스를 생성·실행한다. 결과는 `docs/test-cases/`(xlsx, summary.md)에 남는다. Fail이 있으면 이슈로 등록하고 수정 후 다시 실행한다.
2. `pyproject.toml`의 version을 올리고, 1의 결과와 함께 PR로 병합한다.
3. main에서 `vX.Y.Z` 태그를 push한다.
4. [.github/workflows/release.yml](.github/workflows/release.yml)이 자동으로 빌드, SHA-256 체크섬, GitHub Release, Wiki 페이지(`Release-Notes-vX.Y.Z`, 목록 `Release-Notes`)를 만든다.
5. 릴리즈 후 사용자에게 Release/Wiki 링크와 산출물 체크섬을 알린다.
