# Government Website Status Monitor

정부 웹사이트(.go.kr) 상태를 **저부하**로 모니터링하는 두 가지 구현체

## 🔀 두 가지 구현체

이 프로젝트는 동일한 기능을 제공하는 두 가지 구현체를 포함합니다:

### 1. 🐍 FastAPI 버전 (Python)
- **파일**: `main.py`, `endpoints.yaml`, `.env`
- **장점**: 로컬 실행, 환경변수 설정, 구조화된 설정
- **용도**: 개발/테스트, 온프레미스 배포

### 2. ⚡ Firebase Functions 버전 (Node.js)
- **파일**: `functions/index.js`, `functions/package.json`
- **장점**: 서버리스, 자동 스케일링, 관리 불필요
- **용도**: 프로덕션 배포, 클라우드 운영

## 🏃‍♂️ 빠른 실행

### FastAPI 버전
```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload

# 접속: http://localhost:8000
```

### Firebase Functions 버전
```bash
cd functions

# 의존성 설치
npm install

# 배포
firebase deploy --only functions

# 접속: https://asia-northeast3-PROJECT.cloudfunctions.net/app
```

## 📊 기능 비교

| 기능 | FastAPI | Firebase Functions |
|------|---------|-------------------|
| robots.txt 가드 | ✅ | ✅ |
| 레이트 제한 | ✅ | ✅ |
| SKIPPED UX | ✅ | ✅ |
| 환경변수 설정 | ✅ | ❌ |
| 핫 리로드 | ✅ | ❌ |
| 서버리스 | ❌ | ✅ |
| 자동 스케일링 | ❌ | ✅ |
| 로컬 개발 | ✅ | 제한적 |
| 운영 비용 | 서버 필요 | 저렴 |

## 🎯 선택 가이드

### FastAPI 버전을 선택하는 경우:
- 로컬에서 개발/테스트하고 싶을 때
- 설정을 자주 변경해야 할 때
- 온프레미스 환경에 배포할 때
- Python 생태계를 선호할 때

### Firebase Functions 버전을 선택하는 경우:
- 프로덕션에서 안정적으로 운영하고 싶을 때
- 서버 관리를 하고 싶지 않을 때
- 트래픽 변동에 자동 대응하고 싶을 때
- 비용을 최소화하고 싶을 때

## 🔒 공통 법적 준수사항

두 구현체 모두 동일한 법적 안전 기준을 따릅니다:

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

- **FastAPI 버전**: [main.py 코드 참조](main.py)
- **Firebase Functions 버전**: [functions/README.md](functions/README.md)

## 🛠️ 개발 환경 설정

### 공통 요구사항
- 실제 연락 가능한 이메일 주소
- .go.kr 도메인만 모니터링
- 최대 10개 사이트 권장

### FastAPI 환경
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Firebase Functions 환경
```bash
npm install -g firebase-tools
firebase login
```

## 🚨 주의사항

1. **이메일 주소**: 반드시 실제 연락 가능한 이메일로 설정
2. **레이트 제한**: 설정값을 임의로 줄이지 말 것
3. **모니터링 대상**: .go.kr 도메인만 추가할 것
4. **운영자 요청**: 사이트 운영자가 제외 요청시 즉시 반영

## 📄 라이선스

교육 및 공익 목적으로 제공됩니다. 상업적 이용 전 법적 검토 필요.