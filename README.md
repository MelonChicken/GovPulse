# Government Website Status Monitor

정부 웹사이트(.go.kr) 상태를 **저부하**로 모니터링하는 FastAPI 기반 도구

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
python healthcheck.py --create-samples  # 샘플 파일 생성
python healthcheck.py --urls urls.txt --keywords keywords.json
```

### 3. 프로덕션 배포
- **FastAPI + Caddy**: `politeping/README.md` 참조

## 📊 구현체별 특징

| 구성요소 | 용도 | 주요 기능 |
|---------|------|-----------|
| **기본 FastAPI** | 개발/테스트 | robots.txt 가드, 레이트 제한, 실시간 웹 모니터링 |
| **FastAPI + Caddy** | 프로덕션 배포 | HTTPS 자동화, systemd 서비스, 고성능 |
| **헬스체크 스크립트** | 오프라인 검사 | 일괄 처리, CSV 출력, 키워드 감지 |

## 🎯 사용 시나리오

### 🧪 개발/테스트 단계
- **사용**: 기본 FastAPI (`main.py`)
- **장점**: 빠른 시작, 실시간 수정, 로컬 환경

### 📈 정기 모니터링
- **사용**: 헬스체크 스크립트 (`healthcheck.py`)
- **장점**: cron 스케줄링, 상세한 로그, CSV 분석

### 🏢 프로덕션 배포
- **사용**: FastAPI + Caddy (`politeping/`)
- **장점**: HTTPS 자동화, 고성능, systemd 관리, 완전한 제어

## 🔒 공통 법적 준수사항

모든 구현체가 동일한 법적 안전 기준을 따릅니다:

### ✅ 준수 사항
- **공개 페이지만**: 인증 불필요한 대표 페이지만
- **robots.txt 완전 준수**: Disallow 경로는 요청 안 함
- **저부하**: 도메인당 1분, 엔드포인트당 10분 간격
- **최소 요청**: HEAD 우선, 필요시 GET 첫 청크만
- **연락처 공개**: User-Agent에 실제 연락처 포함

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

## 🚨 주의사항

1. **이메일 주소**: 반드시 실제 연락 가능한 이메일로 설정
2. **레이트 제한**: 설정값을 임의로 줄이지 말 것
3. **모니터링 대상**: .go.kr 도메인만 추가할 것
4. **운영자 요청**: 사이트 운영자가 제외 요청시 즉시 반영

## 📄 라이선스

교육 및 공익 목적으로 제공됩니다. 상업적 이용 전 법적 검토 필요.

본 사이트는 공공 웹페이지( .go.kr )의 공개 엔드포인트에 대해
저부하(도메인당 ≤ 1 req/min) 방식으로 HEAD/경량 GET 요청을 보내
현재 응답 상태를 표시합니다. 

인증이 필요한 페이지·비공개 영역은
점검하지 않으며, 페이지 본문/개인정보를 저장하지 않습니다.
요청 제한이나 모니터링 제외 요청이 있을 경우 즉시 반영합니다.

문의 : m.l02n23@gmail.com