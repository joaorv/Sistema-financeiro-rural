import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    @property
    def GEMINI_API_KEY(self) -> str:
        load_dotenv(BASE_DIR / ".env", override=True)
        return os.getenv("GEMINI_API_KEY", "").strip()
    
    # Validação rápida de configuração
    @property
    def is_gemini_configured(self) -> bool:
        key = self.GEMINI_API_KEY
        return bool(key and key != "sua_chave_aqui" and key != "sua_chave")

settings = Settings()
