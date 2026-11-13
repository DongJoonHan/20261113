"""JUnit XML 파서 테스트 (#1)."""

import pytest

from pytest_report_viewer.models import CaseResult, Status
from pytest_report_viewer.parser import ReportParseError, parse_junit_xml

SUITE_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="5">
    <testcase classname="tests.test_a" name="test_ok" time="0.010" />
    <testcase classname="tests.test_a" name="test_fail" time="0.020">
      <failure message="assert 1 == 2">trace-fail</failure>
    </testcase>
    <testcase classname="tests.test_a" name="test_err" time="0.030">
      <error message="fixture error">trace-error</error>
    </testcase>
    <testcase classname="tests.test_a" name="test_skip" time="0">
      <skipped message="not ready" />
    </testcase>
    <testcase name="test_no_class" />
  </testsuite>
</testsuites>
"""


@pytest.fixture
def cases() -> list[CaseResult]:
    """샘플 XML을 파싱한 결과."""
    return parse_junit_xml(SUITE_XML)


def test_parses_all_testcases(cases):
    assert len(cases) == 5


def test_passed_case(cases):
    case = cases[0]
    assert case.nodeid == "tests.test_a::test_ok"
    assert case.classname == "tests.test_a"
    assert case.name == "test_ok"
    assert case.status is Status.PASSED
    assert case.duration == pytest.approx(0.01)
    assert case.message == ""
    assert case.details == ""


def test_failed_case_keeps_message_and_trace(cases):
    case = cases[1]
    assert case.status is Status.FAILED
    assert case.message == "assert 1 == 2"
    assert case.details == "trace-fail"


def test_error_case(cases):
    case = cases[2]
    assert case.status is Status.ERROR
    assert case.message == "fixture error"
    assert case.details == "trace-error"


def test_skipped_case_without_text(cases):
    case = cases[3]
    assert case.status is Status.SKIPPED
    assert case.message == "not ready"
    assert case.details == ""


def test_case_without_classname_or_time(cases):
    case = cases[4]
    assert case.nodeid == "test_no_class"
    assert case.classname == ""
    assert case.duration == 0.0


def test_single_testsuite_root():
    xml = '<testsuite><testcase classname="m" name="t" time="1.5" /></testsuite>'
    (case,) = parse_junit_xml(xml)
    assert case.nodeid == "m::t"
    assert case.duration == pytest.approx(1.5)


def test_ignores_non_outcome_children():
    xml = """<testsuite>
      <testcase classname="m" name="out_only"><system-out>log</system-out></testcase>
      <testcase classname="m" name="out_then_fail">
        <system-out>log</system-out><failure message="boom">tb</failure>
      </testcase>
    </testsuite>"""
    out_only, out_then_fail = parse_junit_xml(xml)
    assert out_only.status is Status.PASSED
    assert out_then_fail.status is Status.FAILED
    assert out_then_fail.message == "boom"


def test_accepts_bytes():
    xml = b'<testsuite><testcase classname="m" name="t" /></testsuite>'
    assert len(parse_junit_xml(xml)) == 1


def test_empty_suite_returns_empty_list():
    assert parse_junit_xml("<testsuites />") == []


@pytest.mark.parametrize(
    "xml",
    [
        "",
        "not xml",
        "<testsuite><testcase></testsuite>",
    ],
)
def test_malformed_xml_raises(xml):
    with pytest.raises(ReportParseError, match="XML"):
        parse_junit_xml(xml)


def test_unknown_root_raises():
    with pytest.raises(ReportParseError, match="root"):
        parse_junit_xml("<report />")


def test_invalid_time_raises():
    xml = '<testsuite><testcase name="t" time="abc" /></testsuite>'
    with pytest.raises(ReportParseError, match="time"):
        parse_junit_xml(xml)


def test_testcase_without_name_raises():
    with pytest.raises(ReportParseError, match="name"):
        parse_junit_xml('<testsuite><testcase classname="m" /></testsuite>')
