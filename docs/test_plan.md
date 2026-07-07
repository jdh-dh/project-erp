# 시험 계획서 (test_plan.md)

## 1. 개요

Phase 1 기능의 단위시험·통합시험 계획을 정의한다.

- 작성일: 2026-07-07
- 상태: 초안 (사용자 승인 대기)

## 2. 시험 환경

- Backend: pytest + httpx (FastAPI TestClient), 테스트 전용 PostgreSQL (docker-compose 또는 SQLite 대체 불가 — JSONB 사용으로 PostgreSQL 고정)
- Frontend: Vitest + React Testing Library
- CI: GitHub Actions에서 push 시 자동 실행 (Phase 1 내 구성)

## 3. 단위시험 (Unit Test)

서비스 계층 함수 단위로 시험한다.

| ID | 대상 | 시험 항목 |
|----|------|-----------|
| UT-AUTH-01 | 비밀번호 해시 | 해시 생성·검증, 평문 불일치 시 실패 |
| UT-AUTH-02 | JWT | 토큰 생성·검증, 만료 토큰 거부, 위조 토큰 거부 |
| UT-USER-01 | 사용자 서비스 | 등록, 이메일 중복 시 오류, 비활성화 |
| UT-CUST-01 | 고객사 서비스 | 등록, 수정, 담당자 추가, 프로젝트 연결 시 비활성화만 허용 |
| UT-PROJ-01 | 프로젝트 서비스 | 등록, 코드 중복 시 오류 |
| UT-PROJ-02 | 상태 전이 | 허용 전이 성공, 비허용 전이(예: COMPLETED→IN_PROGRESS) 거부 |
| UT-COM-01 | 변경 이력 | 생성·수정·상태변경 시 change_logs 기록 확인 |

## 4. 통합시험 (Integration Test)

API 엔드포인트 단위로 실제 DB를 사용해 시험한다.

| ID | 시나리오 |
|----|----------|
| IT-01 | 로그인 → 토큰 발급 → /auth/me 조회 → 토큰 재발급 |
| IT-02 | 잘못된 비밀번호 로그인 → 401, 비활성 사용자 로그인 → 401 |
| IT-03 | admin이 사용자 등록 → member 권한으로 사용자 등록 시도 → 403 |
| IT-04 | 고객사 등록 → 담당자 추가 → 상세 조회에 담당자 포함 확인 |
| IT-05 | 프로젝트 등록(고객사·PM 연결) → 상세 조회 → 참여자 설정 → 계약 등록 |
| IT-06 | 프로젝트 상태 변경 흐름 (PLANNED→IN_PROGRESS→COMPLETED) 및 이력 조회 |
| IT-07 | 중복 프로젝트 코드 등록 → 409 |
| IT-08 | 인증 없이 보호 API 호출 → 401 |

## 5. 합격 기준

- 계획된 단위시험·통합시험 전체 통과
- 서비스 계층 코드 커버리지 80% 이상
- 시험 결과는 verification.md 에 기록한다.
