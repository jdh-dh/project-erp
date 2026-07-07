# 릴리즈 노트 (release_note.md)

## v0.1.0 — Phase 1 (2026-07-07)

### 신규 기능

**인증/사용자**
- JWT 로그인 (Access 30분 / Refresh 14일), 토큰 재발급
- bcrypt 비밀번호 해시
- 역할 기반 접근 제어 (admin / manager / member)
- 사용자 등록·수정·비활성화 (admin)

**고객사 관리**
- 고객사 등록·조회·수정·비활성화 (논리 삭제)
- 고객사 담당자 복수 등록·수정
- 고객사명 검색

**프로젝트 관리**
- 프로젝트 등록·조회·수정 (코드 중복 방지)
- 프로젝트 유형 (HW / SW / HYBRID)
- 상태 관리 및 전이 규칙 (준비→진행→보류/완료/취소)
- 참여자 지정, 계약 정보 등록·수정

**공통**
- 변경 이력(change_logs) 자동 기록 — 누가/언제/무엇을 (before/after JSONB)
- 요청 로깅, 공통 예외 처리
- 초기 admin 계정 생성 스크립트

### 기술 구성

- Backend: FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 16
- Frontend: React 18 + TypeScript + Vite + TanStack Query
- 배포: docker-compose (db / backend / frontend+nginx)
- CI: GitHub Actions (백엔드 pytest + 프론트 빌드/테스트)

### 시험 결과

- 백엔드 pytest 36건 통과, 커버리지 93%
- 프론트 빌드(타입 검사) 및 Vitest 통과
- E2E 수동 검증 완료 (검증 문서 참조)

### 알려진 제한

- 로그인 실패 횟수 제한 없음 (확인 필요)
- Phase 2(WBS/마일스톤) 이후 기능 미포함
