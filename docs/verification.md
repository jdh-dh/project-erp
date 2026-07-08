# 검증 문서 (verification.md)

## Phase 5 검증 결과 — 릴리즈 이력/보고서/비용

- 검증일: 2026-07-08
- 상태: **검증 완료**

### 시험 결과

- 백엔드 pytest **76건 전체 통과** (Phase 5 신규 7건 포함), 커버리지 94%
- 프론트 빌드(TypeScript 타입 검사)·Vitest 통과

| 계획 ID | 수행 테스트 (tests/test_phase5_api.py) | 결과 |
|---------|----------------------------------------|------|
| UT-REL-01 | TestReleases::test_release_crud (중복 409, 이력, 삭제 후 재등록 포함) | 통과 |
| UT-COST-01 | TestCosts::test_cost_validation | 통과 |
| UT-COST-02 | TestCosts::test_cost_summary_excludes_inactive | 통과 |
| UT-RPT-01 | TestReport::test_full_report | 통과 |
| IT-19 | TestReport::test_full_report (일정/이슈/시험/HW/SW/릴리즈/비용 전 항목 집계 검증) | 통과 |
| IT-20 | TestReleases/TestCosts::test_member_cannot_create | 통과 |

### E2E 수동 검증

실서버(uvicorn + Vite + PostgreSQL 16) 기동 후 확인:

1. API: 릴리즈 등록 → 비용 2건(자재비/인건비) 등록 → 보고서 조회: 일정(진척률 50%, 지연 1건), 이슈(처리중 1건), 시험(합격 1건), HW/SW 현황, 비용 총액 12,500,000원·분류별 합계 — 전부 정확
2. UI: 프로젝트 보고서 페이지(/projects/1/report) — 기본 정보, 일정/이슈/시험/HW·SW·릴리즈/비용 현황 표, 인쇄 버튼 정상 렌더링

### 요구사항 충족

| 요구사항 | 충족 여부 |
|----------|-----------|
| REQ-REL-001~003 | 충족 (버전 중복 409, 등록자 자동, 이력, 논리삭제) |
| REQ-RPT-001~003 | 충족 (종합 집계, 최근 결과 기준 시험 통계, 실시간 집계) |
| REQ-COST-001~004 | 충족 (분류 5종, 금액 > 0, 총액·분류별 합계, 비활성 제외, 등록자·이력) |

---

## Phase 4 검증 결과 — 시험/이슈/문서 관리

- 검증일: 2026-07-08
- 상태: **검증 완료**

### 시험 결과

- 백엔드 pytest **69건 전체 통과** (Phase 4 신규 9건 포함), 커버리지 94%
- 프론트 빌드(TypeScript 타입 검사)·Vitest 통과

| 계획 ID | 수행 테스트 (tests/test_phase4_api.py) | 결과 |
|---------|----------------------------------------|------|
| UT-TC-01 | TestTestCases::test_case_crud | 통과 |
| UT-TC-02 | TestTestCases::test_runs_and_last_result | 통과 |
| UT-ISS-01 | TestIssues::test_member_creates_issue | 통과 |
| UT-ISS-02 | TestIssues::test_full_flow_with_history (RESOLUTION_REQUIRED, CLOSED 전이 불가 포함) | 통과 |
| UT-ISS-03 | TestIssues::test_assignee_permission | 통과 |
| UT-DOC-01 | TestDocuments::test_document_flow | 통과 |
| UT-DOC-02 | TestDocuments::test_member_cannot_create | 통과 |
| IT-16 | TestTestCases::test_runs_and_last_result | 통과 |
| IT-17 | TestIssues::test_full_flow_with_history | 통과 |
| IT-18 | TestDocuments::test_document_flow | 통과 |

### E2E 수동 검증

실서버(uvicorn + Vite + PostgreSQL 16) 기동 후 확인:

