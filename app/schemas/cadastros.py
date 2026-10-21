import re
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TipoPessoa = Literal["FORNECEDOR", "CLIENTE", "FATURADO"]
TipoClassificacao = Literal["DESPESA", "RECEITA"]
TipoMovimento = Literal["APAGAR", "ARECEBER"]


def somente_digitos(valor: Optional[str]) -> Optional[str]:
    """Remove pontuação de CPF/CNPJ. Retorna None se não sobrar nenhum dígito."""
    if not valor:
        return None
    digitos = re.sub(r"\D", "", valor)
    return digitos or None


# -------------------------------------------------------------
# Pessoas (Fornecedor / Cliente / Faturado)
# -------------------------------------------------------------
class PessoaIn(BaseModel):
    tipo: TipoPessoa
    razao_social: str = Field(..., min_length=1, max_length=150)
    fantasia: Optional[str] = Field(None, max_length=150)
    documento: Optional[str] = Field(None, description="CPF ou CNPJ (com ou sem pontuação)")

    @field_validator("razao_social", "fantasia")
    @classmethod
    def _limpar_texto(cls, v: Optional[str]) -> Optional[str]:
        v = (v or "").strip()
        return v or None

    @field_validator("documento")
    @classmethod
    def _validar_documento(cls, v: Optional[str]) -> Optional[str]:
        v = somente_digitos(v)
        if v and len(v) not in (11, 14):
            raise ValueError("Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos).")
        return v


class PessoaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    razao_social: str
    fantasia: Optional[str] = None
    documento: Optional[str] = None
    status: str


# -------------------------------------------------------------
# Classificação (Tipo de Despesa / Tipo de Receita)
# -------------------------------------------------------------
class ClassificacaoIn(BaseModel):
    tipo: TipoClassificacao
    descricao: str = Field(..., min_length=1, max_length=150)

    @field_validator("descricao")
    @classmethod
    def _normalizar(cls, v: str) -> str:
        v = " ".join(v.split()).upper()
        if not v:
            raise ValueError("Descrição é obrigatória.")
        return v


class ClassificacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    descricao: str
    status: str


# -------------------------------------------------------------
# Contas (Movimento + Parcelas)
# -------------------------------------------------------------
class ParcelaIn(BaseModel):
    id: Optional[int] = Field(None, description="Informe para editar uma parcela existente")
    data_vencimento: Optional[date] = None
    valor_parcela: float = Field(..., gt=0)
    valor_pago: float = Field(0, ge=0)


class ParcelaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identificacao: str
    data_vencimento: Optional[date] = None
    valor_parcela: float
    valor_pago: float
    valor_saldo: float
    status: str


class ContaIn(BaseModel):
    tipo: TipoMovimento
    numero_nota_fiscal: Optional[str] = Field(None, max_length=45)
    data_emissao: Optional[date] = None
    descricao: Optional[str] = Field(None, max_length=300)
    valor_total: float = Field(..., gt=0)
    pessoa_id: int = Field(..., description="Fornecedor (A PAGAR) ou Cliente (A RECEBER)")
    faturado_id: Optional[int] = None
    classificacao_ids: List[int] = Field(..., min_length=1)
    parcelas: List[ParcelaIn] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validar_parcelas(self):
        soma = round(sum(p.valor_parcela for p in self.parcelas), 2)
        if abs(soma - round(self.valor_total, 2)) > 0.01:
            raise ValueError(
                f"A soma das parcelas (R$ {soma:.2f}) difere do valor total (R$ {self.valor_total:.2f})."
            )
        return self


class ContaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    numero_nota_fiscal: Optional[str] = None
    data_emissao: Optional[date] = None
    descricao: Optional[str] = None
    valor_total: float
    status: str
    pessoa: PessoaOut
    faturado: Optional[PessoaOut] = None
    classificacoes: List[ClassificacaoOut] = []
    parcelas: List[ParcelaOut] = []
