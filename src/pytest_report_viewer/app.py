"""@brief FastAPI 앱 생성.

@details 실행: `uvicorn pytest_report_viewer.app:app`
결과 폴더는 환경 변수 PRV_RESULTS_DIR로 지정한다 (기본 ./results).
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pytest_report_viewer.api.routes import router as api_router
from pytest_report_viewer.parser import ReportParseError
from pytest_report_viewer.service import ReportService
from pytest_report_viewer.storage import RunNotFoundError, RunStore

## 업로드 파일 최대 크기 기본값 (10 MiB)
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def create_app(
    results_dir: Path | None = None, max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
) -> FastAPI:
    """@brief 앱을 만들고 서비스와 라우트를 등록한다.

    @param results_dir 결과 루트 폴더 (None이면 PRV_RESULTS_DIR 또는 ./results).
    @param max_upload_bytes 업로드 파일 최대 크기(바이트).
    @return 설정이 끝난 FastAPI 앱.
    """
    root = results_dir or Path(os.environ.get("PRV_RESULTS_DIR", "results"))
    app = FastAPI(title="Pytest Report Viewer", version="0.1.0")
    app.state.service = ReportService(RunStore(root))
    app.state.max_upload_bytes = max_upload_bytes
    app.include_router(api_router)
    # 도메인 예외를 HTTP 오류 응답으로 변환한다.
    app.add_exception_handler(RunNotFoundError, _not_found)
    app.add_exception_handler(ReportParseError, _unprocessable)
    return app


async def _not_found(_: Request, exc: Exception) -> JSONResponse:
    """@brief RunNotFoundError → 404.

    @param exc 발생한 예외.
    @return {"detail": 메시지} 404 응답.
    """
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def _unprocessable(_: Request, exc: Exception) -> JSONResponse:
    """@brief ReportParseError → 422.

    @param exc 발생한 예외.
    @return {"detail": 메시지} 422 응답.
    """
    return JSONResponse(status_code=422, content={"detail": str(exc)})


## uvicorn 진입점
app = create_app()
