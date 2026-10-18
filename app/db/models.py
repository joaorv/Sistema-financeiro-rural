"""
Modelo de dados do sistema.

Se o banco definitivo usar outros nomes de tabelas/colunas, ajuste apenas
`__tablename__` e o primeiro argumento de `mapped_column("nome_real", ...)`:
o restante do sistema usa somente os atributos Python.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Table, Text
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
    "movimento_classificacao",
    Base.metadata,
    Column("movimento_id", ForeignKey("movimento_contas.id"), primary_key=True),
    Column("classificacao_id", ForeignKey("classificacao.id"), primary_key=True),
)


class Pessoa(Base):
    __tablename__ = "pessoas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    razao_social: Mapped[str] = mapped_column(String(150))
    fantasia: Mapped[Optional[str]] = mapped_column(String(150))
    documento: Mapped[Optional[str]] = mapped_column(String(14), index=True)  # CPF/CNPJ só com dígitos
    status: Mapped[str] = mapped_column(String(10), default=STATUS_ATIVO, index=True)


class Classificacao(Base):
    __tablename__ = "classificacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10), index=True)
    descricao: Mapped[str] = mapped_column(String(150), index=True)  # sempre em MAIÚSCULAS
    status: Mapped[str] = mapped_column(String(10), default=STATUS_ATIVO, index=True)


class MovimentoContas(Base):
    __tablename__ = "movimento_contas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10), index=True)
    numero_nota_fiscal: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    data_emissao: Mapped[Optional[date]] = mapped_column(Date)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Fornecedor (contas a pagar) ou Cliente (contas a receber)
    pessoa_id: Mapped[int] = mapped_column(ForeignKey("pessoas.id"))
    faturado_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pessoas.id"))
    status: Mapped[str] = mapped_column(String(10), default=STATUS_ATIVO, index=True)

    pessoa: Mapped[Pessoa] = relationship(foreign_keys=[pessoa_id])
    faturado: Mapped[Optional[Pessoa]] = relationship(foreign_keys=[faturado_id])
    classificacoes: Mapped[List[Classificacao]] = relationship(secondary=movimento_classificacao)
    parcelas: Mapped[List["ParcelaContas"]] = relationship(
        back_populates="movimento", order_by="ParcelaContas.data_vencimento"
    )


class ParcelaContas(Base):
    __tablename__ = "parcela_contas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movimento_id: Mapped[int] = mapped_column(ForeignKey("movimento_contas.id"), index=True)
    identificacao: Mapped[str] = mapped_column(String(20))  # "ÚNICA" ou "1/3", "2/3"...
    data_vencimento: Mapped[Optional[date]] = mapped_column(Date)
    valor_parcela: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    valor_saldo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(10), default=STATUS_ATIVO, index=True)

    movimento: Mapped[MovimentoContas] = relationship(back_populates="parcelas")
