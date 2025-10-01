## 요약
- 이 PR의 목적과 배경

## 주요 변경사항
- [ ] 코드/로직
- [ ] 의존성
- [ ] 스키마/마이그레이션
- [ ] 문서

## 테스트 방법
1. `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
2. `/health` 및 대시보드 확인
3. `python healthcheck.py` 또는 `pytest` 실행

## 스크린샷/로그
<!-- 필요 시 첨부 -->

## 체크리스트
- [ ] 로컬 테스트 통과 (수동/자동)
- [ ] Render 배포 설정 확인 (Start command, PORT, proxy-headers)
- [ ] 새/변경 리소스 파일 경로 문서화
- [ ] 이슈 연결 (예: Closes #123)