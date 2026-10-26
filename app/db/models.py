"""
Modelo de dados do sistema.

Os nomes de tabelas/colunas seguem o diagrama do projeto (em minúsculas, sem aspas),
e são os mesmos de `db/schema.sql`, usado para criar o banco PostgreSQL no Neon.
Se o banco definitivo usar outros nomes de tabelas/colunas, ajuste apenas
`__tablename__` e o primeiro argumento de `mapped_column("nome_real", ...)`:
o restante do sistema usa somente os atributos Python.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

# Valores de domínio
STATUS_ATIVO = "ATIVO"
STATUS_INATIVO = "INATIVO"

TIPOS_PESSOA = ("FORNECEDOR", "CLIENTE", "FATURADO")
TIPOS_CLASSIFICACAO = ("DESPESA", "RECEITA")
TIPOS_MOVIMENTO = ("APAGAR", "ARECEBER")


# Associação N:N - um movimento pode ter uma ou mais classificações
movimento_classificacao = Table(
    "movimentocontas_has_classificacao",
    Base.metadata,
    Column(
        "movimentocontas_idmovimentocontas",
        ForeignKey("movimentocontas.idmovimentocontas"),
        primary_key=True,
    ),
    Column("classificacao_idclassificacao", ForeignKey("classificacao.idclassificacao"), primary_key=True),
)


class Pessoa(Base):
    __tablename__ = "pessoas"

    id: Mapped[int] = mapped_column("idpessoas", Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column("tipo", String(45))
    razao_social: Mapped[str] = mapped_column("razaosocial", String(150))
    fantasia: Mapped[Optional[str]] = mapped_column("fantasia", String(150))
    documento: Mapped[Optional[str]] = mapped_column("documento", String(45))  # CPF/CNPJ só com dígitos
    status: Mapped[str] = mapped_column("status", String(45), default=STATUS_ATIVO)


class Classificacao(Base):
    __tablename__ = "classificacao"

    id: Mapped[int] = mapped_column("idclassificacao", Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column("tipo", String(45))
    descricao: Mapped[str] = mapped_column("descricao", String(150))  # sempre em MAIÚSCULAS
    status: Mapped[str] = mapped_column("status", String(45), default=STATUS_ATIVO)


class MovimentoContas(Base):
    __tablename__ = "movimentocontas"

    id: Mapped[int] = mapped_column("idmovimentocontas", Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column("tipo", String(45))
    numero_nota_fiscal: Mapped[Optional[str]] = mapped_column("numeronotafiscal", String(45))
    data_emissao: Mapped[Optional[date]] = mapped_column("dataemissao", Date)
    descricao: Mapped[Optional[str]] = mapped_column("descricao", String(300))
    status: Mapped[str] = mapped_column("status", String(45), default=STATUS_ATIVO)
    valor_total: Mapped[Decimal] = mapped_column("valortotal", Numeric(12, 2))
    # Fornecedor (contas a pagar) ou Cliente (contas a receber)
    pessoa_id: Mapped[int] = mapped_column("pessoas_idfornecedorcliente", ForeignKey("pessoas.idpessoas"))
    faturado_id: Mapped[Optional[int]] = mapped_column("pessoas_idfaturado", ForeignKey("pessoas.idpessoas"))

    pessoa: Mapped[Pessoa] = relationship(foreign_keys=[pessoa_id])
    faturado: Mapped[Optional[Pessoa]] = relationship(foreign_keys=[faturado_id])
    classificacoes: Mapped[List[Classificacao]] = relationship(secondary=movimento_classificacao)
    parcelas: Mapped[List["ParcelaContas"]] = relationship(
        back_populates="movimento", order_by="ParcelaContas.data_vencimento"
    )


class ParcelaContas(Base):
    __tablename__ = "parcelascontas"

    id: Mapped[int] = mapped_column("idparcelascontas", Integer, primary_key=True)
    identificacao: Mapped[str] = mapped_column("identificacao", String(45))  # "ÚNICA" ou "1/3", "2/3"...
    data_vencimento: Mapped[Optional[date]] = mapped_column("datavencimento", Date)
    valor_parcela: Mapped[Decimal] = mapped_column("valorparcela", Numeric(12, 2))
    valor_pago: Mapped[Decimal] = mapped_column("valorpago", Numeric(12, 2), default=0)
    valor_saldo: Mapped[Decimal] = mapped_column("valorsaldo", Numeric(12, 2))
    status: Mapped[str] = mapped_column("statusparcela", String(45), default=STATUS_ATIVO)
    movimento_id: Mapped[int] = mapped_column(
        "movimentocontas_idmovimentocontas", ForeignKey("movimentocontas.idmovimentocontas")
    )

    movimento: Mapped[MovimentoContas] = relationship(back_populates="parcelas")
