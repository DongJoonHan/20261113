"""앱 생성/설정 테스트 (#10)."""

from pathlib import Path

from pytest_report_viewer.app import DEFAULT_MAX_UPLOAD_BYTES, create_app


def test_results_dir_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("PRV_RESULTS_DIR", str(tmp_path / "env"))
    app = create_app()
    assert app.state.service.store.root == tmp_path / "env"


def test_default_results_dir(monkeypatch):
    monkeypatch.delenv("PRV_RESULTS_DIR", raising=False)
    assert create_app().state.service.store.root == Path("results")


def test_default_upload_limit_is_10_mib(tmp_path):
    assert DEFAULT_MAX_UPLOAD_BYTES == 10 * 1024 * 1024
    assert create_app(results_dir=tmp_path).state.max_upload_bytes == DEFAULT_MAX_UPLOAD_BYTES
