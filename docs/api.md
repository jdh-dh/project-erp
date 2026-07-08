# API 설계서 (api.md)

## 1. 개요

Phase 1 REST API를 정의한다. 모든 경로는 `/api` 프리픽스를 갖는다.

- 작성일: 2026-07-07
- 상태: 초안 (사용자 승인 대기)

## 2. 공통 규칙

- 인증: `Authorization: Bearer <access_token>` (로그인·토큰 재발급 제외)
- 응답: 성공 시 데이터 본문, 오류 시 아래 형식

```json
{ "detail": "오류 메시지", "code": "ERROR_CODE" }
```

- 목록 API는 페이지네이션: `?page=1&size=20` → `{ "items": [...], "total": 123, "page": 1, "size": 20 }`
- 주요 상태 코드: 200 / 201 / 400(검증) / 401(인증) / 403(권한) / 404 / 409(중복)

## 3. 인증 (auth)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | /api/auth/login | 로그인, Access+Refresh 토큰 발급 | 공개 |
| POST | /api/auth/refresh | Access 토큰 재발급 | Refresh 토큰 |
| GET | /api/auth/me | 내 정보 조회 | 로그인 |

## 4. 사용자 (users)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/users | 사용자 목록 | admin, manager |
| POST | /api/users | 사용자 등록 | admin |
| GET | /api/users/{id} | 사용자 상세 | admin, manager |
| PATCH | /api/users/{id} | 사용자 수정 (이름, 역할, 비밀번호) | admin |
| PATCH | /api/users/{id}/deactivate | 비활성화 | admin |

## 5. 고객사 (customers)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/customers | 고객사 목록 (이름 검색: ?q=) | 로그인 |
| POST | /api/customers | 고객사 등록 | admin, manager |
| GET | /api/customers/{id} | 상세 (담당자 포함) | 로그인 |
| PATCH | /api/customers/{id} | 수정 | admin, manager |
| PATCH | /api/customers/{id}/deactivate | 비활성화 | admin, manager |
| POST | /api/customers/{id}/contacts | 담당자 추가 | admin, manager |
| PATCH | /api/customers/{id}/contacts/{contact_id} | 담당자 수정 | admin, manager |

## 6. 프로젝트 (projects)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/projects | 프로젝트 목록 (필터: status, customer_id, ?q=) | 로그인 |
| POST | /api/projects | 프로젝트 등록 (code 중복 시 409) | admin, manager |
| GET | /api/projects/{id} | 상세 (참여자, 계약 포함) | 로그인 |
| PATCH | /api/projects/{id} | 수정 | admin, manager |
| PATCH | /api/projects/{id}/status | 상태 변경 (전이 규칙 검증) | admin, manager |
| PUT | /api/projects/{id}/members | 참여자 일괄 설정 | admin, manager |
| POST | /api/projects/{id}/contracts | 계약 등록 | admin, manager |
| PATCH | /api/projects/{id}/contracts/{contract_id} | 계약 수정 | admin, manager |

### 상태 전이 규칙

```
PLANNED → IN_PROGRESS, CANCELED
IN_PROGRESS → ON_HOLD, COMPLETED, CANCELED
ON_HOLD → IN_PROGRESS, CANCELED
COMPLETED, CANCELED → (전이 불가)
```

## 6.5 일정 관리 (Phase 2)

### WBS

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/projects/{id}/wbs | WBS 목록 (활성 항목, 계층 정렬, is_delayed 포함) | 로그인 |
| POST | /api/projects/{id}/wbs | WBS 항목 등록 | admin, manager |
| PATCH | /api/projects/{id}/wbs/{item_id} | 항목 수정 (이름, 담당자, 기간, 진척률, 상태, 순서) | admin, manager, 담당자 본인(진척률·상태만) |
| PATCH | /api/projects/{id}/wbs/{item_id}/deactivate | 논리 삭제 (하위 항목 포함) | admin, manager |

