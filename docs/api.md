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

## 7. 변경 이력 (change-logs)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | /api/change-logs | 변경 이력 조회 (필터: entity_type, entity_id) | 로그인 |

## 8. 확인 필요

- 로그인 실패 횟수 제한(계정 잠금) 필요 여부 → **확인 필요**
