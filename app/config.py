import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env na raiz do projeto (se existir)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Autenticação do sistema
    AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD: str = os.getenv("AUTH_PASSWORD", "rural2026!")
    SESSION_COOKIE_NAME: str = "rural_session_token"
    SESSION_EXPIRATION_HOURS: int = 24
    
    _generated_secret: str = ""

    # Chave secreta para assinatura criptográfica de sessão
    # Se não definida ou vazia no ambiente, gera uma chave forte em memória persistente
    @property
    def SESSION_SECRET_KEY(self) -> str:
        secret = os.getenv("SESSION_SECRET_KEY", "").strip()
        if not secret:
            if not self._generated_secret:
                self._generated_secret = secrets.token_hex(32)
            return self._generated_secret
        return secret

    # Limite de segurança para upload de PDF (10 MB)
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

    # Chave global opcional (se informada no servidor atua como fallback,
    # porém a aplicação prioriza a chave volátil fornecida pelo usuário na sessão)
    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()


settings = Settings()
