# 개발 프로젝트 ERP

하드웨어·소프트웨어 개발 프로젝트를 통합 관리하는 웹 기반 ERP 시스템.

## 기술 스택

- **Backend**: Python FastAPI, SQLAlchemy 2, Alembic
- **Frontend**: React 18 + TypeScript (Vite)
- **Database**: PostgreSQL 16
- **인증**: JWT (Access + Refresh)
- **배포**: Docker (docker-compose)

## 빠른 시작 (Docker)

```bash
docker compose up --build
```

- 웹: http://localhost (초기 계정: `admin@example.com` / `admin1234`)
- API 문서: http://localhost:8000/docs

운영 환경에서는 `ERP_JWT_SECRET`, `ERP_ADMIN_PASSWORD` 환경변수를 반드시 변경한다.

## 개발 환경

### Backend

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head            # DB 마이그레이션
python -m app.initial_data      # 초기 admin 생성
uvicorn app.main:app --reload   # http://localhost:8000
python -m pytest --cov=app      # 테스트 (erp_test DB 필요)
```

기본 DB 접속: `postgresql+psycopg2://erp:erp@localhost:5432/erp` (환경변수 `ERP_DATABASE_URL`로 변경)

### Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 (API는 8000으로 프록시)
npm run build   # 타입 검사 + 번들
npm test        # Vitest
```

## 문서

| 문서 | 내용 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 개발 지침 |
| [docs/requirements.md](docs/requirements.md) | 요구사항 분석 |
| [docs/architecture.md](docs/architecture.md) | 시스템 설계 |
| [docs/database.md](docs/database.md) | DB 설계 |
| [docs/api.md](docs/api.md) | API 명세 |
| [docs/test_plan.md](docs/test_plan.md) | 시험 계획 |
| [docs/verification.md](docs/verification.md) | 검증 결과 |
| [docs/release_note.md](docs/release_note.md) | 릴리즈 노트 |

## 개발 단계

| Phase | 범위 | 상태 |
|-------|------|------|
| 1 | 인증/사용자, 프로젝트, 고객사 관리 | ✅ 완료 (v0.1.0) |
| 2 | 일정 관리 (WBS, 마일스톤) | ✅ 완료 (v0.2.0) |
| 3 | 하드웨어/소프트웨어 관리 | ✅ 완료 (v0.3.0) |
| 4 | 시험/이슈/문서 관리 | ✅ 완료 (v0.4.0) |
| 5 | 릴리즈, 보고서, 비용·자원 | ✅ 완료 (v0.5.0) |
