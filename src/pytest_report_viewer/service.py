"""@brief REST API와 웹 화면이 함께 쓰는 서비스 계층.

@details 라우트는 요청/응답 변환만 하고, 조회·등록 로직은 모두 이 계층에 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pytest_report_viewer.models import CaseResult
from pytest_report_viewer.storage import RunMeta, RunRecord, RunStore
from pytest_report_viewer.trend import TrendPoint, build_trend


@dataclass(frozen=True)
class RunPage:
    """@brief 차수 목록 한 페이지.

    @param total 전체 차수 수.
    @param items 이 페이지의 차수 (최신순).
    """

    total: int
    items: list[RunRecord]


class ReportService:
    """@brief 차수 등록·조회·삭제와 트렌드 계산을 제공한다."""

    def __init__(self, store: RunStore) -> None:
        """@brief 서비스를 만든다.

        @param store 차수 저장소.
        """
        self.store = store

    def register(self, report: bytes, meta: RunMeta, now: datetime | None = None) -> RunRecord:
        """@brief 결과 파일을 새 차수로 등록한다.

        @param report JUnit XML 원본.
        @param meta 실행 환경 정보.
        @param now 등록 시각 (테스트용).
        @return 등록된 차수.
        @throws ReportParseError 결과 파일을 해석할 수 없을 때.
        """
        return self.store.save(report, meta, now=now)

    def list_runs(self, limit: int, offset: int) -> RunPage:
        """@brief 차수 목록을 최신순으로 페이지 단위로 반환한다.

        @param limit 페이지 크기.
        @param offset 건너뛸 차수 수.
        @return 전체 개수와 해당 페이지 차수.
        """
        runs = list(reversed(self.store.list_runs()))
        return RunPage(total=len(runs), items=runs[offset : offset + limit])

    def get_run(self, run_id: str) -> RunRecord:
        """@brief 차수 하나를 조회한다.

        @param run_id 차수 ID.
        @return 차수 정보.
        @throws RunNotFoundError 없는 차수.
        """
        return self.store.get(run_id)

    def list_tests(self, run_id: str) -> list[CaseResult]:
        """@brief 차수의 테스트 케이스 결과를 반환한다.

        @param run_id 차수 ID.
        @return 테스트 케이스 결과 목록 (결과 파일 순서).
        @throws RunNotFoundError 없는 차수.
        """
        return self.store.load_cases(run_id)

    def delete_run(self, run_id: str) -> None:
        """@brief 차수를 삭제한다.

        @param run_id 차수 ID.
        @throws RunNotFoundError 없는 차수.
        """
        self.store.delete(run_id)

    def trend(self, limit: int | None = None) -> list[TrendPoint]:
        """@brief 차수별 트렌드를 계산한다.

        @param limit 최신 N개 차수만 사용 (None이면 전체).
        @return 차수 순 트렌드 점 목록.
        """
        return build_trend(self.store.list_runs(), limit=limit)
