"""@brief REST API 라우트 (/api/v1).

@details 요청 검증과 응답 변환만 담당한다. 로직은 ReportService에 있다.
도메인 예외(ReportParseError, RunNotFoundError)는 app.py의 핸들러가 HTTP 오류로 바꾼다.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse

from pytest_report_viewer.service import ReportService
from pytest_report_viewer.storage import RunMeta

## API 경로 접두어
API_PREFIX = "/api/v1"

router = APIRouter(prefix=API_PREFIX, tags=["runs"])


def get_service(request: Request) -> ReportService:
    """@brief 앱 상태에서 서비스 객체를 꺼낸다 (의존성 주입용).

    @param request 현재 요청.
    @return 앱에 등록된 ReportService.
    """
    return request.app.state.service


## 라우트 함수에서 쓰는 서비스 의존성 타입
ServiceDep = Annotated[ReportService, Depends(get_service)]


def meta_form(
    branch: Annotated[str, Form(description="실행 브랜치")] = "",
    commit: Annotated[str, Form(description="실행 커밋 해시")] = "",
) -> RunMeta:
    """@brief 업로드 폼의 선택 필드로 실행 환경 정보를 만든다.

    @param branch 실행 브랜치.
    @param commit 실행 커밋 해시.
    @return RunMeta.
    """
    return RunMeta(branch=branch, commit=commit)


## 업로드 폼에서 만든 실행 환경 정보 의존성 타입
MetaDep = Annotated[RunMeta, Depends(meta_form)]


@router.post("/runs", status_code=201)
async def create_run(
    request: Request,
    service: ServiceDep,
    file: Annotated[UploadFile, File(description="pytest --junitxml 결과 파일")],
    meta: MetaDep,
) -> JSONResponse:
    """@brief 결과 파일을 업로드해 새 차수를 만든다.

    @return 생성된 차수 (201, Location 헤더 포함).
    @throws HTTPException 413 업로드 크기 초과.
    """
    limit = request.app.state.max_upload_bytes
    # 한도보다 1바이트 더 읽어 초과 여부만 판단한다 (전체를 메모리에 올리지 않음).
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(status_code=413, detail=f"파일이 {limit}바이트를 초과합니다")
    record = service.register(content, meta)
    location = f"{API_PREFIX}/runs/{record.run_id}"
    return JSONResponse(record.to_dict(), status_code=201, headers={"Location": location})


@router.get("/runs")
def list_runs(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    """@brief 차수 목록을 최신순으로 조회한다.

    @return {"total": 전체 수, "items": 차수 목록}.
    """
    page = service.list_runs(limit=limit, offset=offset)
    return {"total": page.total, "items": [record.to_dict() for record in page.items]}


@router.get("/runs/{run_id}")
def get_run(run_id: str, service: ServiceDep) -> dict:
    """@brief 차수 하나의 요약과 메타데이터를 조회한다.

    @return 차수 정보.
    """
    return service.get_run(run_id).to_dict()


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: str, service: ServiceDep) -> Response:
    """@brief 차수를 삭제한다.

    @return 빈 응답 (204).
    """
    service.delete_run(run_id)
    return Response(status_code=204)


@router.get("/runs/{run_id}/tests")
def list_tests(run_id: str, service: ServiceDep) -> dict:
    """@brief 차수의 테스트 케이스 결과 목록을 조회한다.

    @return {"run_id": 차수 ID, "items": 테스트 케이스 목록}.
    """
    cases = service.list_tests(run_id)
    return {"run_id": run_id, "items": [case.to_dict() for case in cases]}


@router.get("/trend")
def get_trend(
    service: ServiceDep,
    limit: Annotated[int | None, Query(ge=1)] = None,
) -> dict:
    """@brief 차수별 트렌드 데이터를 조회한다.

    @return {"items": 차수 순 트렌드 점 목록}.
    """
    return {"items": [point.to_dict() for point in service.trend(limit=limit)]}
