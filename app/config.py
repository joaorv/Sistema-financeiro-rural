import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{(BASE_DIR / 'rural.db').as_posix()}"
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Autenticação do sistema
    AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD: str = os.getenv("AUTH_PASSWORD", "rural2026!")
    SESSION_COOKIE_NAME: str = "rural_session_token"
    SESSION_EXPIRATION_HOURS: int = 24
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "").strip() or secrets.token_hex(32)

    DATABASE_URL: str = _database_url()
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()

    # Informações de versão / Commit para avaliação
    GITHUB_COMMIT_HASH: str = os.getenv("GITHUB_COMMIT_HASH", "").strip()
    GITHUB_REPO_URL: str = os.getenv("GITHUB_REPO_URL", "https://github.com/joaorv/Sistema-financeiro-rural").strip().rstrip("/")

    @property
    def commit_url(self) -> str:
        if self.GITHUB_COMMIT_HASH and self.GITHUB_REPO_URL:
            return f"{self.GITHUB_REPO_URL}/commit/{self.GITHUB_COMMIT_HASH}"
        return ""


settings = Settings()
