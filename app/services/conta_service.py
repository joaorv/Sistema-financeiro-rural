from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import STATUS_ATIVO, STATUS_INATIVO, MovimentoContas, ParcelaContas
from app.repositories import ClassificacaoRepository, MovimentoRepository, PessoaRepository
from app.schemas.cadastros import ContaIn
from app.services.erros import RegraNegocioError

# Qual tipo de pessoa e de classificação cada tipo de movimento aceita
PESSOA_POR_MOVIMENTO = {"APAGAR": "FORNECEDOR", "ARECEBER": "CLIENTE"}
CLASSIFICACAO_POR_MOVIMENTO = {"APAGAR": "DESPESA", "ARECEBER": "RECEITA"}


def _dinheiro(valor) -> Decimal:
    return Decimal(str(valor or 0)).quantize(Decimal("0.01"))


def renumerar_parcelas(parcelas: List[ParcelaContas]) -> None:
    """Identificação: 'ÚNICA' quando só há uma parcela ativa; senão '1/N', '2/N'..."""
    ativas = [p for p in parcelas if p.status == STATUS_ATIVO]
    ativas.sort(key=lambda p: (p.data_vencimento or date.max, p.id or 0))
    total = len(ativas)
    for i, parcela in enumerate(ativas, start=1):
        parcela.identificacao = "ÚNICA" if total == 1 else f"{i}/{total}"


def nova_parcela(data_vencimento: Optional[date], valor, valor_pago=0) -> ParcelaContas:
    valor, pago = _dinheiro(valor), _dinheiro(valor_pago)
    if pago > valor:
        raise RegraNegocioError("O valor pago não pode ser maior que o valor da parcela.")
    return ParcelaContas(
        identificacao="ÚNICA",
        data_vencimento=data_vencimento,
        valor_parcela=valor,
        valor_pago=pago,
        valor_saldo=valor - pago,
        status=STATUS_ATIVO,
    )


def salvar_conta(db: Session, dados: ContaIn, movimento: Optional[MovimentoContas] = None) -> MovimentoContas:
    """Cria (movimento=None) ou atualiza um registro de contas a pagar/receber com suas parcelas."""
    pessoas = PessoaRepository(db)
    classificacoes_repo = ClassificacaoRepository(db)
    movimentos = MovimentoRepository(db)

    # --- Pessoa (fornecedor/cliente) e faturado ---
    tipo_pessoa = PESSOA_POR_MOVIMENTO[dados.tipo]
    pessoa = pessoas.obter(dados.pessoa_id)
    if not pessoa or pessoa.tipo != tipo_pessoa or pessoa.status != STATUS_ATIVO:
        raise RegraNegocioError(f"Selecione um {tipo_pessoa.lower()} ATIVO.")

    if dados.faturado_id is not None:
        faturado = pessoas.obter(dados.faturado_id)
        if not faturado or faturado.tipo != "FATURADO" or faturado.status != STATUS_ATIVO:
            raise RegraNegocioError("Selecione um faturado ATIVO.")

    # --- Classificações (uma ou mais) ---
    tipo_classificacao = CLASSIFICACAO_POR_MOVIMENTO[dados.tipo]
    ids = list(dict.fromkeys(dados.classificacao_ids))
    classificacoes = classificacoes_repo.listar_por_ids(ids)
    if len(classificacoes) != len(ids) or any(
        c.tipo != tipo_classificacao or c.status != STATUS_ATIVO for c in classificacoes
    ):
        raise RegraNegocioError(f"Selecione apenas tipos de {tipo_classificacao.lower()} ATIVOS.")

    # --- Duplicidade ---
    duplicado = movimentos.buscar_duplicado(dados.tipo, dados.numero_nota_fiscal, pessoa.id)
    if duplicado and (movimento is None or duplicado.id != movimento.id):
        raise RegraNegocioError(
            f"Já existe um lançamento ativo com a nota {dados.numero_nota_fiscal} para esta pessoa (ID {duplicado.id}).",
            status_code=409,
        )

    if movimento is None:
        movimento = MovimentoContas(status=STATUS_ATIVO)
        db.add(movimento)

    movimento.tipo = dados.tipo
    movimento.numero_nota_fiscal = (dados.numero_nota_fiscal or "").strip() or None
    movimento.data_emissao = dados.data_emissao
    movimento.descricao = dados.descricao
    movimento.valor_total = _dinheiro(dados.valor_total)
    movimento.pessoa_id = pessoa.id
    movimento.faturado_id = dados.faturado_id
    movimento.classificacoes = classificacoes

    # --- Parcelas: atualiza as enviadas com id, cria as novas e INATIVA as removidas ---
    existentes = {p.id: p for p in movimento.parcelas}
    ids_enviados = set()
    for item in dados.parcelas:
        if item.id is not None:
            parcela = existentes.get(item.id)
            if parcela is None:
                raise RegraNegocioError(f"Parcela {item.id} não pertence a este registro.")
            atualizada = nova_parcela(item.data_vencimento, item.valor_parcela, item.valor_pago)
            parcela.data_vencimento = atualizada.data_vencimento
            parcela.valor_parcela = atualizada.valor_parcela
            parcela.valor_pago = atualizada.valor_pago
            parcela.valor_saldo = atualizada.valor_saldo
            parcela.status = STATUS_ATIVO
            ids_enviados.add(item.id)
        else:
            movimento.parcelas.append(nova_parcela(item.data_vencimento, item.valor_parcela, item.valor_pago))

    for id_, parcela in existentes.items():
        if id_ not in ids_enviados:
            parcela.status = STATUS_INATIVO

    db.flush()
    renumerar_parcelas(movimento.parcelas)
    db.flush()
    return movimento
