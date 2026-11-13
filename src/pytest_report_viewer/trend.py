"""@brief 차수 간 트렌드 집계.

@details 저장된 차수 목록을 차트에 바로 쓸 수 있는 점(point) 목록으로 바꾼다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from pytest_report_viewer.storage import RunRecord


@dataclass(frozen=True)
class TrendPoint:
    """@brief 트렌드 차트의 점 하나 (차수 하나).

    @param run_id 차수 폴더 이름.
    @param seq 차수 순번.
    @param created_at 등록 시각 (ISO 8601).
    @param commit 실행 커밋 (없으면 빈 문자열).
    @param total 전체 테스트 수.
    @param passed 성공 수.
    @param failed 실패 수.
    @param errors 에러 수.
    @param skipped 스킵 수.
    @param duration 실행 시간 합(초).
    @param pass_rate 성공률(%, 스킵 제외).
    """

    run_id: str
    seq: int
    created_at: str
    commit: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float
    pass_rate: float

    def to_dict(self) -> dict:
        """@brief JSON 직렬화용 dict로 변환한다.

        @return 모든 필드를 담은 dict.
        """
        return asdict(self)


def build_trend(records: list[RunRecord], limit: int | None = None) -> list[TrendPoint]:
    """@brief 차수 목록을 차수 순 트렌드 점 목록으로 만든다.

    @param records 저장된 차수 목록 (순서 무관).
    @param limit 최신 N개 차수만 사용 (None이면 전체).
    @return 차수 순번 오름차순의 TrendPoint 목록.
    @throws ValueError limit이 1보다 작을 때.
    """
    if limit is not None and limit < 1:
        raise ValueError(f"limit은 1 이상이어야 합니다: {limit}")
    ordered = sorted(records, key=lambda record: record.seq)
    # 최신 차수가 뒤에 있으므로 뒤에서 limit개를 자른다.
    selected = ordered[-limit:] if limit else ordered
    return [_to_point(record) for record in selected]


def _to_point(record: RunRecord) -> TrendPoint:
    """@brief 차수 정보 하나를 트렌드 점으로 변환한다.

    @param record 차수 정보.
    @return 변환된 TrendPoint.
    """
    summary = record.summary
    return TrendPoint(
        run_id=record.run_id,
        seq=record.seq,
        created_at=record.created_at,
        commit=record.meta.commit,
        total=summary.total,
        passed=summary.passed,
        failed=summary.failed,
        errors=summary.errors,
        skipped=summary.skipped,
        duration=summary.duration,
        pass_rate=summary.pass_rate,
    )
