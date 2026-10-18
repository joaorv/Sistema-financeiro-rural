from typing import Optional

from fastapi import HTTPException, Request, status

from app.auth import verificar_token_sessao
from app.config import settings


def obter_usuario_sessao(request: Request) -> Optional[str]:
    """Extrai e valida o token de sessão a partir do cookie protegido."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    return verificar_token_sessao(token)


def exigir_usuario(request: Request) -> str:
    """Dependência das rotas de API: exige sessão válida (401 caso contrário)."""
    usuario = obter_usuario_sessao(request)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado. Por favor, faça login para utilizar este serviço.",
        )
    return usuario
