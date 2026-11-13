"""차수별 결과 저장소 테스트 (#3)."""

import json
from datetime import datetime

import pytest

from pytest_report_viewer.models import RunSummary, Status
from pytest_report_viewer.parser import ReportParseError
from pytest_report_viewer.storage import RunMeta, RunNotFoundError, RunStore

XML = b"""<testsuite>
  <testcase classname="m" name="ok" time="1.0" />
  <testcase classname="m" name="bad" time="0.5"><failure message="x">tb</failure></testcase>
</testsuite>"""

T1 = datetime(2026, 11, 13, 14, 25, 30)
T2 = datetime(2026, 11, 13, 15, 0, 0)


@pytest.fixture
def store(tmp_path) -> RunStore:
    """임시 폴더를 쓰는 저장소."""
    return RunStore(tmp_path / "results")


def test_save_creates_numbered_run_folder(store):
    record = store.save(XML, RunMeta(branch="main", commit="abc123"), now=T1)
    assert record.run_id == "0001_20261113-142530"
    assert record.seq == 1
    assert record.created_at == "2026-11-13T14:25:30"
    assert record.meta == RunMeta(branch="main", commit="abc123")
    folder = store.root / record.run_id
    assert (folder / "report.xml").read_bytes() == XML
    saved = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    assert saved["summary"]["failed"] == 1


def test_save_computes_summary(store):
    record = store.save(XML, now=T1)
    assert record.summary == RunSummary(
        total=2, passed=1, failed=1, errors=0, skipped=0, duration=1.5
    )
    assert record.meta == RunMeta()


def test_sequence_increments(store):
    store.save(XML, now=T1)
    second = store.save(XML, now=T2)
    assert second.run_id == "0002_20261113-150000"


def test_list_runs_sorted_by_sequence(store):
    store.save(XML, now=T2)
    store.save(XML, now=T1)
    assert [r.seq for r in store.list_runs()] == [1, 2]


def test_list_runs_empty_when_root_missing(store):
    assert store.list_runs() == []


def test_list_runs_ignores_unrelated_entries(store):
    store.save(XML, now=T1)
    (store.root / "notes").mkdir()
    (store.root / ".gitkeep").write_text("")
    assert [r.run_id for r in store.list_runs()] == ["0001_20261113-142530"]


def test_get_returns_saved_record(store):
    saved = store.save(XML, RunMeta(commit="c1"), now=T1)
    assert store.get(saved.run_id) == saved


def test_load_cases_reads_report(store):
    record = store.save(XML, now=T1)
    cases = store.load_cases(record.run_id)
    assert [c.status for c in cases] == [Status.PASSED, Status.FAILED]


def test_delete_removes_folder(store):
    record = store.save(XML, now=T1)
    store.delete(record.run_id)
    assert not (store.root / record.run_id).exists()
    assert store.list_runs() == []


@pytest.mark.parametrize("bad", [b"", b"not xml", b"<report />"])
def test_invalid_report_is_not_saved(store, bad):
    with pytest.raises(ReportParseError):
        store.save(bad, now=T1)
    assert store.list_runs() == []


@pytest.mark.parametrize(
    "run_id",
    [
        "0009_20261113-142530",  # 형식은 맞지만 없음
        "../outside",  # 경로 탈출 시도
        "0001_20261113-142530/../../x",
        "",
    ],
)
def test_unknown_or_invalid_run_id(store, run_id):
    store.save(XML, now=T1)
    with pytest.raises(RunNotFoundError):
        store.get(run_id)
    with pytest.raises(RunNotFoundError):
        store.load_cases(run_id)
    with pytest.raises(RunNotFoundError):
        store.delete(run_id)


def test_save_uses_current_time_by_default(store):
    record = store.save(XML)
    assert datetime.fromisoformat(record.created_at) <= datetime.now()
