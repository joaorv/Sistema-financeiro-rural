from typing import List, Optional

from pydantic import BaseModel, Field


class ItemAnalise(BaseModel):
    """Resultado da consulta de um item da nota no banco de dados."""
    descricao: Optional[str] = Field(None, description="Nome / razão social / descrição exibida")
    documento: Optional[str] = Field(None, description="CPF ou CNPJ (somente dígitos)")
    existe: bool
    id: Optional[int] = None
    status: Optional[str] = Field(None, description="ATIVO ou INATIVO quando o registro existe")


class AnaliseResponse(BaseModel):
    fornecedor: ItemAnalise
    faturado: ItemAnalise
    despesas: List[ItemAnalise]
    movimento_existente_id: Optional[int] = Field(
        None, description="ID de um movimento já lançado com o mesmo nº de nota e fornecedor"
    )


class LancamentoResponse(BaseModel):
    sucesso: bool = True
    mensagem: str
    movimento_id: int
    parcelas_ids: List[int]
    fornecedor_id: int
    faturado_id: Optional[int] = None
    classificacoes_ids: List[int]
    criados: List[str] = Field(default_factory=list, description="O que precisou ser criado")
    reativados: List[str] = Field(default_factory=list, description="O que estava INATIVO e foi reativado")
