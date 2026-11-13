"""@brief 차수별 결과 저장소.

@details 차수 하나를 폴더 하나로 저장한다.
@code
results/
  0001_20261113-142530/
    report.xml     # 업로드한 JUnit XML 원본
    summary.json   # 메타데이터 + 상태별 집계
@endcode
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from pytest_report_viewer.models import CaseResult, RunSummary, summarize
from pytest_report_viewer.parser import parse_junit_xml

## 차수 폴더 이름 규칙: <4자리 이상 순번>_<YYYYMMDD-HHMMSS>
_RUN_ID_PATTERN = re.compile(r"^(\d{4,})_\d{8}-\d{6}$")
_REPORT_FILE = "report.xml"
_SUMMARY_FILE = "summary.json"


class RunNotFoundError(LookupError):
    """@brief 없는 차수이거나 run_id 형식이 잘못되었을 때 발생한다."""


@dataclass(frozen=True)
class RunMeta:
    """@brief 차수 실행 환경 정보.

    @param branch 테스트를 실행한 브랜치.
    @param commit 테스트를 실행한 커밋 해시.
    """

    branch: str = ""
    commit: str = ""


@dataclass(frozen=True)
class RunRecord:
    """@brief 저장된 차수 하나의 정보.

    @param run_id 차수 폴더 이름.
    @param seq 차수 순번 (1부터).
    @param created_at 등록 시각 (ISO 8601, 초 단위).
    @param summary 상태별 집계.
    @param meta 실행 환경 정보.
    """

    run_id: str
    seq: int
    created_at: str
    summary: RunSummary
    meta: RunMeta = field(default_factory=RunMeta)

    def to_dict(self) -> dict:
        """@brief JSON 직렬화용 dict로 변환한다.

        @return summary.json에 저장하는 형태의 dict.
        """
        return {
            "run_id": self.run_id,
            "seq": self.seq,
            "created_at": self.created_at,
            "summary": self.summary.to_dict(),
            "meta": asdict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict) -> RunRecord:
        """@brief to_dict() 결과로부터 객체를 복원한다.

        @param data summary.json 내용.
        @return 복원된 RunRecord.
        """
        return cls(
            run_id=data["run_id"],
            seq=data["seq"],
            created_at=data["created_at"],
            summary=RunSummary.from_dict(data["summary"]),
            meta=RunMeta(**data["meta"]),
        )


class RunStore:
    """@brief 결과 루트 폴더 아래의 차수 폴더를 관리한다."""

    def __init__(self, root: Path) -> None:
        """@brief 저장소를 만든다. 루트 폴더는 첫 저장 시 생성한다.

        @param root 결과 루트 폴더 경로.
        """
        self.root = Path(root)

    def save(
        self, report: bytes, meta: RunMeta | None = None, now: datetime | None = None
    ) -> RunRecord:
        """@brief 결과 파일을 새 차수로 저장한다.

        @param report JUnit XML 원본.
        @param meta 실행 환경 정보 (없으면 빈 값).
        @param now 등록 시각 (테스트용, 기본은 현재 시각).
        @return 저장된 차수 정보.
        @throws ReportParseError 결과 파일을 해석할 수 없을 때 (폴더를 만들지 않음).
        """
        # 파싱을 먼저 해서 잘못된 파일이면 폴더를 만들지 않는다.
        summary = summarize(parse_junit_xml(report))
        created = (now or datetime.now()).replace(microsecond=0)
        seq = self._next_seq()
        record = RunRecord(
            run_id=f"{seq:04d}_{created:%Y%m%d-%H%M%S}",
            seq=seq,
            created_at=created.isoformat(),
            summary=summary,
            meta=meta or RunMeta(),
        )
        folder = self.root / record.run_id
        folder.mkdir(parents=True)
        (folder / _REPORT_FILE).write_bytes(report)
        (folder / _SUMMARY_FILE).write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return record

    def list_runs(self) -> list[RunRecord]:
        """@brief 저장된 모든 차수를 순번 오름차순으로 반환한다.

        @return 차수 목록 (없으면 빈 목록).
        """
        return [self._read(folder) for folder in self._run_folders()]

    def get(self, run_id: str) -> RunRecord:
        """@brief 차수 하나를 조회한다.

        @param run_id 차수 폴더 이름.
        @return 차수 정보.
        @throws RunNotFoundError 없거나 형식이 잘못된 run_id.
        """
        return self._read(self._folder(run_id))

    def load_cases(self, run_id: str) -> list[CaseResult]:
        """@brief 차수의 테스트 케이스 결과를 읽는다.

        @param run_id 차수 폴더 이름.
        @return 테스트 케이스 결과 목록.
        @throws RunNotFoundError 없거나 형식이 잘못된 run_id.
        """
        return parse_junit_xml((self._folder(run_id) / _REPORT_FILE).read_bytes())

    def delete(self, run_id: str) -> None:
        """@brief 차수 폴더를 삭제한다.

        @param run_id 차수 폴더 이름.
        @throws RunNotFoundError 없거나 형식이 잘못된 run_id.
        """
        shutil.rmtree(self._folder(run_id))

    def _folder(self, run_id: str) -> Path:
        """@brief run_id를 검증하고 차수 폴더 경로를 반환한다.

        @details 정규식으로 형식을 강제해 "../" 같은 경로 탈출을 막는다.
        @param run_id 차수 폴더 이름.
        @return 존재하는 차수 폴더 경로.
        @throws RunNotFoundError 형식이 틀리거나 폴더가 없을 때.
        """
        folder = self.root / run_id
        if not _RUN_ID_PATTERN.match(run_id) or not folder.is_dir():
            raise RunNotFoundError(f"차수를 찾을 수 없습니다: {run_id!r}")
        return folder

    def _run_folders(self) -> list[Path]:
        """@brief 이름 규칙에 맞는 차수 폴더를 순번 순으로 반환한다.

        @return 차수 폴더 목록 (루트가 없으면 빈 목록).
        """
        if not self.root.is_dir():
            return []
        folders = [p for p in self.root.iterdir() if p.is_dir() and _RUN_ID_PATTERN.match(p.name)]
        return sorted(folders, key=_seq_of)

    def _next_seq(self) -> int:
        """@brief 다음 차수 순번을 계산한다.

        @return 가장 큰 기존 순번 + 1 (없으면 1).
        """
        folders = self._run_folders()
        return _seq_of(folders[-1]) + 1 if folders else 1

    @staticmethod
    def _read(folder: Path) -> RunRecord:
        """@brief 차수 폴더의 summary.json을 읽는다.

        @param folder 차수 폴더 경로.
        @return 차수 정보.
        """
        data = json.loads((folder / _SUMMARY_FILE).read_text(encoding="utf-8"))
        return RunRecord.from_dict(data)


def _seq_of(folder: Path) -> int:
    """@brief 차수 폴더 이름에서 순번을 꺼낸다.

    @param folder 이름 규칙을 만족하는 차수 폴더.
    @return 순번.
    """
    return int(_RUN_ID_PATTERN.match(folder.name).group(1))
