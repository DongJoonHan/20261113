"""REST API 테스트 (#10)."""

import pytest
from fastapi.testclient import TestClient

from pytest_report_viewer.app import create_app

API = "/api/v1"
XML = b"""<testsuite>
  <testcase classname="m" name="ok" time="1" />
  <testcase classname="m" name="bad" time="1"><failure message="x">tb</failure></testcase>
</testsuite>"""
LIMIT = 1024  # 테스트용 업로드 최대 크기(바이트)
UNKNOWN_RUN = "0009_20261113-142530"


@pytest.fixture
def client(tmp_path) -> TestClient:
    """임시 결과 폴더를 쓰는 API 클라이언트."""
    return TestClient(create_app(results_dir=tmp_path, max_upload_bytes=LIMIT))


def upload(client: TestClient, content: bytes = XML, **form: str):
    """결과 파일 업로드 요청."""
    files = {"file": ("report.xml", content, "application/xml")}
    return client.post(f"{API}/runs", files=files, data=form)


# ------------------------------------------------------------------ POST /runs


def test_upload_creates_run(client):
    res = upload(client, branch="main", commit="abc")
    assert res.status_code == 201
    body = res.json()
    assert res.headers["location"] == f"{API}/runs/{body['run_id']}"
    assert body["seq"] == 1
    assert body["meta"] == {"branch": "main", "commit": "abc"}
    assert body["summary"]["passed"] == 1
    assert body["summary"]["failed"] == 1
    assert body["summary"]["pass_rate"] == 50.0


def test_upload_without_meta_uses_empty_strings(client):
    assert upload(client).json()["meta"] == {"branch": "", "commit": ""}


@pytest.mark.parametrize("content", [b"", b"not xml", b"<report />"])
def test_upload_invalid_report_returns_422(client, content):
    res = upload(client, content)
    assert res.status_code == 422
    assert "detail" in res.json()
    assert client.get(f"{API}/runs").json()["total"] == 0


def test_upload_without_file_returns_422(client):
    assert client.post(f"{API}/runs", data={"branch": "main"}).status_code == 422


def test_upload_size_boundary(client):
    padding = b"<!--" + b"x" * (LIMIT - len(XML) - 7) + b"-->"
    exact = XML + padding
    assert len(exact) == LIMIT
    assert upload(client, exact).status_code == 201
    res = upload(client, exact + b" ")
    assert res.status_code == 413
    assert "detail" in res.json()


# ------------------------------------------------------------------ GET /runs


def test_list_runs_empty(client):
    assert client.get(f"{API}/runs").json() == {"total": 0, "items": []}


def test_list_runs_newest_first_with_paging(client):
    for _ in range(3):
        upload(client)
    body = client.get(f"{API}/runs", params={"limit": 2, "offset": 1}).json()
    assert body["total"] == 3
    assert [r["seq"] for r in body["items"]] == [2, 1]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 1001}, {"offset": -1}, {"limit": "x"}])
def test_list_runs_invalid_paging_returns_422(client, params):
    assert client.get(f"{API}/runs", params=params).status_code == 422


@pytest.mark.parametrize("params", [{"limit": 1}, {"limit": 1000}, {"offset": 0}])
def test_list_runs_paging_boundaries_accepted(client, params):
    assert client.get(f"{API}/runs", params=params).status_code == 200


# ------------------------------------------------------------------ GET/DELETE /runs/{id}


def test_get_run(client):
    run_id = upload(client).json()["run_id"]
    body = client.get(f"{API}/runs/{run_id}").json()
    assert body["run_id"] == run_id
    assert body["summary"]["total"] == 2


def test_delete_run(client):
    run_id = upload(client).json()["run_id"]
    res = client.delete(f"{API}/runs/{run_id}")
    assert res.status_code == 204
    assert client.get(f"{API}/runs/{run_id}").status_code == 404


@pytest.mark.parametrize("run_id", [UNKNOWN_RUN, "..", "bad-id"])
@pytest.mark.parametrize("method", ["get", "delete"])
def test_unknown_run_returns_404(client, run_id, method):
    res = getattr(client, method)(f"{API}/runs/{run_id}")
    assert res.status_code == 404
    assert "detail" in res.json()


# ------------------------------------------------------------------ GET /runs/{id}/tests


def test_list_tests(client):
    run_id = upload(client).json()["run_id"]
    body = client.get(f"{API}/runs/{run_id}/tests").json()
    assert body["run_id"] == run_id
    assert [(t["name"], t["status"]) for t in body["items"]] == [
        ("ok", "passed"),
        ("bad", "failed"),
    ]
    assert body["items"][1]["message"] == "x"


def test_list_tests_unknown_run_returns_404(client):
    assert client.get(f"{API}/runs/{UNKNOWN_RUN}/tests").status_code == 404


# ------------------------------------------------------------------ GET /trend


def test_trend(client):
    for _ in range(3):
        upload(client)
    body = client.get(f"{API}/trend", params={"limit": 2}).json()
    assert [p["seq"] for p in body["items"]] == [2, 3]
    assert body["items"][0]["pass_rate"] == 50.0


def test_trend_without_limit_and_empty(client):
    assert client.get(f"{API}/trend").json() == {"items": []}


@pytest.mark.parametrize("limit", [0, -1, "x"])
def test_trend_invalid_limit_returns_422(client, limit):
    assert client.get(f"{API}/trend", params={"limit": limit}).status_code == 422


# ------------------------------------------------------------------ OpenAPI


def test_openapi_lists_all_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {
        f"{API}/runs",
        f"{API}/runs/{{run_id}}",
        f"{API}/runs/{{run_id}}/tests",
        f"{API}/trend",
    }
    assert set(paths[f"{API}/runs"]) == {"get", "post"}
    assert set(paths[f"{API}/runs/{{run_id}}"]) == {"get", "delete"}
