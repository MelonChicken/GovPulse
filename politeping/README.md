# PolitePing FastAPI + Caddy

FastAPI 기반 정부 웹사이트 상태 모니터링 시스템 (Caddy 역프록시 + 자동 TLS)

## 🏗️ 프로젝트 구조

```
politeping/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션
│   ├── config.py            # 설정 관리
│   ├── endpoints.py         # 엔드포인트 로더
│   ├── rate_limit.py        # 레이트 제한
│   ├── robots.py            # robots.txt 가드
│   ├── checker.py           # 웹사이트 체크 로직
│   └── ui.py                # HTML 대시보드
├── deploy/
│   ├── Caddyfile            # Caddy 설정 (배포용)
│   └── politeping.service   # systemd 서비스
├── endpoints.yaml           # 모니터링 대상
├── .env.example             # 환경변수 템플릿
├── requirements.txt         # Python 의존성
├── Caddyfile                # 로컬 테스트용
└── README.md
```

## 🚀 빠른 시작

### 1. 사전 준비

```bash
# 도메인과 이메일 설정 (필수)
DOMAIN="monitor.example.com"
EMAIL="you@example.com"
```

### 2. 로컬 테스트

```bash
# 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경설정
cp .env.example .env
sed -i "s/you@example.com/$EMAIL/g" .env

# 애플리케이션 실행
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 테스트: http://localhost:8000
```

### 3. 프로덕션 배포

#### 서버 준비

```bash
# 패키지 업데이트
sudo apt update && sudo apt install -y python3.11-venv git

# Caddy 설치 (공식 리포)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo tee /usr/share/keyrings/caddy-stable-archive-keyring.gpg >/dev/null
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

#### 앱 배치

```bash
# 디렉토리 생성
sudo mkdir -p /opt/politeping && sudo chown $USER:$USER /opt/politeping

# 코드 복사
cp -R . /opt/politeping
cd /opt/politeping

# Python 환경 설정
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# 환경설정 (이메일 주소 반드시 수정)
cp .env.example .env
sed -i "s/you@example.com/$EMAIL/g" .env
```

#### systemd 서비스 등록

```bash
# 서비스 파일 복사
sudo cp deploy/politeping.service /etc/systemd/system/politeping.service

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable --now politeping

# 상태 확인
sudo systemctl status politeping
```

#### Caddy 설정

```bash
# Caddy 설정 복사 및 도메인 수정
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo sed -i "s/monitor.example.com/$DOMAIN/g" /etc/caddy/Caddyfile

# Caddy 재시작
sudo systemctl reload caddy

# 상태 확인
sudo systemctl status caddy
```

## ✅ 검증 절차

### 1. 앱 헬스 체크

```bash
curl -s https://$DOMAIN/health
# 응답: {"ok": true, "ts": 1234567890.123}
```

### 2. 스냅샷 API 테스트

```bash
# 첫 번째 호출 (정상 JSON)
curl -s https://$DOMAIN/snapshot | jq .

# 바로 재호출 (SKIPPED 항목 확인)
curl -s https://$DOMAIN/snapshot | jq .
```

### 3. 대시보드 확인

브라우저에서 `https://$DOMAIN` 접속:
- 카드 형태 UI 표시
- 60초마다 자동 갱신
- robots.txt 상태 표시

## ⚙️ 설정 가이드

### 환경변수 (.env)

```bash
# 연락처 정보 (필수 수정)
PP_UA="GovPublicStatusMonitor/1.0 (+contact@yourcompany.com)"

# 타임아웃 설정
PP_CONNECT_TIMEOUT_S=5      # 연결 타임아웃
PP_READ_TIMEOUT_S=8         # 읽기 타임아웃
PP_TOTAL_TIMEOUT_S=12       # 전체 타임아웃
PP_TTFB_SLA_S=8             # TTFB SLA 기준

# 레이트 제한
PP_HOST_MIN_INTERVAL_S=60   # 도메인당 최소 간격 (초)
PP_EP_MIN_INTERVAL_S=600    # 엔드포인트당 최소 간격 (초)

# 동시성 제어
PP_GLOBAL_MAX_CONCURRENCY=3    # 전체 최대 동시 요청
PP_PER_HOST_CONCURRENCY=1      # 호스트당 최대 동시 요청
```

### 모니터링 대상 (endpoints.yaml)