- 진척률 100 입력 시 상태를 DONE으로 자동 처리 (REQ-WBS-007)
- parent_id는 같은 프로젝트의 활성 항목만 지정 가능, 자기 자신·순환 참조 거부
- 기간(start_date/end_date) 변경 시 change_logs에 UPDATE 기록 (REQ-WBS-005)

### 마일스톤

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/projects/{id}/milestones | 마일스톤 목록 (is_delayed 포함) | 로그인 |
| POST | /api/projects/{id}/milestones | 등록 | admin, manager |
| PATCH | /api/projects/{id}/milestones/{ms_id} | 수정 | admin, manager |
| PATCH | /api/projects/{id}/milestones/{ms_id}/achieve | 달성 처리 (달성일 기록) | admin, manager |
| PATCH | /api/projects/{id}/milestones/{ms_id}/deactivate | 논리 삭제 | admin, manager |

### 일정 요약

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/projects/{id}/schedule/summary | 전체 진척률, WBS 지연 수, 마일스톤 지연 수 | 로그인 |

응답 예:

```json
{ "progress": 42.5, "wbs_total": 8, "wbs_delayed": 2, "milestone_total": 3, "milestone_delayed": 1 }
```

## 6.6 하드웨어 관리 (Phase 3)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/projects/{id}/hw/boards | 보드 목록 (활성) | 로그인 |
| POST | /api/projects/{id}/hw/boards | 보드 등록 (이름+리비전 중복 시 409) | admin, manager |
| GET | /api/projects/{id}/hw/boards/{board_id} | 보드 상세 (BOM, 제작 이력 포함) | 로그인 |
| PATCH | /api/projects/{id}/hw/boards/{board_id} | 보드 수정 (상태 포함) | admin, manager |
| PATCH | /api/projects/{id}/hw/boards/{board_id}/deactivate | 논리 삭제 (BOM 연쇄) | admin, manager |
| POST | /api/projects/{id}/hw/boards/{board_id}/bom | BOM 부품 추가 | admin, manager |
| PATCH | /api/projects/{id}/hw/boards/{board_id}/bom/{item_id} | BOM 부품 수정 | admin, manager |
| PATCH | /api/projects/{id}/hw/boards/{board_id}/bom/{item_id}/deactivate | BOM 부품 삭제 | admin, manager |
| POST | /api/projects/{id}/hw/boards/{board_id}/fabrications | 제작 이력 추가 | admin, manager |

## 6.7 소프트웨어 관리 (Phase 3)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/projects/{id}/sw/modules | 모듈 목록 | 로그인 |
| POST | /api/projects/{id}/sw/modules | 모듈 등록 (이름 중복 시 409) | admin, manager |
| GET | /api/projects/{id}/sw/modules/{module_id} | 모듈 상세 (버전 목록 포함) | 로그인 |
| PATCH | /api/projects/{id}/sw/modules/{module_id} | 모듈 수정 | admin, manager |
| PATCH | /api/projects/{id}/sw/modules/{module_id}/deactivate | 논리 삭제 | admin, manager |
| POST | /api/projects/{id}/sw/modules/{module_id}/versions | 버전 등록 (중복 시 409) | admin, manager |
| GET | /api/projects/{id}/sw/modules/{module_id}/versions/{version_id} | 버전 상세 (빌드/배포 이력 포함) | 로그인 |
| PATCH | /api/projects/{id}/sw/modules/{module_id}/versions/{version_id} | 버전 수정 | admin, manager |
| PATCH | .../versions/{version_id}/release | 릴리즈 처리 (릴리즈일 기록, 중복 릴리즈 400) | admin, manager |
| POST | .../versions/{version_id}/builds | 빌드 이력 추가 (커밋 해시 포함) | admin, manager |
| POST | .../versions/{version_id}/deployments | 배포 이력 추가 | admin, manager |

## 7. 변경 이력 (change-logs)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/change-logs | 변경 이력 조회 (필터: entity_type, entity_id) | 로그인 |

## 8. 확인 필요

- 로그인 실패 횟수 제한(계정 잠금) 필요 여부 → **확인 필요**
