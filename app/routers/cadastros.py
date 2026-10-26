"""
API REST dos cadastros: Pessoas, Classificações e Contas (Movimento + Parcelas).

Regras de negócio:
  - GET sem filtro de status traz apenas ATIVOS ("TODOS" na tela).
  - POST grava sempre com status ATIVO.
  - PUT não altera o status.
  - DELETE não exclui: altera o status para INATIVO.
  - POST /{id}/reativar volta o status para ATIVO.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import STATUS_ATIVO, Classificacao, Pessoa
from app.dependencies import exigir_usuario
from app.repositories import ClassificacaoRepository, MovimentoRepository, PessoaRepository
from app.schemas.cadastros import (
    ClassificacaoIn,
    ClassificacaoOut,
    ContaIn,
    ContaOut,
    PessoaIn,
    PessoaOut,
)
from app.services.conta_service import salvar_conta
from app.services.erros import RegraNegocioError

router = APIRouter(prefix="/api", dependencies=[Depends(exigir_usuario)])

FiltroStatus = Query("ATIVO", alias="status", pattern="^(ATIVO|INATIVO|TODOS)$")


def _ou_404(obj, nome: str):
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{nome} não encontrado(a).")
    return obj


# =============================================================
# PESSOAS (Manter Fornecedor / Cliente / Faturado)
# =============================================================
@router.get("/pessoas", response_model=List[PessoaOut], tags=["Pessoas"])
def listar_pessoas(
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    status_: str = FiltroStatus,
    db: Session = Depends(get_db),
):
    return PessoaRepository(db).listar(busca=busca, tipo=tipo, status=status_)


@router.get("/pessoas/{id_}", response_model=PessoaOut, tags=["Pessoas"])
def obter_pessoa(id_: int, db: Session = Depends(get_db)):
    return _ou_404(PessoaRepository(db).obter(id_), "Pessoa")


@router.post("/pessoas", response_model=PessoaOut, status_code=201, tags=["Pessoas"])
def criar_pessoa(dados: PessoaIn, db: Session = Depends(get_db)):
    repo = PessoaRepository(db)
    if repo.documento_em_uso(dados.documento, dados.tipo):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Já existe um {dados.tipo.lower()} com este documento.")
    pessoa = repo.adicionar(Pessoa(**dados.model_dump(), status=STATUS_ATIVO))
    db.commit()
    return pessoa


@router.put("/pessoas/{id_}", response_model=PessoaOut, tags=["Pessoas"])
def atualizar_pessoa(id_: int, dados: PessoaIn, db: Session = Depends(get_db)):
    repo = PessoaRepository(db)
    pessoa = _ou_404(repo.obter(id_), "Pessoa")
    if repo.documento_em_uso(dados.documento, dados.tipo, ignorar_id=id_):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Já existe um {dados.tipo.lower()} com este documento.")
    for campo, valor in dados.model_dump().items():
        setattr(pessoa, campo, valor)
    db.commit()
    return pessoa


@router.delete("/pessoas/{id_}", response_model=PessoaOut, tags=["Pessoas"])
def inativar_pessoa(id_: int, db: Session = Depends(get_db)):
    repo = PessoaRepository(db)
    pessoa = repo.inativar(_ou_404(repo.obter(id_), "Pessoa"))
    db.commit()
    return pessoa


@router.post("/pessoas/{id_}/reativar", response_model=PessoaOut, tags=["Pessoas"])
def reativar_pessoa(id_: int, db: Session = Depends(get_db)):
    repo = PessoaRepository(db)
    pessoa = repo.reativar(_ou_404(repo.obter(id_), "Pessoa"))
    db.commit()
    return pessoa


# =============================================================
# CLASSIFICAÇÃO (Manter Tipo de Despesa / Tipo de Receita)
# =============================================================
@router.get("/classificacoes", response_model=List[ClassificacaoOut], tags=["Classificações"])
def listar_classificacoes(
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    status_: str = FiltroStatus,
    db: Session = Depends(get_db),
):
    return ClassificacaoRepository(db).listar(busca=busca, tipo=tipo, status=status_)


@router.get("/classificacoes/{id_}", response_model=ClassificacaoOut, tags=["Classificações"])
def obter_classificacao(id_: int, db: Session = Depends(get_db)):
    return _ou_404(ClassificacaoRepository(db).obter(id_), "Classificação")


@router.post("/classificacoes", response_model=ClassificacaoOut, status_code=201, tags=["Classificações"])
def criar_classificacao(dados: ClassificacaoIn, db: Session = Depends(get_db)):
    repo = ClassificacaoRepository(db)
    if repo.buscar_por_descricao(dados.descricao, dados.tipo):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Já existe um tipo de {dados.tipo.lower()} com esta descrição.")
    classificacao = repo.adicionar(Classificacao(**dados.model_dump(), status=STATUS_ATIVO))
    db.commit()
    return classificacao


@router.put("/classificacoes/{id_}", response_model=ClassificacaoOut, tags=["Classificações"])
def atualizar_classificacao(id_: int, dados: ClassificacaoIn, db: Session = Depends(get_db)):
    repo = ClassificacaoRepository(db)
    classificacao = _ou_404(repo.obter(id_), "Classificação")
    existente = repo.buscar_por_descricao(dados.descricao, dados.tipo)
    if existente and existente.id != id_:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Já existe um tipo de {dados.tipo.lower()} com esta descrição.")
    classificacao.tipo = dados.tipo
    classificacao.descricao = dados.descricao
    db.commit()
    return classificacao


@router.delete("/classificacoes/{id_}", response_model=ClassificacaoOut, tags=["Classificações"])
def inativar_classificacao(id_: int, db: Session = Depends(get_db)):
    repo = ClassificacaoRepository(db)
    classificacao = repo.inativar(_ou_404(repo.obter(id_), "Classificação"))
    db.commit()
    return classificacao


@router.post("/classificacoes/{id_}/reativar", response_model=ClassificacaoOut, tags=["Classificações"])
def reativar_classificacao(id_: int, db: Session = Depends(get_db)):
    repo = ClassificacaoRepository(db)
    classificacao = repo.reativar(_ou_404(repo.obter(id_), "Classificação"))
    db.commit()
    return classificacao


# =============================================================
# CONTAS (Registrar Contas a Pagar / a Receber)
# =============================================================
@router.get("/contas", response_model=List[ContaOut], tags=["Contas"])
def listar_contas(
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    status_: str = FiltroStatus,
    db: Session = Depends(get_db),
):
    return MovimentoRepository(db).listar(busca=busca, tipo=tipo, status=status_)


@router.get("/contas/{id_}", response_model=ContaOut, tags=["Contas"])
def obter_conta(id_: int, db: Session = Depends(get_db)):
    return _ou_404(MovimentoRepository(db).obter(id_), "Conta")


@router.post("/contas", response_model=ContaOut, status_code=201, tags=["Contas"])
def criar_conta(dados: ContaIn, db: Session = Depends(get_db)):
    movimento = salvar_conta(db, dados)
    db.commit()
    return MovimentoRepository(db).obter(movimento.id)


@router.put("/contas/{id_}", response_model=ContaOut, tags=["Contas"])
def atualizar_conta(id_: int, dados: ContaIn, db: Session = Depends(get_db)):
    repo = MovimentoRepository(db)
    salvar_conta(db, dados, _ou_404(repo.obter(id_), "Conta"))
    db.commit()
    return repo.obter(id_)


@router.delete("/contas/{id_}", response_model=ContaOut, tags=["Contas"])
def inativar_conta(id_: int, db: Session = Depends(get_db)):
    repo = MovimentoRepository(db)
    repo.inativar(_ou_404(repo.obter(id_), "Conta"))
    db.commit()
    return repo.obter(id_)


@router.post("/contas/{id_}/reativar", response_model=ContaOut, tags=["Contas"])
def reativar_conta(id_: int, db: Session = Depends(get_db)):
    repo = MovimentoRepository(db)
    movimento = _ou_404(repo.obter(id_), "Conta")
    duplicado = repo.buscar_duplicado(movimento.tipo, movimento.numero_nota_fiscal, movimento.pessoa_id)
    if duplicado and duplicado.id != id_:
        raise RegraNegocioError(
            f"Não é possível reativar: a nota já está lançada no registro ativo ID {duplicado.id}.", 409
        )
    repo.reativar(movimento)
    db.commit()
    return repo.obter(id_)
