# Government Website Status Monitor

정부 웹사이트(.go.kr) 상태를 **저부하**로 모니터링하는 FastAPI 기반 도구

## 📑 목차

- [프로젝트 개요](#프로젝트-개요)
- [프로젝트 구성](#-프로젝트-구성)
- [빠른 실행](#️-빠른-실행)
- [구현체별 특징](#-구현체별-특징)
- [사용 시나리오](#-사용-시나리오)
- [공통 법적 준수사항](#-공통-법적-준수사항)
- [상세 문서](#-상세-문서)
- [모니터링 사이트 추가 방법](#-모니터링-사이트-추가-방법)
- [Healthy 판단 로직](#-healthy-판단-로직)
- [최근 변경사항](#-최근-변경사항)
- [주의사항](#-주의사항)
- [라이선스](#-라이선스)

## 프로젝트 개요
이 프로젝트는 최근 (2025.9.26. 20:15) 발생한 국가정보자원관리원의 화재 사고의 영향으로 정부 사이트 및 전산이 마비됨에 따라 주요 사이트의 복구 여부를 한눈에 보기 위해 만들어진 프로젝트 입니다.

기술 스택은 FastAPI를 기반으로 가벼우면서 빠른 개발을 지향하였고 Claude code로 빠른 시간 내에 개발을 목표로 프로젝트를 진행하였습니다.
현재 (2025.9.29.) 3단계 지능형 건강 상태 판단 시스템이 구축되어 정교한 사이트 상태 분석이 가능합니다.

그렇기에 언제든지 개선점에 대한 의견을 주시면 감사하겠습니다.
현재 이 프로젝트의 협업 방식은 pull request로 신청시 검토후 반영 (만약 현재 레포지토리로 업로드를 희망하시는 경우) 혹은 독자적 개발을 채택하고 있습니다.

## 🔀 프로젝트 구성

### 1. 🐍 기본 FastAPI 버전
- **파일**: `main.py`, `endpoints.yaml`
- **용도**: 빠른 테스트 및 개발

### 2. 🏭 프로덕션 FastAPI + Caddy 버전
- **디렉토리**: `politeping/`
- **용도**: HTTPS 자동 인증서, systemd 서비스

### 3. 🔍 헬스체크 스크립트
- **파일**: `healthcheck.py`, `healthcheck_enhanced.py`
- **용도**: 오프라인 일괄 상태 검사

## 🏃‍♂️ 빠른 실행

### 1. 기본 FastAPI (개발용)
```bash
pip install requests fastapi uvicorn pyyaml
uvicorn main:app --reload
# 접속: http://localhost:8000
```

### 2. 헬스체크 스크립트 (일괄 검사)
```bash
pip install requests
python healthcheck.py  # 기본 테스트 URL 사용
python healthcheck.py local_test/samples/urls.txt  # URL 파일 사용
```

**파일 경로**:
- **샘플 URL 파일**: `local_test/samples/urls.txt`에 저장
- **CSV 결과 파일**: `local_test/csv/health_check_results.csv`에 자동 저장
- **키워드 설정**: `res/keywords.json` 사용

### 3. 프로덕션 배포
- **FastAPI + Caddy**: `politeping/README.md` 참조

## 📊 구현체별 특징

| 구성요소 | 용도 | 주요 기능 |
|---------|------|-----------|
| **기본 FastAPI** | 개발/테스트 | robots.txt 가드, 실시간 웹 모니터링, 간소화된 상태 표시 |
| **FastAPI + Caddy** | 프로덕션 배포 | HTTPS 자동화, systemd 서비스, 고성능, 키워드 기반 장애 감지 |
| **헬스체크 스크립트** | 오프라인 검사 | 일괄 처리, CSV 출력, 키워드 감지 |

## 🎯 사용 시나리오

### 🧪 개발/테스트 단계
- **사용**: 기본 FastAPI (`main.py`)
- **장점**: 빠른 시작, 실시간 수정, 로컬 환경

## 🔒 공통 법적 준수사항

모든 구현체가 동일한 법적 안전 기준을 따릅니다:

### ✅ 준수 사항
- **공개 페이지만**: 인증 불필요한 대표 페이지만
- **robots.txt 완전 준수**: Disallow 경로는 요청 안 함
- **실시간 모니터링**: 새로고침할 때마다 실제 상태 확인 (하지만 과도한 트래픽은 차단)
- **최소 요청**: HEAD 우선, 필요시 GET 첫 청크

### ❌ 금지 사항
- 비공개 경로 접근 (`/admin`, `/login` 등)
- 개인정보 수집 (폼 제출, 쿠키 등)
- 대량 요청 (레이트 제한 우회)
- 콘텐츠 저장 (크롤링/스크래핑)

## 📚 상세 문서

| 구성요소 | 문서 위치 | 설명 |
|---------|-----------|------|
| 기본 FastAPI | `main.py` 코드 참조 | 단일 파일 구현 |
| 프로덕션 FastAPI + Caddy | `politeping/README.md` | 전체 스택 배포 |
| 헬스체크 스크립트 | `healthcheck_usage.md` | 오프라인 모니터링 |

## 🌐 모니터링 사이트 추가 방법

### 1. 기본 FastAPI 버전 (`main.py`)

**설정 파일**: `res/endpoints.yaml`

```yaml
endpoints:
  - name: "사이트 표시명"
    url: "https://example.go.kr/"
    keywords: ["핵심키워드1", "핵심키워드2"]
```

**예시 추가**:
```yaml
  - name: "국세청 홈택스"
    url: "https://www.hometax.go.kr/"
    keywords: ["홈택스", "국세청", "HOMETAX"]
```

### 2. 프로덕션 FastAPI + Caddy 버전

**설정 파일**: `res/endpoints.yaml`

```yaml
endpoints:
  - name: "사이트 표시명"
    url: "https://example.go.kr/"
```

**예시 추가**:
```yaml
  - name: "국세청 홈택스"
    url: "https://www.hometax.go.kr/"
```

### 3. 헬스체크 스크립트 버전

**URL 목록 파일** (예: `res/urls.txt`):
```
https://example1.go.kr/
https://example2.go.kr/
```

**키워드 설정 파일** (`res/keywords.json`):
```json
{
  "https://example1.go.kr/": ["키워드1", "키워드2"],
  "https://example2.go.kr/": ["키워드3", "키워드4"]
}
```

### 📋 사이트 추가 체크리스트

#### ✅ 추가 전 필수 확인사항
- [ ] `.go.kr` 도메인인지 확인
- [ ] 공개 접근 가능한 메인 페이지인지 확인
- [ ] `robots.txt` 확인 (`https://사이트주소/robots.txt`)
- [ ] 인증이 필요하지 않은 페이지인지 확인

#### 🎯 키워드 선택 가이드
- **필수**: 사이트의 핵심 브랜드명
- **권장**: 서비스의 주요 기능명
- **예시**:
  - 정부24 → `["정부24", "Government 24"]`
  - 홈택스 → `["홈택스", "국세청", "HOMETAX"]`

#### 🚫 추가하면 안 되는 사이트
- 인증이 필요한 관리자 페이지 (`/admin`, `/login`)
- 개인정보가 포함된 페이지
- `robots.txt`에서 접근을 금지한 경로
- 테스트/개발 환경 사이트

### 💡 사이트 추가 후 확인

1. **설정 파일 저장** 후 서비스 재시작
2. **웹 대시보드**에서 새 사이트 표시 확인
3. **상태 체크** 정상 작동 확인
4. **키워드 감지** 테스트 (해당하는 경우)

## 🩺 Healthy 판단 로직

각 구현체는 서로 다른 복잡도의 건강 상태 판단 로직을 사용합니다.

### 📊 개선된 3단계 상태 분류 체계

| 상태 | 의미 | 표시 | 판정 기준 |
|------|------|------|-----------|
| **Healthy** | 정상 작동 | 🟢 녹색 | HTTP 200 + 부정 키워드 없음 + 콘텐츠 품질 양호 |
| **Degraded** | 부분 장애/정보성 | 🟡 노란색 | HTTP 200 + 중립 키워드 감지 OR 경미한 품질 문제 (≤1개) |
| **Unhealthy** | 심각한 장애 | 🔴 빨간색 | HTTP 오류 OR 부정 키워드 감지 OR 심각한 품질 문제 (≥2개) |

### 1. 🐍 기본 FastAPI 버전 (`main.py`)

#### 기본 로직 (fallback)
```
if (HTTP 200) → Healthy
else → Unhealthy
```

#### 고급 로직 (keywords.json 사용시)
```
if (keywords.json 로딩 성공):
    result = healthcheck.health_check_url() 호출
    → 3단계 종합 분석 결과 사용
else:
    → 기본 로직 사용
```

**주요 특징**:
- `keywords.json` 파일이 있으면 고급 분석 자동 활성화
- robots.txt 완전 준수 (`main.py:104-151`)
- HEAD 요청 우선, 405 오류시 GET 요청으로 재시도 (`main.py:244-252`)

### 2. 🏭 프로덕션 FastAPI + Caddy 버전 (`politeping/`)

#### 상세 판단 로직 (`politeping/app/checker.py:261-273`)
```python
if (HTTP 200-399 범위):
    if (부정 키워드 감지):
        → Unhealthy
    else:
        → Healthy
elif (HTTP 상태 코드 존재):
    → Error
else:
    → Error (연결 실패)
```

**핵심 분석 과정**:
1. **요청 단계** (`checker.py:244`) - HEAD 요청 시도, 실패시 GET 스트리밍
2. **콘텐츠 분석** - 전체 페이지 콘텐츠 다운로드 (최대 3MB)
3. **부정 키워드 검사** - 글로벌 + 도메인별 키워드 및 정규식 패턴 매칭

### 3. 🔍 헬스체크 스크립트 (`healthcheck.py`) - **새로 개선됨**

#### 최고 수준의 3단계 종합 분석
```python
if (HTTP != 200):
    → Unhealthy
elif (부정 키워드 매칭):
    → Unhealthy
elif (중립 키워드 매칭 OR 경미한 품질 문제 ≤1개):
    → Degraded
elif (심각한 품질 문제 ≥2개):
    → Unhealthy
else:
    → Healthy
```

**10단계 종합 검사 과정**:

1. **기본 HTTP 검사** - HTTP 200이 아니면 즉시 Unhealthy

2. **콘텐츠 수집** - UTF-8 우선 인코딩, HTML 전체 다운로드 (최대 3MB)

3. **종합 텍스트 추출** - Title, Meta description/og:*, Noscript, 본문 텍스트 통합 분석

4. **텍스트 정규화** - 유니코드 NFKC, 공백 정규화, 대소문자 통일

5. **부정 키워드 검사**
   - **글로벌 키워드**: "시스템 점검", "maintenance", "server error" 등
   - **도메인별 키워드**: 와일드카드 패턴 지원 (*.go.kr)
   - **정규식 패턴**: 11개 고급 패턴으로 장애 상황 탐지

6. **🆕 중립 키워드 검사** (새로운 기능)
   - **정보성 키워드**: "점검 예정", "scheduled update", "정기 업데이트" 등
   - **계획된 유지보수**: "routine maintenance", "시스템 업그레이드" 등
   - **서비스 개선**: "update notice", "service improvement" 등

7. **향상된 콘텐츠 품질 검사**
   - **도메인별 최소 길이**: `min_text_length_overrides` 설정 지원
   - **메타 태그 기반 제목 검증**: `<meta name="description">`, `<meta property="og:title/description">` 인정
   - **단어 수 부족**: 10개 미만 단어 감지
   - **JavaScript 오류**: 4가지 JS 에러 패턴 감지

8. **지능형 최종 판정**
   ```python
   if 부정_키워드_존재:
       return "Unhealthy"
   elif 중립_키워드_존재 or (품질_문제_개수 <= 1):
       return "Degraded"
   elif 품질_문제_개수 >= 2:
       return "Unhealthy"
   else:
       return "Healthy"
   ```

9. **결과 생성** - 타임스탬프, 응답시간, 콘텐츠 해시, 상세 키워드 정보

10. **통계 및 리포팅** - 3단계 상태별 집계 및 CSV 출력

### 📋 향상된 키워드 설정 (`keywords.json`)

#### 새로운 키워드 카테고리
```json
{
  "global_keywords": [
    "시스템 점검", "서비스 중단", "maintenance", "server error"
  ],
  "neutral_info_keywords": [
    "점검 예정", "scheduled update", "정기 업데이트",
    "routine maintenance", "시스템 업그레이드"
  ],
  "domains": {
    "*.go.kr": ["정부사이트 특화 키워드"]
  },
  "settings": {
    "min_text_length": 60,
    "min_text_length_overrides": {
      "*.go.kr": 30,
      "www.data.go.kr": 50
    }
  }
}
```

#### 도메인별 최소 텍스트 길이 설정
- **기본값**: 60자
- ***.go.kr**: 30자 (정부사이트는 간결한 경우가 많음)
- **특정 사이트**: 개별 설정 가능

### 🚨 False Positive 방지 개선 사항

#### 1. 메타 태그 기반 제목 인정
- `<meta name="description">` 존재시 제목 누락으로 판정하지 않음
- `<meta property="og:title">`, `<meta property="og:description">` 인정

#### 2. 3단계 점진적 판정
- **Degraded 상태 도입**: 완전한 장애가 아닌 정보성/계획된 상황 구분
- **중립 키워드**: 계획된 유지보수나 업데이트 안내는 Degraded로 분류

#### 3. 도메인별 맞춤 설정
- 정부사이트는 일반적으로 간결 → 낮은 최소 텍스트 길이 적용
- 사이트별 특성에 맞는 개별 임계값 설정

### 💡 성능 최적화 유지

#### 요청 최적화
- **HEAD 우선**: 콘텐츠 다운로드 없이 상태 확인
- **스트리밍 GET**: HEAD 실패시 부분 다운로드
- **타임아웃 설정**: 연결 5초, 읽기 8초, 전체 12초

#### 캐싱 전략
- **robots.txt**: 24시간 캐시
- **성공 결과**: 메모리 캐시로 빠른 재확인

#### Rate Limiting
- **호스트별**: 동시 요청 1개 제한
- **글로벌**: 최대 3개 동시 요청
- **최소 간격**: 호스트당 60초, 엔드포인트당 10분

## 📁 프로젝트 파일 구조

```
GovPulse/
├── main.py                      # 기본 FastAPI 서버
├── healthcheck.py               # 헬스체크 스크립트
├── res/                         # 리소스 파일 디렉토리
│   ├── endpoints.yaml           # 모니터링 대상 사이트 설정
│   ├── keywords.json            # 키워드 기반 장애 감지 설정
│   └── urls.txt                 # URL 목록 파일
├── local_test/                  # 로컬 테스트 디렉토리
│   ├── samples/                 # 샘플 CSV 파일 위치 (git 추적)
│   │   └── sample.csv
│   ├── csv/                     # 산출된 CSV 결과 저장소 (git 무시)
│   │   └── health_check_results.csv
│   └── test_main.http          # API 테스트 파일
├── politeping/                  # 프로덕션 배포용 디렉토리
│   ├── app/
│   │   ├── main.py
│   │   ├── checker.py
│   │   └── ...
│   └── README.md
└── README.md
```

### 📋 CSV 파일 관리

- **샘플 파일**: `local_test/samples/` - Git에 포함되어 예시로 제공
- **결과 파일**: `local_test/csv/` - Git에서 제외되며, 스크립트 실행 시 자동 생성
- **출력 경로**: `healthcheck.py` 실행 시 결과는 `local_test/csv/health_check_results.csv`에 자동 저장

## 🔄 최근 변경사항

### v2025.09.30 - 리소스 파일 구조 개선
- **res 디렉토리 도입**: 설정 파일(`endpoints.yaml`, `keywords.json`, `urls.txt`)을 `res/` 디렉토리로 이동하여 체계적인 리소스 관리
- **Firebase Functions 제거**: 미사용 Firebase Functions 디렉토리 완전 삭제
- **CSV 경로 표준화**: 결과 파일은 `local_test/csv/`에 저장, 샘플은 `local_test/samples/`에 보관
- **문서 개선**: 프로젝트 구조 및 리소스 파일 위치 명시
- **모든 참조 업데이트**: `main.py`, `healthcheck.py`, `politeping/` 모듈의 파일 경로를 새로운 구조에 맞게 수정

### v2025.9.29 - 지능형 3단계 건강 상태 시스템
- **3단계 상태 도입**: Healthy/Degraded/Unhealthy로 세분화
- **중립 키워드 시스템**: 계획된 유지보수/업데이트 정보 구분
- **메타 태그 지원**: description, og:title/description을 제목 대안으로 인정
- **도메인별 설정**: `min_text_length_overrides`로 사이트별 맞춤 임계값
- **False Positive 대폭 감소**: 정부사이트 특성 반영한 판정 로직
- **향상된 리포팅**: 3단계 상태별 통계 및 상세 분석 결과

## 🚨 주의사항

1. **이메일 주소**: 반드시 실제 연락 가능한 이메일로 설정
2. **모니터링 대상**: .go.kr 도메인만 추가할 것
3. **운영자 요청**: 사이트 운영자가 제외 요청시 즉시 반영
4. **새로고침 주의**: 실시간 요청으로 변경되어 과도한 새로고침 자제

## 📄 라이선스

기본적으로 MIT 라이센스를 기반으로 하고 있으나, 프로젝트의 특성상 일부 제한을 추가하고 있습니다.
교육 및 공익 목적으로 제공됩니다. 상업적 이용 전 법적 검토가 필요합니다.

본 사이트는 공공 웹페이지( .go.kr )의 공개 엔드포인트에 대해
실시간 모니터링 방식으로 HEAD/경량 GET 요청을 보내
현재 응답 상태를 표시합니다. 

인증이 필요한 페이지·비공개 영역은
점검하지 않으며, 페이지 본문/개인정보를 저장하지 않습니다.
공적인 목적으로의 요청 제한이나 모니터링 제외 요청이 있을 경우 즉시 반영합니다.

문의 : m.l02n23@gmail.com
