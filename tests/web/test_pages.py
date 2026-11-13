"""웹 페이지 테스트 (#2)."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from pytest_report_viewer.app import create_app

XML_MIXED = b"""<testsuite>
  <testcase classname="m" name="ok" time="0.5" />
  <testcase classname="m" name="bad" time="0.25">
    <failure message="assert 1 == 2">tb</failure>
  </testcase>
  <testcase classname="m" name="err" time="0"><error message="fixture">tb</error></testcase>
  <testcase classname="m" name="skip" time="0"><skipped message="later" /></testcase>
</testsuite>"""
XML_ALL_PASS = b'<testsuite><testcase classname="m" name="ok" time="1" /></testsuite>'
UNKNOWN_RUN = "0009_20261113-142530"


@pytest.fixture
def client(tmp_path) -> TestClient:
    """임시 결과 폴더를 쓰는 클라이언트."""
    return TestClient(create_app(results_dir=tmp_path))


def upload(client: TestClient, content: bytes, commit: str = "") -> str:
    """API로 차수를 등록하고 run_id 반환."""
    files = {"file": ("r.xml", content, "application/xml")}
    return client.post("/api/v1/runs", files=files, data={"commit": commit}).json()["run_id"]


def trend_data(html: str) -> list[dict]:
    """페이지에 포함된 트렌드 JSON을 꺼낸다."""
    match = re.search(r'<script id="trend-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(match.group(1))


# ------------------------------------------------------------------ 차수 목록 /


def test_index_without_runs_shows_empty_message(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/html")
    assert "등록된 차수가 없습니다" in res.text
    assert trend_data(res.text) == []


def test_index_lists_runs_newest_first_with_links(client):
    first = upload(client, XML_MIXED, commit="c1")
    second = upload(client, XML_ALL_PASS, commit="c2")
    html = client.get("/").text
    table = html[html.index("<table") :]  # 트렌드 JSON(차수 순)은 제외하고 표만 본다
    assert table.index(second) < table.index(first)
    assert f'href="/runs/{first}"' in html
    assert "33.3%" in html  # 1 / (4 - 1 skipped)
    assert "100.0%" in html


def test_index_embeds_trend_in_run_order(client):
    upload(client, XML_MIXED)
    upload(client, XML_ALL_PASS)
    points = trend_data(client.get("/").text)
    assert [p["seq"] for p in points] == [1, 2]
    assert [p["failed"] for p in points] == [1, 0]


# ------------------------------------------------------------------ 차수 상세 /runs/{id}


def test_run_page_shows_summary_and_every_test(client):
    run_id = upload(client, XML_MIXED, commit="abc123")
    res = client.get(f"/runs/{run_id}")
    assert res.status_code == 200
    html = res.text
    assert run_id in html
    assert "abc123" in html
    for name in ("m::ok", "m::bad", "m::err", "m::skip"):
        assert name in html
    assert "assert 1 == 2" in html


@pytest.mark.parametrize("status", ["passed", "failed", "error", "skipped"])
def test_run_page_marks_each_status(client, status):
    run_id = upload(client, XML_MIXED)
    assert f'class="status status-{status}"' in client.get(f"/runs/{run_id}").text


def test_run_page_escapes_html_in_results(client):
    xml = (
        b'<testsuite><testcase classname="m" name="t">'
        b'<failure message="&lt;script&gt;x&lt;/script&gt;" />'
        b"</testcase></testsuite>"
    )
    run_id = upload(client, xml)
    html = client.get(f"/runs/{run_id}").text
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;x&lt;/script&gt;" in html


def test_unknown_run_page_returns_html_404(client):
    res = client.get(f"/runs/{UNKNOWN_RUN}")
    assert res.status_code == 404
    assert res.headers["content-type"].startswith("text/html")
    assert "차수를 찾을 수 없습니다" in res.text


def test_api_404_stays_json(client):
    res = client.get(f"/api/v1/runs/{UNKNOWN_RUN}")
    assert res.status_code == 404
    assert res.headers["content-type"].startswith("application/json")
