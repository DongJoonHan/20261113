"""결과 모델과 요약 계산 테스트 (#1)."""

import pytest

from pytest_report_viewer.models import CaseResult, RunSummary, Status, summarize


def make_case(status: Status, duration: float = 1.0) -> CaseResult:
    """테스트용 CaseResult 생성."""
    return CaseResult(
        nodeid=f"m::{status.value}",
        classname="m",
        name=status.value,
        status=status,
        duration=duration,
    )


def test_status_values():
    assert [s.value for s in Status] == ["passed", "failed", "error", "skipped"]


def test_case_defaults_are_empty_strings():
    case = make_case(Status.PASSED)
    assert case.message == ""
    assert case.details == ""


def test_summarize_counts_each_status():
    cases = [
        make_case(Status.PASSED, 1.0),
        make_case(Status.PASSED, 2.0),
        make_case(Status.FAILED, 0.5),
        make_case(Status.ERROR, 0.25),
        make_case(Status.SKIPPED, 0.0),
    ]
    summary = summarize(cases)
    assert summary == RunSummary(
        total=5, passed=2, failed=1, errors=1, skipped=1, duration=pytest.approx(3.75)
    )


def test_pass_rate_excludes_skipped():
    summary = RunSummary(total=4, passed=2, failed=1, errors=0, skipped=1, duration=0.0)
    assert summary.pass_rate == pytest.approx(2 / 3 * 100)


def test_pass_rate_is_zero_when_nothing_executed():
    assert summarize([]).pass_rate == 0.0
    only_skipped = summarize([make_case(Status.SKIPPED)])
    assert only_skipped.pass_rate == 0.0


def test_summary_to_dict():
    summary = RunSummary(total=2, passed=1, failed=1, errors=0, skipped=0, duration=1.5)
    assert summary.to_dict() == {
        "total": 2,
        "passed": 1,
        "failed": 1,
        "errors": 0,
        "skipped": 0,
        "duration": 1.5,
        "pass_rate": 50.0,
    }


def test_summary_from_dict_roundtrip():
    summary = RunSummary(total=2, passed=1, failed=1, errors=0, skipped=0, duration=1.5)
    assert RunSummary.from_dict(summary.to_dict()) == summary


def test_case_to_dict_and_back():
    case = CaseResult("m::t", "m", "t", Status.FAILED, 0.5, "msg", "trace")
    data = case.to_dict()
    assert data["status"] == "failed"
    assert CaseResult.from_dict(data) == case
