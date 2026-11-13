"""@brief pytest JUnit XML 결과 파서.

@details `pytest --junitxml=report.xml`로 만든 파일을 CaseResult 목록으로 바꾼다.
루트는 <testsuites> 또는 <testsuite>를 모두 지원한다.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pytest_report_viewer.models import CaseResult, Status

## 결과 하위 태그와 상태의 대응 (먼저 나온 태그를 사용)
_OUTCOME_TAGS = {
    "failure": Status.FAILED,
    "error": Status.ERROR,
    "skipped": Status.SKIPPED,
}

## 허용하는 루트 태그
_ROOT_TAGS = ("testsuites", "testsuite")


class ReportParseError(ValueError):
    """@brief 결과 파일을 해석할 수 없을 때 발생하는 예외."""


def parse_junit_xml(content: str | bytes) -> list[CaseResult]:
    """@brief JUnit XML 문자열을 테스트 케이스 결과 목록으로 변환한다.

    @param content XML 내용 (str 또는 bytes).
    @return 문서 순서대로 정렬된 CaseResult 목록.
    @throws ReportParseError XML 문법 오류, 지원하지 않는 루트, 잘못된 속성일 때.
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ReportParseError(f"XML 파싱 실패: {exc}") from exc
    if root.tag not in _ROOT_TAGS:
        raise ReportParseError(f"지원하지 않는 root 태그: <{root.tag}>")
    # testsuite가 중첩될 수 있으므로 모든 하위 testcase를 순회한다.
    return [_parse_case(element) for element in root.iter("testcase")]


def _parse_case(element: ET.Element) -> CaseResult:
    """@brief <testcase> 요소 하나를 CaseResult로 변환한다.

    @param element <testcase> XML 요소.
    @return 변환된 CaseResult.
    @throws ReportParseError name 누락 또는 time 값 오류.
    """
    name = element.get("name")
    if not name:
        raise ReportParseError("testcase에 name 속성이 없습니다")
    classname = element.get("classname", "")
    status, outcome = _find_outcome(element)
    return CaseResult(
        nodeid=f"{classname}::{name}" if classname else name,
        classname=classname,
        name=name,
        status=status,
        duration=_parse_time(element.get("time", "0")),
        # 성공한 테스트는 outcome 요소가 없으므로 빈 문자열로 둔다.
        message=outcome.get("message", "") if outcome is not None else "",
        details=(outcome.text or "") if outcome is not None else "",
    )


def _find_outcome(element: ET.Element) -> tuple[Status, ET.Element | None]:
    """@brief testcase의 결과 하위 요소를 찾아 상태를 결정한다.

    @param element <testcase> XML 요소.
    @return (상태, 결과 요소). 결과 요소가 없으면 (PASSED, None).
    """
    for child in element:
        if child.tag in _OUTCOME_TAGS:
            return _OUTCOME_TAGS[child.tag], child
    return Status.PASSED, None


def _parse_time(value: str) -> float:
    """@brief time 속성을 초 단위 실수로 변환한다.

    @param value time 속성 문자열.
    @return 실행 시간(초).
    @throws ReportParseError 숫자가 아닐 때.
    """
    try:
        return float(value)
    except ValueError as exc:
        raise ReportParseError(f"잘못된 time 값: {value!r}") from exc
