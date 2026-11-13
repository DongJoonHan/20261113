# 20261113
테스트 프로젝트

Pytest 수행 결과를 웹에서 보여주는 프로그램
각 차수의 결과를 폴더 별로 나누고, 트랜드를 보여줘야 함
성공과 실패에 대해 표로 표시해야 한다.

## 사용법

```bash
pip install -e .
# 결과 서버 실행 (결과 폴더 기본값: ./results)
PRV_RESULTS_DIR=results uvicorn pytest_report_viewer.app:app --port 8000

# 테스트 실행 후 결과 등록
pytest --junitxml=report.xml
curl -F file=@report.xml -F branch=main -F commit=$(git rev-parse HEAD) http://localhost:8000/api/v1/runs
```

- 웹 화면: `http://localhost:8000/` (차수 목록, 트렌드), `/runs/{run_id}` (테스트별 성공/실패)
- REST API 문서: `http://localhost:8000/docs`
