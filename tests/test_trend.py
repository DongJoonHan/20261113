"""차수 간 트렌드 집계 테스트 (#4)."""

import pytest

from pytest_report_viewer.models import RunSummary
from pytest_report_viewer.storage import RunMeta, RunRecord
from pytest_report_viewer.trend import TrendPoint, build_trend


def make_record(seq: int, passed: int, failed: int, skipped: int = 0) -> RunRecord:
    """테스트용 차수 정보 생성."""
    total = passed + failed + skipped
    return RunRecord(
        run_id=f"{seq:04d}_20261113-1000{seq:02d}",
        seq=seq,
        created_at=f"2026-11-13T10:00:{seq:02d}",
        summary=RunSummary(total, passed, failed, 0, skipped, duration=float(seq)),
        meta=RunMeta(commit=f"c{seq}"),
    )


RECORDS = [make_record(1, 8, 2), make_record(2, 9, 1), make_record(3, 10, 0, skipped=2)]


def test_no_runs_gives_empty_trend():
    assert build_trend([]) == []


def test_single_run():
    (point,) = build_trend(RECORDS[:1])
    assert point == TrendPoint(
        run_id="0001_20261113-100001",
        seq=1,
        created_at="2026-11-13T10:00:01",
        commit="c1",
        total=10,
        passed=8,
        failed=2,
        errors=0,
        skipped=0,
        duration=1.0,
        pass_rate=80.0,
    )


def test_points_follow_run_order_even_if_input_unsorted():
    trend = build_trend([RECORDS[2], RECORDS[0], RECORDS[1]])
    assert [p.seq for p in trend] == [1, 2, 3]
    assert [p.pass_rate for p in trend] == [80.0, 90.0, 100.0]


@pytest.mark.parametrize(
    ("limit", "expected_seqs"),
    [
        (1, [3]),  # 최소값: 최신 1개
        (2, [2, 3]),
        (3, [1, 2, 3]),  # 차수 수와 같음
        (4, [1, 2, 3]),  # 차수 수 초과
        (None, [1, 2, 3]),  # 제한 없음
    ],
)
def test_limit_keeps_latest_runs(limit, expected_seqs):
    assert [p.seq for p in build_trend(RECORDS, limit=limit)] == expected_seqs


@pytest.mark.parametrize("limit", [0, -1])
def test_limit_must_be_positive(limit):
    with pytest.raises(ValueError, match="limit"):
        build_trend(RECORDS, limit=limit)


def test_point_to_dict():
    data = build_trend(RECORDS[:1])[0].to_dict()
    assert data["run_id"] == "0001_20261113-100001"
    assert data["pass_rate"] == 80.0
    assert set(data) == {
        "run_id",
        "seq",
        "created_at",
        "commit",
        "total",
        "passed",
        "failed",
        "errors",
        "skipped",
        "duration",
        "pass_rate",
    }
