# Advanced Health Check Script

강력한 도메인별 키워드 기반 웹사이트 상태 점검 도구

## 🎯 주요 기능

- **도메인별 키워드 설정**: 특정 도메인에 맞춤형 장애 키워드 적용
- **와일드카드 지원**: `*.go.kr` 같은 패턴으로 하위 도메인 일괄 설정
- **정규식 패턴**: 복잡한 문자열 패턴 매칭 지원
- **HTML 제목 추출**: 페이지 `<title>` 태그에서 제목 추출
- **제한된 스캔**: 응답 본문의 일정 바이트만 검사하여 효율성 확보
- **상세한 CSV 출력**: 모든 결과를 구조화된 형태로 저장

## 📥 입력 파일 형식

### 1. URLs 파일 (urls.txt)

```
# 정부 웹사이트
https://www.law.go.kr/
https://www.gov.kr/
https://www.k-eta.go.kr/

# 테스트 URL
https://httpbin.org/status/200
```

- 줄바꿈으로 구분된 URL 목록
- `#`으로 시작하는 줄은 주석으로 무시

### 2. 키워드 설정 파일 (keywords.json)

```json
{
  "global_keywords": [
    "시스템 점검",
    "서비스 중단",
    "불편을 드려 죄송",
    "화재"
  ],
  "domains": {
    "www.law.go.kr": [
      "법령 서비스 중단",
      "데이터베이스 점검"
    ],
    "*.go.kr": [
      "정부 시스템 점검",
      "공공서비스 일시 중단"
    ]
  },
  "regex_keywords": [
    {
      "pattern": "점검.*중",
      "flags": "i"
    }
  ]
}
```

#### 스키마 설명:

- **global_keywords**: 모든 도메인에 적용되는 기본 키워드
- **domains**: 도메인별 전용 키워드
  - 정확한 도메인: `"www.law.go.kr"`
  - 와일드카드: `"*.go.kr"` (모든 .go.kr 하위 도메인)
- **regex_keywords**: 정규식 패턴
  - `pattern`: 정규식 패턴
  - `flags`: 플래그 ("i" = 대소문자 무시)

## 🔍 키워드 매칭 우선순위

1. **정확한 도메인 매칭**: `www.law.go.kr` 전용 키워드
2. **와일드카드 매칭**: `*.go.kr` 패턴 키워드
3. **글로벌 키워드**: 기본 키워드
4. **정규식 패턴**: 모든 regex_keywords 검사

## 🏥 상태 판정 규칙

### Healthy ✅
- HTTP 상태코드 = 200
- 응답 본문에 장애 키워드가 **없음**

### Unhealthy ❌
- HTTP 상태코드 = 200
- 응답 본문에 장애 키워드가 **있음**

### Error 🚫
- HTTP 상태코드 ≠ 200
- 네트워크 오류 (타임아웃, 연결 실패 등)

## 📊 CSV 출력 형식

| 필드 | 설명 | 예시 |
|------|------|------|
| `timestamp_iso` | ISO 8601 형식 시각 | `2025-09-28T17:04:24.830785` |
| `url` | 검사한 URL | `https://www.law.go.kr/` |
| `domain` | 추출된 도메인 | `www.law.go.kr` |
| `status_code` | HTTP 상태 코드 | `200`, `404`, `N/A` |
| `result` | 최종 판정 | `Healthy`, `Unhealthy`, `Error` |
| `response_time_ms` | 응답 시간 (밀리초) | `1513.0` |
| `title` | HTML 제목 | `국가법령정보센터` |
| `matched_keyword` | 매칭된 키워드 | `시스템 점검` |
| `error_message` | 오류 메시지 | `HTTP 404` |

## 🚀 사용법

### 기본 사용

```bash
python healthcheck.py --urls urls.txt --keywords keywords.json --out result.csv
```

### 고급 옵션

```bash
# 스캔 바이트 제한 (기본: 50,000)
python healthcheck.py --urls urls.txt --keywords keywords.json --max-bytes 100000

# 타임아웃 설정 (기본: 10초)
python healthcheck.py --urls urls.txt --keywords keywords.json --timeout 15

# 출력 파일 지정
python healthcheck.py --urls urls.txt --keywords keywords.json --out custom_results.csv
```

### 샘플 파일 생성

```bash
python healthcheck.py --create-samples
```

## 📋 명령행 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--urls` | URL 파일 경로 | 필수 |
| `--keywords` | 키워드 JSON 파일 경로 | 필수 |
| `--out` | 출력 CSV 파일 | `health_check_results.csv` |
| `--max-bytes` | 최대 스캔 바이트 | `50000` |
| `--timeout` | 요청 타임아웃 (초) | `10` |
| `--create-samples` | 샘플 파일 생성 | - |

## 🔧 실행 환경

### 필요한 라이브러리

```bash
pip install requests
```

### Python 버전
- Python 3.7 이상

## 📝 실행 예시

### 1. 정상 케이스
```
Checking 1/3: https://www.law.go.kr/
  → Healthy (200) - 1513.0ms
```

### 2. 장애 키워드 감지
```
Checking 2/3: https://maintenance.example.com/
  → Unhealthy (200) - 856.2ms - Keyword: 시스템 점검
```

### 3. 네트워크 오류
```
Checking 3/3: https://down.example.com/
  → Error (N/A) - Connection error: [Errno 111] Connection refused
```

## 🛠️ 고급 설정

### 도메인별 키워드 예시

```json
{
  "domains": {
    "www.law.go.kr": [
      "법령 서비스 중단",
      "데이터베이스 점검",
      "법령정보 업데이트"
    ],
    "*.go.kr": [
      "정부 시스템 점검",
      "공공서비스 일시 중단"
    ],
    "private.company.com": [
      "내부 시스템 점검",
      "보안 업데이트"
    ]
  }
}
```

### 정규식 패턴 예시

```json
{
  "regex_keywords": [
    {
      "pattern": "점검.*중",
      "flags": "i"
    },
    {
      "pattern": "service.*(?:down|unavailable)",
      "flags": "i"
    },
    {
      "pattern": "시스템.*(?:장애|중단)",
      "flags": "i"
    }
  ]
}
```

## 🚨 주의사항

1. **폴라이트 크롤링**: 요청 간 0.5초 대기로 서버 부하 최소화
2. **바이트 제한**: 대용량 페이지의 전체 다운로드 방지
3. **타임아웃 설정**: 느린 서버로 인한 무한 대기 방지
4. **User-Agent**: 모니터링 목적임을 명시하는 적절한 User-Agent 사용

## 📈 모니터링 활용

### 정기 실행
```bash
# cron으로 매 시간 실행
0 * * * * /usr/bin/python3 /path/to/healthcheck.py --urls /path/to/urls.txt --keywords /path/to/keywords.json --out /path/to/$(date +\%Y\%m\%d_\%H).csv
```

### 알림 연동
```bash
# 결과 분석 및 알림 발송
python healthcheck.py --urls urls.txt --keywords keywords.json --out result.csv
if grep -q "Unhealthy" result.csv; then
    echo "Health check failed!" | mail -s "Alert" admin@company.com
fi
```

## 🤝 확장 가능성

1. **다양한 출력 형식**: JSON, XML 출력 지원
2. **알림 통합**: Slack, 이메일 직접 연동
3. **병렬 처리**: asyncio를 통한 동시 요청
4. **메트릭 수집**: Prometheus, InfluxDB 연동
5. **웹 대시보드**: 실시간 상태 모니터링 UI