1. API: 시험 케이스 등록 → FAIL/PASS 실행 기록 → 최근 결과 PASS / 이슈 등록 → 처리중 → 원인 분석 / 문서 2건 등록 — 정상
2. UI: 시험 관리(케이스 펼침, 실행 이력 합격/불합격 배지, 결과 기록 폼), 이슈 관리(심각도·상태 배지, 상세 펼침), 문서 관리 섹션 정상 렌더링

### 요구사항 충족

| 요구사항 | 충족 여부 |
|----------|-----------|
| REQ-TEST-001~005 | 충족 (케이스 CRUD, 유형, 실행 기록·시험자 자동, 최근 결과, 논리삭제·이력) |
| REQ-ISS-001~008 | 충족 (유형·심각도, 상태 전이, RESOLVED 조치결과 필수·해결일, member 등록, 담당자 권한, 이력) |
| REQ-DOC-001~005 | 충족 (유형, 버전, 링크 URL, 작성자 자동, 이력, 권한, 논리삭제) |

### 잔여 사항

- 문서 파일 업로드(저장소) — 링크 방식으로 대체, 필요 여부 **확인 필요**

---

## Phase 3 검증 결과 — 하드웨어/소프트웨어 관리

- 검증일: 2026-07-08
- 상태: **검증 완료**

### 시험 결과

- 백엔드 pytest **60건 전체 통과** (Phase 3 신규 12건 포함), 커버리지 93% (서비스 계층 80% 이상)
- 프론트 빌드(TypeScript 타입 검사)·Vitest 통과

| 계획 ID | 수행 테스트 | 결과 |
|---------|-------------|------|
| UT-HW-01 | test_hardware_api.py::TestBoard::test_create_and_duplicate, test_status_change | 통과 |
| UT-HW-02 | TestBoard::test_bom_update_and_validation | 통과 |
| UT-HW-03 | TestBoard::test_deactivate_cascades_bom | 통과 |
| UT-HW-04 | TestBoard::test_full_flow_with_history | 통과 |
| UT-SW-01 | test_software_api.py::TestModule::test_create_and_duplicate, TestVersion::test_deactivate_module_hides_versions | 통과 |
| UT-SW-02 | TestVersion::test_version_duplicate | 통과 |
| UT-SW-03 | TestVersion::test_release | 통과 |
| UT-SW-04 | TestVersion::test_full_flow | 통과 |
| IT-13 | TestBoard::test_full_flow_with_history | 통과 |
| IT-14 | TestVersion::test_full_flow | 통과 |
| IT-15 | TestBoard/TestModule::test_member_cannot_create | 통과 |

### E2E 수동 검증

실서버(uvicorn + Vite + PostgreSQL 16) 기동 후 확인:

1. API: 보드 등록 → BOM 2건 → 제작 이력 → 모듈 등록(GitHub URL) → 버전 → 빌드(커밋 해시) → 배포(FIELD) → 릴리즈 처리(릴리즈일 기록) — 정상
2. UI: 프로젝트 상세의 하드웨어/소프트웨어 섹션 — 보드 펼침(BOM·제작 이력·추가 폼), 모듈 펼침(버전·릴리즈 배지), 버전 펼침(빌드·배포 이력) 정상 렌더링

### 요구사항 충족

| 요구사항 | 충족 여부 |
|----------|-----------|
| REQ-HW-001~007 | 충족 (보드 CRUD, 상태, 이름+리비전 중복 409, BOM, 제작 이력, 이력 기록, 논리삭제 연쇄) |
| REQ-SW-001~009 | 충족 (모듈 CRUD, 유형, 중복 409, 버전, 릴리즈 처리, 빌드/배포 이력, repo_url·커밋 해시, 논리삭제) |

### 잔여 사항

- GitHub API 실연동(커밋/릴리즈 자동 조회)은 저장소 URL·커밋 해시 기록으로 대체 — 실연동 필요 여부 **확인 필요**

---

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
