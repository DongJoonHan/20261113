"""서비스 계층 테스트 (#10)."""

from datetime import datetime

import pytest

from pytest_report_viewer.service import ReportService
from pytest_report_viewer.storage import RunMeta, RunNotFoundError, RunStore

XML = b'<testsuite><testcase classname="m" name="ok" time="1" /></testsuite>'


@pytest.fixture
def service(tmp_path) -> ReportService:
    """임시 저장소를 쓰는 서비스."""
    return ReportService(RunStore(tmp_path))


def register(service: ReportService, count: int) -> list[str]:
    """차수를 count개 등록하고 run_id 목록을 반환."""
    return [
        service.register(XML, RunMeta(), now=datetime(2026, 11, 13, 10, 0, i)).run_id
        for i in range(count)
    ]


def test_register_and_get(service):
    record = service.register(XML, RunMeta(branch="main"))
    assert service.get_run(record.run_id) == record


@pytest.mark.parametrize(
    ("limit", "offset", "expected"),
    [
        (10, 0, [3, 2, 1]),  # 최신 차수 먼저
        (1, 0, [3]),
        (2, 1, [2, 1]),
        (10, 3, []),  # offset = 전체 개수
    ],
)
def test_list_runs_newest_first_with_paging(service, limit, offset, expected):
    register(service, 3)
    page = service.list_runs(limit=limit, offset=offset)
    assert page.total == 3
    assert [r.seq for r in page.items] == expected


def test_list_tests(service):
    (run_id,) = register(service, 1)
    assert [c.name for c in service.list_tests(run_id)] == ["ok"]


def test_delete_run(service):
    (run_id,) = register(service, 1)
    service.delete_run(run_id)
    with pytest.raises(RunNotFoundError):
        service.get_run(run_id)


def test_trend(service):
    register(service, 3)
    assert [p.seq for p in service.trend(limit=2)] == [2, 3]
