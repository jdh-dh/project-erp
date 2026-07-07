# 검증 문서 (verification.md)

## Phase 1 검증 결과

- 검증일: 2026-07-07
- 검증 환경: Python 3.11.15, Node 22.22.2, PostgreSQL 16
- 상태: **검증 완료**

## 1. 단위시험 / 통합시험 결과

`backend/tests/` — pytest 실행 결과:

| 항목 | 결과 |
|------|------|
| 테스트 수 | 36건 |
| 통과 | 36건 (100%) |
| 실패 | 0건 |
| 전체 커버리지 | 93% |
| 서비스 계층 커버리지 | 84~100% (합격 기준 80% 이상) |

시험 계획 대비 수행 현황:

| 계획 ID | 수행 테스트 | 결과 |
|---------|-------------|------|
| UT-AUTH-01 | tests/test_security.py::TestPasswordHash | 통과 |
| UT-AUTH-02 | tests/test_security.py::TestJwt | 통과 |
| UT-USER-01 | tests/test_users_api.py | 통과 |
| UT-CUST-01 | tests/test_customers_api.py | 통과 |
| UT-PROJ-01 | tests/test_projects_api.py::TestProjectCrud | 통과 |
| UT-PROJ-02 | tests/test_projects_api.py::TestStatusTransition | 통과 |
| UT-COM-01 | test_users_api.py, test_projects_api.py (change_logs 확인) | 통과 |
| IT-01 ~ IT-08 | test_auth_api.py, test_users_api.py, test_customers_api.py, test_projects_api.py | 통과 |

프론트엔드: `npm run build`(TypeScript 타입 검사 포함) 성공, Vitest 3건 통과.

## 2. E2E 수동 검증 (실제 서버 구동)

uvicorn(백엔드) + Vite(프론트엔드) + PostgreSQL 16을 실제 기동하여 확인:

1. 초기 admin 계정 생성 (`python -m app.initial_data`) — 정상
2. API: 로그인 → 고객사 등록 → 프로젝트 등록 → 상태 변경(PLANNED→IN_PROGRESS) → 변경 이력 조회 — 정상
3. UI(Chromium): 로그인 화면 → 로그인 → 프로젝트 목록 → 프로젝트 상세(기본정보, 상태 변경 버튼, 참여자, 계약, 변경 이력) — 정상 렌더링·동작

## 3. 요구사항 충족 확인

| 요구사항 | 충족 여부 |
|----------|-----------|
| REQ-AUTH-001~005 | 충족 (JWT, refresh, bcrypt, 역할, 비활성화) |
| REQ-CUST-001~003 | 충족 (등록/수정, 담당자 복수, 논리 삭제) |
| REQ-PROJ-001~006 | 충족 (CRUD, 유형, 상태 전이, 참여자, 계약, 코드 중복 409) |
| REQ-COM-001~003 | 충족 (change_logs 기록, 예외 처리·로그, 프로젝트 중심 연결) |

## 4. 잔여 사항 (확인 필요)

- 로그인 실패 횟수 제한(계정 잠금) — 미구현, 요구 여부 **확인 필요**
- 운영 배포 환경(HTTPS, 서버) — **확인 필요**
- CI(GitHub Actions)는 저장소 push 시 자동 실행되도록 구성함 (.github/workflows/ci.yml) — 원격 실행 결과는 GitHub에서 확인
