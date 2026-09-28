import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Response, status, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.auth import (
    criar_token_sessao,
    verificar_token_sessao,
    verificar_credenciais,
    verificar_rate_limit,
    registrar_falha_login,
    limpar_falhas_login,
)
from app.schemas.invoice import ExtracaoNotaFiscalResponse
from app.services.gemini_service import extrair_dados_nota_fiscal

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Sistema de Gestão Financeira Rural - Processador de Notas",
    description="Web Service acadêmico seguro para extração e classificação de notas fiscais via IA Gemini",
    version="2.0.0"
)

# -------------------------------------------------------------
# Middleware de Segurança: Headers HTTP
# -------------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    # Prevenção contra Clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Prevenção contra MIME Sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Política de Referrer segura
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Proteção XSS básica para browsers legados
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Configuração de arquivos estáticos e templates Jinja2
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# -------------------------------------------------------------
# Utilitários de Autenticação e Sessão
# -------------------------------------------------------------
def obter_usuario_sessao(request: Request) -> Optional[str]:
    """Extrai e valida o token de sessão a partir do cookie protegido."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    return verificar_token_sessao(token)


class LoginRequest(BaseModel):
    usuario: str
    senha: str


# -------------------------------------------------------------
# Rotas de Autenticação e Páginas
# -------------------------------------------------------------
@app.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request):
    """Renderiza a página de login. Se já autenticado, redireciona ao painel."""
    usuario = obter_usuario_sessao(request)
    if usuario:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/api/login")
async def efetuar_login(request: Request, credenciais: LoginRequest):
    """
    Endpoint seguro de login:
    - Proteção contra ataques de força bruta por IP (Rate Limiting).
    - Validação de credenciais em tempo constante (evita timing attacks).
    - Emissão de cookie HttpOnly e SameSite assinado criptograficamente.
    """
    ip_cliente = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")

    # Verifica limite de tentativas por IP
    if not verificar_rate_limit(ip_cliente):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas incorretas. Por motivos de segurança, aguarde 1 minuto."
        )

    # Valida credenciais
    if not verificar_credenciais(credenciais.usuario, credenciais.senha):
        registrar_falha_login(ip_cliente)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos."
        )

    # Login bem-sucedido
    limpar_falhas_login(ip_cliente)
    token = criar_token_sessao(credenciais.usuario)

    # Detecta se a requisição é HTTPS (direta ou atrás do proxy reverso do Render)
    eh_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"

    # Cookie com flags de segurança rigorosas (HttpOnly, SameSite=Lax, Path=/)
    resposta = JSONResponse(content={"success": True, "usuario": credenciais.usuario})
    resposta.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_EXPIRATION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=eh_https,
        path="/"
    )
    return resposta


@app.post("/api/logout")
async def efetuar_logout():
    """Invalida a sessão do usuário removendo o cookie de autenticação."""
    resposta = JSONResponse(content={"success": True, "mensagem": "Sessão encerrada com sucesso."})
    resposta.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return resposta


@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request):
    """Painel principal de upload e extração. Requer autenticação ativa."""
    usuario = obter_usuario_sessao(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "usuario": usuario
        }
    )


@app.get("/api/status")
async def verificar_status(request: Request):
    """Informa se o serviço está online e se a sessão do usuário é válida."""
    usuario = obter_usuario_sessao(request)
    return {
        "status": "online",
        "autenticado": bool(usuario),
        "usuario": usuario or "anonimo"
    }


# -------------------------------------------------------------
# Processamento de Notas Fiscais com Chave Volátil
# -------------------------------------------------------------
@app.post(
    "/api/processar-nota",
    response_model=ExtracaoNotaFiscalResponse,
    summary="Processa PDF de Nota Fiscal com Gemini usando chave em memória",
    description="Recebe o PDF e a chave volátil via cabeçalho X-Gemini-API-Key, sem gravar a chave no servidor."
)
async def processar_nota(
    request: Request,
    arquivo: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    # 1. Autenticação obrigatória
    usuario = obter_usuario_sessao(request)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado. Por favor, faça login para utilizar este serviço."
        )

    # 2. Verificação da chave da API do Gemini (deve ser informada pelo usuário)
    chave_gemini = (x_gemini_api_key or "").strip() or settings.GEMINI_API_KEY
    if not chave_gemini:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chave de API do Gemini não fornecida. Por favor, informe sua chave no painel antes de extrair os dados."
        )

    # 3. Validação do formato e nome do arquivo
    nome_arquivo = arquivo.filename or "arquivo.pdf"
    if not nome_arquivo.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Por favor, envie um arquivo com extensão .PDF."
        )

    # 4. Leitura em memória e validação de tamanho (máximo 10 MB)
    conteudo_pdf = await arquivo.read()
    if len(conteudo_pdf) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O arquivo PDF enviado está vazio.")
    
    if len(conteudo_pdf) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo muito grande. O limite máximo permitido é de {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )

    # 5. Validação de Magic Bytes (%PDF-) para impedir scripts ou binários camuflados
    if not conteudo_pdf.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido. O conteúdo não corresponde a um documento PDF genuíno."
        )

    # 6. Extração com a IA utilizando a chave em memória RAM (sem gravação)
    try:
        resultado = extrair_dados_nota_fiscal(
            pdf_bytes=conteudo_pdf,
            api_key=chave_gemini,
            filename=nome_arquivo
        )
        return resultado
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(re))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante o processamento da nota fiscal: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
