ㅇ# PolitePing Firebase Functions

Firebase Functions v2 기반 정부 웹사이트 상태 모니터링 시스템

## 📋 목차

- [프로젝트 소개](#프로젝트-소개)
- [주요 기능](#주요-기능)
- [빠른 시작](#빠른-시작)
- [상세 설정 가이드](#상세-설정-가이드)
- [커스터마이징](#커스터마이징)
- [문제해결](#문제해결)
- [API 문서](#api-문서)
- [법적 준수사항](#법적-준수사항)

## 🎯 프로젝트 소개

PolitePing은 정부 웹사이트(.go.kr)의 상태를 **저부하**로 모니터링하는 시스템입니다.

### 특징
- 🚫 **robots.txt 완전 준수**: Disallow 경로는 실제 요청하지 않음
- ⏱️ **엄격한 레이트 제한**: 도메인당 1분, 엔드포인트당 10분 간격
- 🎯 **HEAD 우선**: 최소한의 트래픽으로 상태 확인
- 📱 **실시간 대시보드**: 60초마다 자동 갱신
- 🔒 **법적 안전**: 공개 대표 페이지만 모니터링

## ✨ 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| robots.txt 가드 | Disallow 경로는 DISALLOWED로 표시만 | ✅ |
| 레이트 제한 | 도메인 1req/min, 엔드포인트 1req/10min | ✅ |
| SKIPPED UX | 레이트 제한시 마지막 결과 표시 | ✅ |
| 캐시 제어 | Cache-Control: max-age=60 | ✅ |
| 저부하 요청 | HEAD → GET 첫 청크만 | ✅ |
| 서울 리전 | asia-northeast3 배포 | ✅ |

## 🚀 빠른 시작

### 1. 사전 준비

```bash
# Node.js 20+ 설치 확인
node --version

# Firebase CLI 설치
npm install -g firebase-tools

# Firebase 로그인
firebase login
```

### 2. 프로젝트 설정

```bash
# 새 디렉토리 생성
mkdir politeping
cd politeping

# Firebase 프로젝트 초기화
firebase init

# Functions 선택 (스페이스로 체크)
# ◉ Functions

# 설정 선택
# - JavaScript 선택
# - ESLint 사용하지 않음
# - 의존성 설치 Yes
```

### 3. 파일 복사

```bash
# 이 프로젝트의 파일들을 복사
cp functions/package.json your-project/functions/
cp functions/index.js your-project/functions/
```

### 4. 설정 수정

`functions/index.js`를 열어 다음을 수정:

```javascript
// 🔧 반드시 수정해야 할 부분
const UA = "GovPublicStatusMonitor/1.0 (+YOUR-EMAIL@domain.com)";

// 📝 모니터링할 사이트 수정
const ENDPOINTS = [
  { name: "정부24 메인", url: "https://www.gov.kr/" },
  // 추가할 사이트들...
];
```

### 5. 배포

```bash
cd functions
npm install
cd ..
firebase deploy --only functions
```

### 6. 확인

배포 완료 후 출력되는 URL로 접속:
```
https://asia-northeast3-YOUR-PROJECT.cloudfunctions.net/app
```

## ⚙️ 상세 설정 가이드

### 연락처 정보 설정

```javascript
// functions/index.js 상단
const UA = "GovPublicStatusMonitor/1.0 (+contact@yourcompany.com)";
```

**중요**: 실제 연락 가능한 이메일을 입력하세요. 사이트 운영자가 연락할 수 있어야 합니다.

### 모니터링 대상 설정

```javascript
const ENDPOINTS = [
  {
    name: "사이트 표시명",
    url: "https://example.go.kr/"
  },
  // 최대 10개 정도 권장
];
```

### 타임아웃 설정

```javascript
const TOTAL_TIMEOUT_MS = 12000;  // 전체 타임아웃 12초
const READ_TIMEOUT_MS = 8000;    // 읽기 타임아웃 8초
const SLA_TTFB_MS = 8000;        // TTFB 기준 8초
```

### 레이트 제한 설정

```javascript
const HOST_MIN_INTERVAL_MS = 60 * 1000;      // 도메인당 1분
const EP_MIN_INTERVAL_MS = 10 * 60 * 1000;   // 엔드포인트당 10분
```

**주의**: 이 값들을 너무 짧게 설정하지 마세요. 법적 문제가 발생할 수 있습니다.

### 지역 설정

```javascript
exports.app = onRequest({
  region: "asia-northeast3",  // 서울
  timeoutSeconds: 15,
  cors: true
}, app);
```

다른 지역 옵션:
- `asia-northeast1` (도쿄)
- `us-central1` (아이오와)
- `europe-west1` (벨기에)

## 🎨 커스터마이징

### 대시보드 스타일 변경

`functions/index.js`의 HTML 섹션에서 CSS 수정:

```javascript
app.get("/", (_req, res) => {
  res.type("html").send(`<!doctype html>
<style>
/* 여기서 스타일 수정 */
body {
  font-family: 'Noto Sans KR', sans-serif;
  background: #f8f9fa;
}
.card {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}
.card:hover {
  transform: translateY(-2px);
}
</style>
```

### 상태 기준 변경

```javascript
// checkOne() 함수 내부
if (http && http >= 200 && http < 400) {
  // 기준 변경 가능
  outcome = (ttfbMs <= SLA_TTFB_MS) ? "OK" : "UNSTABLE";
} else if (http) {
  outcome = http >= 500 ? "HTTP5xx" : "HTTP4xx";
}
```

### 알림 추가

```javascript
// 에러 발생시 알림 (Slack, 이메일 등)
if (outcome === "ERROR" || outcome === "HTTP5xx") {
  // 여기에 알림 로직 추가
  console.error(`Alert: ${ep.name} is down!`);
}
```

### 데이터 저장

현재는 메모리 캐시만 사용하지만, Firestore 추가 가능:

```javascript
// Firestore 저장 예시
const { getFirestore } = require('firebase-admin/firestore');

async function saveResult(result) {
  const db = getFirestore();
  await db.collection('monitoring').add({
    ...result,
    timestamp: new Date()
  });
}
```

## 🔧 문제해결

### 배포 실패

```bash
# 권한 확인
firebase login

# 프로젝트 설정 확인
firebase use --add

# 함수만 다시 배포
firebase deploy --only functions:app
```

### 로그 확인

```bash
# 실시간 로그
firebase functions:log

# 특정 함수 로그
firebase functions:log --only app
```

### 메모리 부족

Functions 메모리 늘리기:

```javascript
exports.app = onRequest({
  region: "asia-northeast3",
  timeoutSeconds: 15,
  memory: "1GiB",  // 기본 256MB → 1GB
  cors: true
}, app);
```

### CORS 오류

```javascript
// CORS 설정 상세화
exports.app = onRequest({
  region: "asia-northeast3",
  timeoutSeconds: 15,
  cors: {
    origin: ["https://yourdomain.com"],
    methods: ["GET"]
  }
}, app);
```

## 📚 API 문서

### GET /snapshot

정부 사이트들의 현재 상태를 JSON으로 반환

**응답 예시:**
```json
[
  {
    "name": "정부24 메인",
    "url": "https://www.gov.kr/",
    "http": 200,
    "ttfb_ms": 456.7,
    "outcome": "OK",
    "error": null,
    "ts": "2023-12-01T10:30:00.000Z",
    "robots": "parsed"
  },
  {
    "name": "차단된 사이트",
    "url": "https://blocked.go.kr/admin/",
    "http": null,
    "ttfb_ms": 0,
    "outcome": "DISALLOWED",
    "error": null,
    "ts": "2023-12-01T10:30:00.000Z",
    "robots": "parsed"
  },
  {
    "name": "레이트 제한",
    "url": "https://example.go.kr/",
    "outcome": "SKIPPED",
    "skipped": true,
    "last_outcome": "OK",
    "http": 200,
    "ttfb_ms": 234.5,
    "last_ts": "2023-12-01T10:29:00.000Z",
    "ts": "2023-12-01T10:30:00.000Z",
    "robots": "allow"
  }
]
```

**필드 설명:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | string | 사이트 표시명 |
| `url` | string | 모니터링 URL |
| `http` | number\|null | HTTP 상태 코드 |
| `ttfb_ms` | number | Time To First Byte (밀리초) |
| `outcome` | string | OK, UNSTABLE, ERROR, HTTP4xx, HTTP5xx, DISALLOWED, SKIPPED |
| `error` | string\|null | 에러 메시지 |
| `ts` | string | 체크 시각 (ISO 8601) |
| `robots` | string | robots.txt 정책 (parsed, allow, unknown) |
| `skipped` | boolean | 레이트 제한으로 스킵 여부 |
| `last_outcome` | string | 마지막 성공한 결과 (SKIPPED시에만) |
| `last_ts` | string | 마지막 성공 시각 (SKIPPED시에만) |

### GET /

HTML 대시보드 반환. 브라우저에서 접속하여 실시간 모니터링 가능.

## ⚖️ 법적 준수사항

이 프로젝트는 **법적 안전**을 최우선으로 설계되었습니다.

### ✅ 준수 사항

1. **공개 페이지만**: 인증이 필요없는 대표 페이지만 모니터링
2. **robots.txt 완전 준수**: Disallow 경로는 요청하지 않음
3. **저부하**: 도메인당 1분, 엔드포인트당 10분 간격
4. **최소 요청**: HEAD 우선, 필요시 GET 첫 청크만
5. **연락처 공개**: User-Agent에 연락 가능한 이메일 포함
6. **데이터 미저장**: 개인정보나 콘텐츠 저장 안 함

### ❌ 금지 사항

1. **비공개 경로 접근**: `/admin`, `/login` 등 인증 필요 영역
2. **개인정보 수집**: 폼 제출, 쿠키 저장 등
3. **대량 요청**: 레이트 제한 우회 시도
4. **콘텐츠 저장**: 페이지 내용 크롤링/저장
5. **봇 탐지 우회**: 헤더 조작, IP 로테이션 등

### 📋 운영 체크리스트

배포 전 확인사항:

- [ ] 연락처 이메일이 실제 연락 가능한지 확인
- [ ] 모니터링 대상이 모두 .go.kr 도메인인지 확인
- [ ] 레이트 제한이 1분/10분으로 설정되어 있는지 확인
- [ ] robots.txt 차단 기능이 활성화되어 있는지 확인
- [ ] 대상 사이트가 10개 이하인지 확인

운영 중 모니터링:

- [ ] Firebase 로그에서 robots.txt 차단 확인
- [ ] 요청 간격이 설정값을 지키는지 확인
- [ ] 에러율이 50% 이하인지 확인
- [ ] 사이트 운영자로부터 차단 요청이 없는지 확인

### 🚨 문제 발생시 대응

1. **사이트 운영자 연락시**: 즉시 해당 사이트를 ENDPOINTS에서 제거
2. **법적 문제 제기시**: 서비스 즉시 중단 후 전문가 상담
3. **과도한 요청 감지시**: 레이트 제한을 더 엄격하게 조정

## 📞 지원

문제가 발생하거나 질문이 있으면:

1. **이슈 등록**: GitHub Issues에 상세한 설명과 함께 등록
2. **로그 첨부**: Firebase Functions 로그 스크린샷 포함
3. **설정 공유**: 문제가 되는 설정 부분 코드 첨부

## 📄 라이선스

이 프로젝트는 교육 및 공익 목적으로 제공됩니다. 상업적 이용시 사전 검토가 필요합니다.