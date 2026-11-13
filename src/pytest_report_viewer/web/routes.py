"""@brief 웹 화면 라우트.

@details 데이터는 ReportService에서 가져오고 Jinja2 템플릿으로 렌더링한다.
템플릿은 autoescape가 켜져 있어 결과 파일의 문자열이 HTML로 해석되지 않는다.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pytest_report_viewer.api.routes import ServiceDep

## 템플릿 폴더 (패키지 데이터로 배포)
TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "templates")

## 목록 화면에 표시할 최대 차수 수
MAX_LISTED_RUNS = 1000

# 화면 라우트는 OpenAPI 문서에서 제외한다.
router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, service: ServiceDep) -> HTMLResponse:
    """@brief 차수 목록과 트렌드 차트 화면.

    @return 차수 목록(최신순) 표와 차수 순 트렌드 데이터를 담은 HTML.
    """
    page = service.list_runs(limit=MAX_LISTED_RUNS, offset=0)
    trend = [point.to_dict() for point in service.trend()]
    return TEMPLATES.TemplateResponse(
        request, "index.html", {"runs": page.items, "total": page.total, "trend": trend}
    )


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: str, service: ServiceDep) -> HTMLResponse:
    """@brief 차수 상세 화면 (요약 + 테스트별 성공/실패 표).

    @return 차수 상세 HTML. 없는 차수는 app.py 핸들러가 404 화면으로 바꾼다.
    """
    record = service.get_run(run_id)
    cases = service.list_tests(run_id)
    return TEMPLATES.TemplateResponse(request, "run.html", {"run": record, "cases": cases})


def render_not_found(request: Request, message: str) -> HTMLResponse:
    """@brief 404 화면을 렌더링한다.

    @param request 현재 요청.
    @param message 표시할 오류 메시지.
    @return 상태 코드 404의 HTML 응답.
    """
    return TEMPLATES.TemplateResponse(request, "404.html", {"message": message}, status_code=404)
