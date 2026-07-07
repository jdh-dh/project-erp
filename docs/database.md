# 데이터베이스 설계서 (database.md)

## 1. 개요

Phase 1 테이블 설계를 정의한다. PostgreSQL + SQLAlchemy + Alembic 사용.

- 작성일: 2026-07-07
- 상태: 초안 (사용자 승인 대기)

## 2. 공통 규칙

- 모든 테이블: `id` (BIGSERIAL PK), `created_at`, `updated_at` (TIMESTAMPTZ)
- 삭제는 논리 삭제(`is_active` 또는 상태값) 우선. 물리 삭제는 하지 않는다.
- FK는 명시적으로 선언하고 인덱스를 둔다.

## 3. 테이블 정의

### 3.1 users — 사용자

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 로그인 ID |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 해시 |
| name | VARCHAR(100) | NOT NULL | 이름 |
| role | VARCHAR(20) | NOT NULL | admin / manager / member |
| is_active | BOOLEAN | NOT NULL, default true | 비활성화 = 로그인 불가 |

### 3.2 customers — 고객사

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| name | VARCHAR(200) | NOT NULL | 고객사명 |
| business_no | VARCHAR(20) | NULL | 사업자번호 |
| address | VARCHAR(300) | NULL | |
| note | TEXT | NULL | 비고 |
| is_active | BOOLEAN | NOT NULL, default true | |

### 3.3 customer_contacts — 고객사 담당자

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| customer_id | BIGINT | FK → customers.id, NOT NULL | |
| name | VARCHAR(100) | NOT NULL | |
| position | VARCHAR(100) | NULL | 직책 |
| phone | VARCHAR(50) | NULL | |
| email | VARCHAR(255) | NULL | |
| is_active | BOOLEAN | NOT NULL, default true | |

### 3.4 projects — 프로젝트

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| code | VARCHAR(50) | UNIQUE, NOT NULL | 프로젝트 코드 |
| name | VARCHAR(200) | NOT NULL | |
| customer_id | BIGINT | FK → customers.id, NOT NULL | |
| project_type | VARCHAR(10) | NOT NULL | HW / SW / HYBRID |
| status | VARCHAR(20) | NOT NULL, default 'PLANNED' | PLANNED / IN_PROGRESS / ON_HOLD / COMPLETED / CANCELED |
| manager_id | BIGINT | FK → users.id, NOT NULL | PM |
| start_date | DATE | NULL | |
| end_date | DATE | NULL | |
| description | TEXT | NULL | |

### 3.5 project_members — 프로젝트 참여자

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| project_id | BIGINT | FK → projects.id, NOT NULL | |
| user_id | BIGINT | FK → users.id, NOT NULL | |
| role | VARCHAR(50) | NULL | 프로젝트 내 역할 (HW개발, SW개발 등) |

- UNIQUE(project_id, user_id)

### 3.6 contracts — 계약

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| project_id | BIGINT | FK → projects.id, NOT NULL | |
| contract_no | VARCHAR(100) | NOT NULL | 계약번호 |
| amount | NUMERIC(15,0) | NULL | 계약금액(원) |
| signed_date | DATE | NULL | 계약일 |
| start_date | DATE | NULL | |
| end_date | DATE | NULL | |
| status | VARCHAR(20) | NOT NULL, default 'ACTIVE' | ACTIVE / CLOSED / CANCELED |
| note | TEXT | NULL | |

### 3.7 change_logs — 변경 이력 (공통)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| entity_type | VARCHAR(50) | NOT NULL | project / customer / contract / user |
| entity_id | BIGINT | NOT NULL | 대상 레코드 id |
| action | VARCHAR(20) | NOT NULL | CREATE / UPDATE / STATUS_CHANGE / DEACTIVATE |
| changed_by | BIGINT | FK → users.id, NOT NULL | |
| changed_at | TIMESTAMPTZ | NOT NULL, default now() | |
| before_data | JSONB | NULL | 변경 전 |
| after_data | JSONB | NULL | 변경 후 |

- INDEX(entity_type, entity_id)

## 4. 관계 요약

```
customers 1 ── N customer_contacts
customers 1 ── N projects
users     1 ── N projects (manager)
projects  1 ── N project_members N ── 1 users
projects  1 ── N contracts
(모든 엔티티) ── N change_logs
```

## 5. Phase 2 테이블 — 일정 관리

### 5.1 wbs_items — WBS 항목

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| project_id | BIGINT | FK → projects.id, NOT NULL | |
| parent_id | BIGINT | FK → wbs_items.id, NULL | 상위 항목 (NULL = 최상위) |
| name | VARCHAR(200) | NOT NULL | 작업명 |
| assignee_id | BIGINT | FK → users.id, NULL | 담당자 |
| start_date | DATE | NULL | 계획 시작일 |
| end_date | DATE | NULL | 계획 종료일 |
| progress | SMALLINT | NOT NULL, default 0 | 진척률 0~100 |
| status | VARCHAR(20) | NOT NULL, default 'TODO' | TODO / IN_PROGRESS / DONE |
| sort_order | INTEGER | NOT NULL, default 0 | 같은 계층 내 정렬 순서 |
| is_active | BOOLEAN | NOT NULL, default true | 논리 삭제 |

- INDEX(project_id), INDEX(parent_id)
- **지연 판정(is_delayed)**: `end_date < 오늘 AND status != 'DONE'` — 컬럼이 아닌 계산 필드

### 5.2 milestones — 마일스톤

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| project_id | BIGINT | FK → projects.id, NOT NULL | |
| name | VARCHAR(200) | NOT NULL | |
| due_date | DATE | NOT NULL | 목표일 |
| status | VARCHAR(20) | NOT NULL, default 'PENDING' | PENDING / ACHIEVED |
| achieved_date | DATE | NULL | 달성일 |
| note | TEXT | NULL | |
| is_active | BOOLEAN | NOT NULL, default true | 논리 삭제 |

- INDEX(project_id)
- **지연 판정**: `due_date < 오늘 AND status = 'PENDING'` — 계산 필드

## 6. 확장 고려 (Phase 3+)

- Phase 3: hw_boards, sw_modules, sw_versions 등도 projects.id 기준으로 연결 → "프로젝트 중심 추적" 원칙 유지.
