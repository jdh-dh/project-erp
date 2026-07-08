# 시스템 설계서 (architecture.md)

## 1. 개요

Phase 1(인증/사용자, 고객사, 프로젝트 관리)의 시스템 구조를 정의한다.

- 작성일: 2026-07-07
- 상태: 초안 (사용자 승인 대기)

## 2. 전체 구조

```
[Browser]
   │  HTTPS
   ▼
[Frontend]  React + TypeScript (Vite)  ── Docker container
   │  REST API (/api/*)
   ▼
[Backend]   FastAPI + SQLAlchemy       ── Docker container
   │
   ▼
[Database]  PostgreSQL                 ── Docker container
```

- 3계층 구조: Frontend / Backend(API) / Database
- 모든 서비스는 docker-compose 로 기동한다.
- 개발 시 Frontend는 Vite dev server, Backend는 uvicorn --reload 를 사용한다.

## 3. 저장소 구조 (모노레포)

```
project-erp/
├── CLAUDE.md
├── docs/                  # 프로젝트 공통 문서
│   ├── requirements.md
│   ├── architecture.md
│   ├── database.md
│   ├── api.md
│   ├── test_plan.md
│   ├── verification.md
│   └── release_note.md
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 앱 생성, 라우터 등록
│   │   ├── core/              # 설정, 보안(JWT), 로깅
│   │   ├── db/                # 세션, Base, Alembic 마이그레이션
│   │   ├── models/            # SQLAlchemy 모델
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── api/               # 라우터 (auth, users, customers, projects)
│   │   ├── services/          # 비즈니스 로직 (라우터와 분리)
│   │   └── utils/
│   ├── tests/                 # pytest 단위·통합시험
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               # API 클라이언트 (axios)
│   │   ├── pages/             # 화면 (로그인, 프로젝트, 고객사, 사용자)
│   │   ├── components/        # 공통 컴포넌트
│   │   ├── hooks/
│   │   └── types/
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## 4. Backend 설계 원칙

- 라우터(api) → 서비스(services) → 모델(models) 계층을 분리한다. 라우터에 비즈니스 로직을 두지 않는다. (단일 책임 원칙)
- 모든 서비스 함수는 예외 처리를 구현하고, 공통 예외 핸들러가 일관된 오류 응답(JSON)을 반환한다.
- 로깅: 요청 단위 로그(method, path, status, 소요시간) + 서비스 오류 로그를 남긴다.
- 변경 이력: 서비스 계층에서 생성·수정·상태변경 시 change_logs 테이블에 기록한다.
- DB 마이그레이션은 Alembic으로 관리한다. 모델 직접 create_all 금지(테스트 제외).

## 5. 인증 설계

- 로그인 성공 시 Access Token(30분) + Refresh Token(14일) 발급.
- Access Token: `Authorization: Bearer <token>` 헤더로 전달.
- 역할(Role) 기반 접근 제어:
  - admin: 사용자 관리 포함 전체
  - manager: 프로젝트·고객사 생성/수정
  - member: 조회 및 본인 담당 항목 수정
- 비밀번호는 bcrypt 해시로 저장한다.

## 6. Frontend 설계 원칙

- React + TypeScript + Vite.
- 상태 관리: 서버 상태는 TanStack Query, 인증 상태는 Context.
- API 오류는 공통 인터셉터에서 처리(401 → 토큰 재발급 → 실패 시 로그인 이동).
- 화면(Phase 1): 로그인, 대시보드(프로젝트 목록), 프로젝트 상세, 고객사 목록/상세, 사용자 관리(admin).

## 7. 영향 범위 분석 (Phase 1)

- 신규 프로젝트이므로 기존 코드 영향 없음.
- Phase 2 이후 기능(WBS, 하드웨어/소프트웨어 관리 등)은 모두 projects 테이블을 참조하므로, projects 스키마를 안정적으로 설계하는 것이 중요하다.

## 7.5 영향 범위 분석 (Phase 2 — 일정 관리)

- **신규 추가**: models(wbs_item, milestone), schemas(schedule), services(schedule_service), api/routes(schedule), Alembic 마이그레이션 1건, 프론트 프로젝트 상세 내 일정 섹션.
- **기존 코드 변경 최소화**:
  - `app/models/__init__.py` — 신규 모델 export 추가만
  - `app/main.py` — 라우터 등록 1줄 추가만
  - `frontend/src/pages/ProjectDetailPage.tsx` — 일정 섹션 컴포넌트 삽입
  - Phase 1 테이블 스키마 변경 없음 → 기존 시험에 영향 없음
- **재사용**: change_log_service(일정 변경 이력), require_roles(권한), Page(페이지네이션 불필요 — 프로젝트당 목록 전체 반환).
- **위험 요소**: WBS 계층의 순환 참조 → 서비스 계층에서 조상 탐색으로 차단. 담당자 본인 수정 권한(REQ-WBS-008)은 라우터가 아닌 서비스에서 필드 단위로 제한.

## 7.6 영향 범위 분석 (Phase 3 — 하드웨어/소프트웨어 관리)

- **신규 추가**: models(hw_board, bom_item, hw_fabrication, sw_module, sw_version, sw_build, sw_deployment), schemas(hardware, software), services(hardware_service, software_service), api/routes(hardware, software), Alembic 마이그레이션 1건, 프론트 HwSection/SwSection 컴포넌트.
- **기존 코드 변경 최소화**: models/__init__.py export 추가, main.py 라우터 등록, ProjectDetailPage에 섹션 삽입. Phase 1·2 스키마 변경 없음 → 기존 시험 영향 없음.
- **재사용**: change_log_service, require_roles, 논리 삭제 패턴(Phase 2와 동일).
- **GitHub 연동 범위**: 1단계는 저장소 URL·커밋 해시 기록. GitHub API 실연동(커밋/릴리즈 자동 조회)은 별도 승인 후 진행 — **확인 필요**.

## 8. 확인 필요

- 배포 대상 서버 환경(사내 서버/클라우드) → **확인 필요**
- HTTPS 인증서 처리 방식(리버스 프록시 유무) → **확인 필요**
