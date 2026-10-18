"""Páginas HTML dos cadastros (listagem com busca + formulário de inclusão/edição)."""
from typing import Optional

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import obter_usuario_sessao


def criar_router(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter(include_in_schema=False)

    def _render(request: Request, nome: str, menu: str, **contexto):
        usuario = obter_usuario_sessao(request)
        if not usuario:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        return templates.TemplateResponse(
            request=request, name=nome, context={"usuario": usuario, "menu": menu, **contexto}
        )

    # --- Pessoas ---
    @router.get("/pessoas")
    def pessoas_lista(request: Request, tipo: Optional[str] = None):
        return _render(request, "pessoas/lista.html", "pessoas", tipo=(tipo or "").upper())

    @router.get("/pessoas/novo")
    def pessoas_novo(request: Request, tipo: Optional[str] = None):
        return _render(request, "pessoas/form.html", "pessoas", registro_id=None, tipo=(tipo or "").upper())

    @router.get("/pessoas/{id_}/editar")
    def pessoas_editar(request: Request, id_: int):
        return _render(request, "pessoas/form.html", "pessoas", registro_id=id_, tipo="")

    # --- Classificações ---
    @router.get("/classificacoes")
    def classificacoes_lista(request: Request, tipo: Optional[str] = None):
        return _render(request, "classificacoes/lista.html", "classificacoes", tipo=(tipo or "").upper())

    @router.get("/classificacoes/novo")
    def classificacoes_novo(request: Request, tipo: Optional[str] = None):
        return _render(request, "classificacoes/form.html", "classificacoes", registro_id=None, tipo=(tipo or "").upper())

    @router.get("/classificacoes/{id_}/editar")
    def classificacoes_editar(request: Request, id_: int):
        return _render(request, "classificacoes/form.html", "classificacoes", registro_id=id_, tipo="")

    # --- Contas ---
    @router.get("/contas")
    def contas_lista(request: Request, tipo: Optional[str] = None):
        return _render(request, "contas/lista.html", "contas", tipo=(tipo or "").upper())

    @router.get("/contas/novo")
    def contas_novo(request: Request, tipo: Optional[str] = None):
        return _render(request, "contas/form.html", "contas", registro_id=None, tipo=(tipo or "APAGAR").upper())

    @router.get("/contas/{id_}/editar")
    def contas_editar(request: Request, id_: int):
        return _render(request, "contas/form.html", "contas", registro_id=id_, tipo="")

    return router
