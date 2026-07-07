"""애플리케이션 설정. 환경변수(ERP_ 프리픽스) 또는 .env 파일로 재정의한다."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ERP_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://erp:erp@localhost:5432/erp"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # 초기 admin 계정 (initial_data.py 에서 사용)
    admin_email: str = "admin@example.com"
    admin_password: str = "admin1234"
    admin_name: str = "관리자"


settings = Settings()
