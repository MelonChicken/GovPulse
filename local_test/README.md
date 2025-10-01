# local_test/

로컬 환경에서 애플리케이션을 테스트하기 위한 디렉토리입니다.

## 구조

```
local_test/
├── samples/        # 샘플 입력 파일 (git 추적)
│   └── *.csv      # 테스트용 샘플 데이터
├── csv/           # 테스트 결과 출력 (git 무시)
│   ├── *.csv      # 헬스체크 결과
│   └── *.json     # JSON 형식 결과
├── test_urls.txt  # 테스트용 URL 목록
└── test_main.http # HTTP 요청 테스트 파일
```

## 사용법

### 1. 헬스체크 실행
```bash
python healthcheck.py
```
결과는 `local_test/csv/` 디렉토리에 저장됩니다.

### 2. API 서버 테스트
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

테스트 URL: http://localhost:8000

### 3. 샘플 데이터 추가
`samples/` 디렉토리에 테스트용 CSV 파일을 추가할 수 있습니다.
이 파일들은 git으로 추적되어 팀원들과 공유됩니다.

## 주의사항

- `csv/` 디렉토리의 산출물은 .gitignore에 의해 자동으로 제외됩니다
- 민감한 정보가 포함된 URL은 테스트하지 마세요
- 테스트 결과 파일은 로컬에만 보관됩니다