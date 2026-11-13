"""@brief 테스트 결과 데이터 모델.

@details 파서, 저장소, API가 함께 사용하는 불변 데이터 구조를 정의한다.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import StrEnum


class Status(StrEnum):
    """@brief 테스트 케이스 하나의 실행 결과 상태."""

    PASSED = "passed"  # 성공
    FAILED = "failed"  # assert 실패
    ERROR = "error"  # fixture/수집 등 테스트 외부 오류
    SKIPPED = "skipped"  # skip, xfail


@dataclass(frozen=True)
class CaseResult:
    """@brief 테스트 케이스 하나의 결과.

    @param nodeid 테스트 식별자 ("classname::name").
    @param classname 테스트가 속한 모듈/클래스 경로.
    @param name 테스트 함수 이름 (파라미터 포함).
    @param status 실행 결과 상태.
    @param duration 실행 시간(초).
    @param message 실패/에러/스킵 메시지.
    @param details 실패/에러 traceback 원문.
    """

    nodeid: str
    classname: str
    name: str
    status: Status
    duration: float
    message: str = ""
    details: str = ""

    def to_dict(self) -> dict:
        """@brief JSON 직렬화용 dict로 변환한다.

        @return status를 문자열로 바꾼 dict.
        """
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> CaseResult:
        """@brief to_dict() 결과로부터 객체를 복원한다.

        @param data to_dict()가 만든 dict.
        @return 복원된 CaseResult.
        """
        return cls(**{**data, "status": Status(data["status"])})


@dataclass(frozen=True)
class RunSummary:
    """@brief 한 차수의 상태별 집계.

    @param total 전체 테스트 수.
    @param passed 성공 수.
    @param failed 실패 수.
    @param errors 에러 수.
    @param skipped 스킵 수.
    @param duration 전체 실행 시간 합(초).
    """

    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float

    @property
    def pass_rate(self) -> float:
        """@brief 성공률(%)을 계산한다.

        @details 스킵은 실행하지 않은 것으로 보고 분모에서 제외한다.
        @return 0~100 사이 값, 실행된 테스트가 없으면 0.
        """
        executed = self.total - self.skipped
        if executed == 0:
            return 0.0
        return self.passed / executed * 100

    def to_dict(self) -> dict:
        """@brief JSON 직렬화용 dict로 변환한다.

        @return 집계 필드와 pass_rate를 담은 dict.
        """
        return {**asdict(self), "pass_rate": self.pass_rate}

    @classmethod
    def from_dict(cls, data: dict) -> RunSummary:
        """@brief to_dict() 결과로부터 객체를 복원한다.

        @param data to_dict()가 만든 dict (pass_rate는 무시).
        @return 복원된 RunSummary.
        """
        fields = ("total", "passed", "failed", "errors", "skipped", "duration")
        return cls(**{key: data[key] for key in fields})


def summarize(cases: list[CaseResult]) -> RunSummary:
    """@brief 테스트 케이스 목록을 상태별로 집계한다.

    @param cases 파싱된 테스트 케이스 목록.
    @return 상태별 개수와 총 실행 시간.
    """
    counts = Counter(case.status for case in cases)
    return RunSummary(
        total=len(cases),
        passed=counts[Status.PASSED],
        failed=counts[Status.FAILED],
        errors=counts[Status.ERROR],
        skipped=counts[Status.SKIPPED],
        duration=sum(case.duration for case in cases),
    )
