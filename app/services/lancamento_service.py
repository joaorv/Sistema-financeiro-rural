"""
2ª Etapa: análise dos dados extraídos da nota e lançamento da conta a pagar.

Fluxo:
  1. analisar_nota()  -> consulta no banco se FORNECEDOR, FATURADO e DESPESA(s) existem
  2. lancar_nota()    -> cria o que faltar + MOVIMENTO (APAGAR) + PARCELA(S), em uma única transação
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import STATUS_ATIVO, Classificacao, MovimentoContas, Pessoa
from app.repositories import ClassificacaoRepository, MovimentoRepository, PessoaRepository
from app.repositories.classificacao_repo import normalizar_descricao
from app.schemas.analise import AnaliseResponse, ItemAnalise, LancamentoResponse
from app.schemas.cadastros import somente_digitos
from app.schemas.invoice import ExtracaoNotaFiscalResponse
from app.services.conta_service import nova_parcela, renumerar_parcelas
from fastapi import HTTPException
from app.services.erros import RegraNegocioError

CATEGORIA_PADRAO = "OUTRAS DESPESAS"


def _para_data(valor: Optional[str]) -> Optional[date]:
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def _categorias_da_nota(nota: ExtracaoNotaFiscalResponse) -> List[str]:
    categorias = [normalizar_descricao(c.categoria) for c in nota.classificacoes_despesa if c.categoria]
    categorias = list(dict.fromkeys(c for c in categorias if c))  # remove repetidas mantendo a ordem
    return categorias or [CATEGORIA_PADRAO]


def _consultar(db: Session, nota: ExtracaoNotaFiscalResponse):
    pessoas = PessoaRepository(db)
    classificacoes = ClassificacaoRepository(db)

    fornecedor = pessoas.buscar_por_documento(nota.fornecedor.cnpj, "FORNECEDOR") or (
        None if somente_digitos(nota.fornecedor.cnpj) else pessoas.buscar_por_nome(nota.fornecedor.razao_social, "FORNECEDOR")
    )
    faturado = pessoas.buscar_por_documento(nota.faturado.cpf, "FATURADO") or (
        None if somente_digitos(nota.faturado.cpf) else pessoas.buscar_por_nome(nota.faturado.nome_completo, "FATURADO")
    )
    despesas = [(cat, classificacoes.buscar_por_descricao(cat, "DESPESA")) for cat in _categorias_da_nota(nota)]
    return fornecedor, faturado, despesas


def _item(registro, descricao: Optional[str], documento: Optional[str] = None) -> ItemAnalise:
    return ItemAnalise(
        descricao=descricao,
        documento=somente_digitos(documento),
        existe=registro is not None,
        id=registro.id if registro else None,
        status=registro.status if registro else None,
    )


def analisar_nota(db: Session, nota: ExtracaoNotaFiscalResponse) -> AnaliseResponse:
    fornecedor, faturado, despesas = _consultar(db, nota)

    duplicado = None
    if fornecedor:
        duplicado = MovimentoRepository(db).buscar_duplicado("APAGAR", nota.numero_nota_fiscal, fornecedor.id)

    return AnaliseResponse(
        fornecedor=_item(fornecedor, nota.fornecedor.razao_social, nota.fornecedor.cnpj),
        faturado=_item(faturado, nota.faturado.nome_completo, nota.faturado.cpf),
        despesas=[_item(c, descricao) for descricao, c in despesas],
        movimento_existente_id=duplicado.id if duplicado else None,
    )


def _montar_parcelas(nota: ExtracaoNotaFiscalResponse, valor_total: Decimal) -> list:
    """Converte as parcelas extraídas; completa valores ausentes dividindo o saldo restante."""
    vencimento_padrao = _para_data(nota.data_vencimento) or _para_data(nota.data_emissao)
    extraidas = nota.parcelas or []
    if not extraidas:
        return [nova_parcela(vencimento_padrao, valor_total)]

    informado = sum(Decimal(str(p.valor)) for p in extraidas if p.valor)
    sem_valor = [p for p in extraidas if not p.valor]
    rateio = ((valor_total - informado) / len(sem_valor)).quantize(Decimal("0.01")) if sem_valor else Decimal(0)

    parcelas = []
    for p in extraidas:
        valor = Decimal(str(p.valor)) if p.valor else rateio
        if valor <= 0:
            raise HTTPException(status_code=400, detail="Não foi possível determinar o valor de todas as parcelas da nota.")
        parcelas.append(nova_parcela(_para_data(p.data_vencimento) or vencimento_padrao, valor))
    return parcelas


def lancar_nota(db: Session, nota: ExtracaoNotaFiscalResponse) -> LancamentoResponse:
    if not (nota.fornecedor.razao_social or "").strip():
        raise HTTPException(status_code=400, detail="A nota não possui fornecedor identificado. Não é possível lançar.")

    fornecedor, faturado, despesas = _consultar(db, nota)
    pessoas = PessoaRepository(db)
    classificacoes_repo = ClassificacaoRepository(db)
    criados: List[str] = []
    reativados: List[str] = []

    # 1. FORNECEDOR
    if fornecedor is None:
        fornecedor = pessoas.adicionar(Pessoa(
            tipo="FORNECEDOR",
            razao_social=nota.fornecedor.razao_social.strip(),
            fantasia=(nota.fornecedor.nome_fantasia or "").strip() or None,
            documento=somente_digitos(nota.fornecedor.cnpj),
            status=STATUS_ATIVO,
        ))
        criados.append(f"Fornecedor (ID {fornecedor.id})")
    elif fornecedor.status != STATUS_ATIVO:
        pessoas.reativar(fornecedor)
        reativados.append(f"Fornecedor (ID {fornecedor.id})")

    # 2. FATURADO (opcional: cupons podem não ter destinatário)
    # 2. FATURADO
    if faturado is None and (nota.faturado.nome_completo or "").strip():
        faturado = pessoas.adicionar(Pessoa(
            tipo="FATURADO",
            razao_social=nota.faturado.nome_completo.strip(),
            documento=somente_digitos(nota.faturado.cpf),
            status=STATUS_ATIVO,
        ))
        criados.append(f"Faturado (ID {faturado.id})")
    elif faturado is not None and faturado.status != STATUS_ATIVO:
        pessoas.reativar(faturado)
        reativados.append(f"Faturado (ID {faturado.id})")

    # 3. DESPESA(S)
    classificacoes: List[Classificacao] = []
    for descricao, classificacao in despesas:
        if classificacao is None:
            classificacao = classificacoes_repo.adicionar(
                Classificacao(tipo="DESPESA", descricao=descricao, status=STATUS_ATIVO)
            )
            criados.append(f"Despesa {descricao} (ID {classificacao.id})")
        elif classificacao.status != STATUS_ATIVO:
            classificacoes_repo.reativar(classificacao)
            reativados.append(f"Despesa {descricao} (ID {classificacao.id})")
        classificacoes.append(classificacao)

    # Evita lançar a mesma nota duas vezes
    duplicado = MovimentoRepository(db).buscar_duplicado("APAGAR", nota.numero_nota_fiscal, fornecedor.id)
    if duplicado:
        raise RegraNegocioError(
            f"Esta nota já foi lançada anteriormente (Movimento ID {duplicado.id}).", status_code=409
        )

    # 4. MOVIMENTO + PARCELA(S)
    valor_total = Decimal(str(nota.valor_total or 0)).quantize(Decimal("0.01"))
    if valor_total <= 0:
        valor_total = sum((Decimal(str(p.valor or 0)) for p in nota.parcelas), Decimal(0)).quantize(Decimal("0.01"))
    if valor_total <= 0:
        raise HTTPException(status_code=400, detail="A nota não possui valor total. Não é possível lançar.")

    movimento = MovimentoContas(
        tipo="APAGAR",
        numero_nota_fiscal=(nota.numero_nota_fiscal or "").strip()[:45] or None,
        data_emissao=_para_data(nota.data_emissao),
        descricao=(nota.descricao_produtos or "")[:300] or None,  # limite da coluna no banco
        valor_total=valor_total,
        pessoa_id=fornecedor.id,
        faturado_id=faturado.id if faturado else None,
        status=STATUS_ATIVO,
        classificacoes=classificacoes,
        parcelas=_montar_parcelas(nota, valor_total),
    )
    db.add(movimento)
    db.flush()
    renumerar_parcelas(movimento.parcelas)
    db.flush()

    return LancamentoResponse(
        mensagem=f"Registro lançado com sucesso! Movimento ID {movimento.id} com {len(movimento.parcelas)} parcela(s).",
        movimento_id=movimento.id,
        parcelas_ids=[p.id for p in movimento.parcelas],
        fornecedor_id=fornecedor.id,
        faturado_id=faturado.id if faturado else None,
        classificacoes_ids=[c.id for c in classificacoes],
        criados=criados,
        reativados=reativados,
    )