```yaml
endpoints:
  - name: "사이트명"
    url: "https://example.go.kr/"
  # 최대 10개 권장
```

### Caddy 설정

```
your-domain.com {
  encode gzip
  reverse_proxy 127.0.0.1:8000

  # 보안 헤더
  header {
    X-Frame-Options "DENY"
    X-Content-Type-Options "nosniff"
    Referrer-Policy "no-referrer"
  }

  # 캐시 제어
  @snapshot path /snapshot
  header @snapshot Cache-Control "public, max-age=60, s-maxage=60"
  header /* Cache-Control "no-store"
}
```

## 🔧 문제해결

### 서비스 상태 확인

```bash
# 앱 상태
sudo systemctl status politeping
sudo journalctl -u politeping -f

# Caddy 상태
sudo systemctl status caddy
sudo journalctl -u caddy -f
```

### 로그 확인

```bash
# 애플리케이션 로그
sudo journalctl -u politeping --since "1 hour ago"

# Caddy 액세스 로그
sudo journalctl -u caddy --since "1 hour ago"
```

### 설정 재로드

```bash
# 환경변수 변경 후
sudo systemctl restart politeping

# Caddy 설정 변경 후
sudo systemctl reload caddy
```

### 일반적인 문제

#### 1. 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep :8000
sudo fuser -k 8000/tcp  # 프로세스 종료
```

#### 2. 권한 문제
```bash
# 디렉토리 권한 확인
sudo chown -R www-data:www-data /opt/politeping
sudo chmod -R 755 /opt/politeping
```

#### 3. DNS/TLS 문제
```bash
# DNS 확인
nslookup $DOMAIN

# TLS 인증서 확인
sudo caddy list-certificates
```

## 📊 모니터링

### 주요 메트릭

- **응답 시간**: TTFB 8초 이내 권장
- **성공률**: 90% 이상 유지
- **레이트 준수**: 도메인당 1분, 엔드포인트당 10분 간격

### 알림 설정

로그 기반 알림 예시:

```bash
# systemd journal을 통한 모니터링
journalctl -u politeping -f | grep -E "(ERROR|HTTP5xx)" | while read line; do
  echo "Alert: $line" | mail -s "PolitePing Alert" admin@company.com
done
```

## 🔒 보안 고려사항

### 1. 네트워크 접근 제한

```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (Caddy)
sudo ufw allow 443/tcp     # HTTPS (Caddy)
sudo ufw --force enable

# 내부 포트 차단
sudo ufw deny 8000/tcp     # FastAPI는 localhost만
```

### 2. 시스템 업데이트

```bash
# 정기 업데이트
sudo apt update && sudo apt upgrade -y

# 보안 패치만
sudo unattended-upgrades
```

### 3. 로그 로테이션

```bash
# logrotate 설정
sudo tee /etc/logrotate.d/politeping << EOF
/var/log/syslog {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 0644 syslog adm
    postrotate
        systemctl reload rsyslog
    endscript
}
EOF
```

## 📋 운영 체크리스트

### 배포 전 확인

- [ ] 도메인이 서버 IP로 올바르게 설정됨
- [ ] .env 파일의 이메일 주소가 실제 연락 가능한 주소임
- [ ] endpoints.yaml의 모든 URL이 .go.kr 도메인임
- [ ] 레이트 제한이 1분/10분으로 설정됨
- [ ] systemd 서비스가 정상 시작됨
- [ ] Caddy TLS 인증서가 정상 발급됨

### 운영 중 모니터링

- [ ] 앱 health check 정상 응답 확인
- [ ] robots.txt 차단 현황 주기적 확인
- [ ] 에러율 50% 이하 유지
- [ ] TTFB 평균 8초 이하 유지
- [ ] 디스크 사용량 80% 이하 유지

### 정기 점검 (월 1회)

- [ ] 시스템 패키지 업데이트
- [ ] 로그 파일 정리
- [ ] TLS 인증서 만료일 확인
- [ ] 모니터링 대상 사이트 유효성 확인

## 📞 지원

문제 발생시:

1. **로그 확인**: `sudo journalctl -u politeping --since "1 hour ago"`
2. **서비스 재시작**: `sudo systemctl restart politeping caddy`
3. **설정 검증**: 환경변수와 yaml 파일 문법 확인