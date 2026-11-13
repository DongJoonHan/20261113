#!/usr/bin/env bash
# 릴리즈 노트(Markdown)를 표준 출력으로 만든다.
# 사용: release-notes.sh <태그> <pytest 요약 파일> <체크섬 파일>
#   - 이전 태그부터 이번 태그까지의 커밋과 해결된 이슈를 모은다.
#   - docs/test-cases/summary.md 가 있으면 시스템 테스트 결과로 포함한다.
# 필요: git(전체 이력), gh(GH_TOKEN)
set -euo pipefail

TAG="$1"
PYTEST_SUMMARY="$2"
CHECKSUMS="$3"

# 이전 태그가 없으면(첫 릴리즈) 전체 이력을 범위로 삼는다.
PREV_TAG="$(git describe --tags --abbrev=0 "${TAG}^" 2>/dev/null || true)"
RANGE="${PREV_TAG:+${PREV_TAG}..}${TAG}"

echo "# ${TAG} 릴리즈 노트"
echo
echo "- 릴리즈 일자: $(date -u +%Y-%m-%d)"
echo "- 커밋: \`$(git rev-parse --short "${TAG}")\`"
echo "- 이전 버전: ${PREV_TAG:-없음 (첫 릴리즈)}"
echo

echo "## 해결된 이슈"
echo
# 커밋 본문의 "Closes #N" 으로 해결된 이슈를 찾는다.
ISSUES="$(git log "${RANGE}" --format=%B | grep -oiE 'closes #[0-9]+' | grep -oE '[0-9]+' | sort -un || true)"
if [ -z "${ISSUES}" ]; then
  echo "- 없음"
fi
for n in ${ISSUES}; do
  echo "- #${n} $(gh issue view "${n}" --json title --jq .title)"
done
echo

echo "## 변경 커밋"
echo
git log "${RANGE}" --no-merges --format='- %s (`%h`)'
echo

echo "## 테스트 결과"
echo
echo '```'
cat "${PYTEST_SUMMARY}"
echo '```'
echo

echo "## 시스템 테스트"
echo
if [ -f docs/test-cases/summary.md ]; then
  cat docs/test-cases/summary.md
else
  echo "- 이번 릴리즈에는 시스템 테스트 결과가 없습니다."
fi
echo

echo "## 산출물 체크섬 (SHA-256)"
echo
echo "| 파일 | SHA-256 |"
echo "|---|---|"
while read -r sum file; do
  echo "| \`${file#\*}\` | \`${sum}\` |"  # 바이너리 모드 표시(*) 제거
done < "${CHECKSUMS}"
echo
echo "검증: \`sha256sum -c SHA256SUMS.txt\`"
