# 검증 문서 (verification.md)

## Phase 2 검증 결과 — 일정 관리

- 검증일: 2026-07-07
- 상태: **검증 완료**

### 시험 결과

- 백엔드 pytest **48건 전체 통과** (Phase 2 신규 12건 포함), 커버리지 93%
- 프론트 빌드(TypeScript 타입 검사)·Vitest 통과

| 계획 ID | 수행 테스트 (tests/test_schedule_api.py) | 결과 |
|---------|------------------------------------------|------|
| UT-WBS-01 | TestWbsCrud::test_hierarchy_and_history, test_parent_from_other_project_rejected | 통과 |
| UT-WBS-02 | TestWbsCrud::test_self_and_circular_parent_rejected | 통과 |
| UT-WBS-03 | TestWbsCrud::test_progress_100_marks_done | 통과 |
| UT-WBS-04 | TestWbsCrud::test_delay_computation | 통과 |
| UT-WBS-05 | TestWbsCrud::test_deactivate_cascades_children | 통과 |
| UT-MS-01 | TestMilestone::test_milestone_flow | 통과 |
| UT-SCH-01 | TestScheduleSummary::test_summary | 통과 |
| IT-09 | TestWbsCrud::test_hierarchy_and_history (change_logs 확인 포함) | 통과 |
| IT-10 | TestAssigneePermission::test_assignee_updates_own_progress | 통과 |
| IT-11 | TestWbsCrud::test_member_cannot_create | 통과 |
| IT-12 | TestScheduleSummary::test_summary | 통과 |

### E2E 수동 검증

실서버(uvicorn + Vite + PostgreSQL 16) 기동 후 확인:

1. API: WBS 계층 등록 → 요약 조회(진척률 50%, WBS 지연 1건, 마일스톤 지연 1건) — 계산값 정상
2. UI: 프로젝트 상세 내 일정 섹션 — WBS 계층 들여쓰기, 지연 배지, 진척률 인라인 수정, 마일스톤 달성 처리 버튼 정상 렌더링

### 요구사항 충족

| 요구사항 | 충족 여부 |
|----------|-----------|
| REQ-WBS-001~008 | 충족 (계층, 담당자·기간·진척률·상태, 지연 판정, 이력, 논리삭제 연쇄, 100%→완료, 담당자 본인 수정) |
| REQ-MS-001~003 | 충족 (등록/수정, 달성 처리·달성일, 지연 판정) |
| REQ-SCH-001 | 충족 (진척률 평균·지연 수, 비활성 제외) |

---

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
