import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, List

from app.config import settings

# Armazenamento em memória para proteção contra ataques de força bruta (Rate Limiting)
# Mapeia IP -> lista de timestamps de falhas nos últimos 60 segundos
_TENTATIVAS_FALHAS: Dict[str, List[float]] = {}
MAX_TENTATIVAS_POR_MINUTO = 5
JANELA_TEMPO_SEGUNDOS = 60


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data_str: str) -> bytes:
    padding = "=" * ((4 - len(data_str) % 4) % 4)
    return base64.urlsafe_b64decode(data_str + padding)


def criar_token_sessao(username: str) -> str:
    """Gera um token de sessão assinado criptograficamente com HMAC-SHA256."""
    agora = int(time.time())
    expiracao = agora + (settings.SESSION_EXPIRATION_HOURS * 3600)
    
    payload = {
        "sub": username,
        "iat": agora,
        "exp": expiracao,
        "rnd": secrets.token_hex(8)
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    payload_b64 = _b64_encode(payload_bytes)
    
    assinatura = hmac.new(
        settings.SESSION_SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).digest()
    assinatura_b64 = _b64_encode(assinatura)
    
    return f"{payload_b64}.{assinatura_b64}"


def verificar_token_sessao(token: Optional[str]) -> Optional[str]:
    """
    Verifica a autenticidade e validade do token de sessão.
    Retorna o nome do usuário se válido, ou None se inválido/expirado.
    """
    if not token or "." not in token:
        return None
    
    try:
        payload_b64, assinatura_b64 = token.split(".", 1)
        
        # Recalcula a assinatura esperada
        assinatura_esperada = hmac.new(
            settings.SESSION_SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).digest()
        assinatura_recebida = _b64_decode(assinatura_b64)
        
        # Comparação em tempo constante (previne timing attacks)
        if not hmac.compare_digest(assinatura_esperada, assinatura_recebida):
            return None
        
        # Decodifica payload e valida expiração
        payload = json.loads(_b64_decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        
        return payload.get("sub")
    except Exception:
        return None


def verificar_credenciais(usuario: str, senha: str) -> bool:
    """Compara usuário e senha utilizando tempo constante para evitar timing attacks."""
    user_ok = secrets.compare_digest(usuario.strip(), settings.AUTH_USERNAME.strip())
    pass_ok = secrets.compare_digest(senha.strip(), settings.AUTH_PASSWORD.strip())
    return user_ok and pass_ok


def verificar_rate_limit(ip: str) -> bool:
    """Verifica se o IP excedeu o limite de tentativas de login por minuto."""
    agora = time.time()
    falhas = _TENTATIVAS_FALHAS.get(ip, [])
    # Filtra apenas tentativas dentro da janela de 60s
    falhas_recentes = [t for t in falhas if agora - t < JANELA_TEMPO_SEGUNDOS]
    _TENTATIVAS_FALHAS[ip] = falhas_recentes
    return len(falhas_recentes) < MAX_TENTATIVAS_POR_MINUTO


def registrar_falha_login(ip: str) -> None:
    """Registra uma falha de tentativa de login para o IP informado."""
    agora = time.time()
    falhas = _TENTATIVAS_FALHAS.get(ip, [])
    falhas.append(agora)
    _TENTATIVAS_FALHAS[ip] = [t for t in falhas if agora - t < JANELA_TEMPO_SEGUNDOS]


def limpar_falhas_login(ip: str) -> None:
    """Limpa o histórico de falhas ao efetuar login com sucesso."""
    if ip in _TENTATIVAS_FALHAS:
        del _TENTATIVAS_FALHAS[ip]
