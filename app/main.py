import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.schemas.invoice import ExtracaoNotaFiscalResponse
from app.services.gemini_service import extrair_dados_nota_fiscal

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Sistema de Gestão Financeira - Processador de Notas Fiscais",
    description="Backend FastAPI com extração de PDF via Gemini e Classificação de Despesas do Agronegócio",
    version="1.0.0"
)

# Permite CORS para facilitar integrações e testes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de arquivos estáticos e templates Jinja2
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request):
    """Renderiza a interface web principal de upload e extração da nota fiscal."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "gemini_configurado": settings.is_gemini_configured
        }
    )


@app.get("/api/status")
async def verificar_status():
    """Retorna o status da aplicação e a verificação da chave do Gemini."""
    return {
        "status": "online",
        "gemini_configurado": settings.is_gemini_configured,
        "mensagem": (
            "Servidor pronto para processar notas fiscais."
            if settings.is_gemini_configured
            else "Atenção: GEMINI_API_KEY não configurada no arquivo .env."
        )
    }


@app.post(
    "/api/processar-nota",
    response_model=ExtracaoNotaFiscalResponse,
    summary="Processa PDF de Nota Fiscal com Gemini",
    description="Recebe o arquivo PDF da nota fiscal (Contas a Pagar), extrai os campos e classifica a despesa."
)
async def processar_nota(arquivo: UploadFile = File(...)):
    # 1. Validação da extensão e tipo do arquivo
    nome_arquivo = arquivo.filename or "arquivo.pdf"
    if not nome_arquivo.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Por favor, envie um arquivo com extensão .PDF."
        )

    # 2. Leitura dos bytes do arquivo com limite de segurança (máximo 25 MB)
    limite_bytes = 25 * 1024 * 1024
    conteudo_pdf = await arquivo.read()
    
    if len(conteudo_pdf) == 0:
        raise HTTPException(status_code=400, detail="O arquivo PDF enviado está vazio.")
    
    if len(conteudo_pdf) > limite_bytes:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. O tamanho máximo permitido é de 25 MB."
        )

    # 3. Processamento e extração via Gemini
    try:
        resultado = extrair_dados_nota_fiscal(conteudo_pdf, filename=nome_arquivo)
        return resultado
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail=str(re))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar a nota fiscal: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
