from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CategoriaDespesaEnum(str, Enum):
    INSUMOS_AGRICOLAS = "INSUMOS AGRÍCOLAS"
    MANUTENCAO_OPERACAO = "MANUTENÇÃO E OPERAÇÃO"
    RECURSOS_HUMANOS = "RECURSOS HUMANOS"
    SERVICOS_OPERACIONAIS = "SERVIÇOS OPERACIONAIS"
    INFRAESTRUTURA_UTILIDADES = "INFRAESTRUTURA E UTILIDADES"
    ADMINISTRATIVAS = "ADMINISTRATIVAS"
    SEGUROS_PROTECAO = "SEGUROS E PROTEÇÃO"
    IMPOSTOS_TAXAS = "IMPOSTOS E TAXAS"
    INVESTIMENTOS = "INVESTIMENTOS"
    OUTRAS = "OUTRAS DESPESAS"


class FornecedorSchema(BaseModel):
    razao_social: Optional[str] = Field(None, description="Razão Social do Fornecedor emitente")
    nome_fantasia: Optional[str] = Field(None, description="Nome Fantasia do Fornecedor")
    cnpj: Optional[str] = Field(None, description="CNPJ do Fornecedor formatado ou numérico")


class FaturadoSchema(BaseModel):
    nome_completo: Optional[str] = Field(None, description="Nome Completo do Destinatário/Faturado")
    cpf: Optional[str] = Field(None, description="CPF do Destinatário/Faturado formatado ou numérico")


class ParcelaSchema(BaseModel):
    numero: int = Field(default=1, description="Número ordinal da parcela")
    data_vencimento: Optional[str] = Field(None, description="Data de vencimento da parcela no formato AAAA-MM-DD")
    valor: Optional[float] = Field(None, description="Valor da parcela em Reais (R$)")


class ClassificacaoDespesaSchema(BaseModel):
    categoria: str = Field(..., description="Categoria principal da despesa (conforme taxonomia)")
    subcategoria_sugerida: Optional[str] = Field(None, description="Ex: Combustíveis e Lubrificantes, Sementes, etc.")
    justificativa: Optional[str] = Field(None, description="Breve justificativa da classificação com base nos produtos")


class ExtracaoNotaFiscalResponse(BaseModel):
    fornecedor: FornecedorSchema = Field(default_factory=FornecedorSchema)
    faturado: FaturadoSchema = Field(default_factory=FaturadoSchema)
    numero_nota_fiscal: Optional[str] = Field(None, description="Número da Nota Fiscal (NF-e, NFS-e, etc.)")
    data_emissao: Optional[str] = Field(None, description="Data de emissão no formato AAAA-MM-DD")
    descricao_produtos: Optional[str] = Field(None, description="Descrição resumida dos produtos e serviços constantes na nota")
    quantidade_parcelas: int = Field(default=1, description="Quantidade de parcelas da fatura/duplicata")
    data_vencimento: Optional[str] = Field(None, description="Data de vencimento da fatura/primeira parcela")
    valor_total: Optional[float] = Field(None, description="Valor total da nota fiscal em Reais (R$)")
    
    # Estrutura preparada para 1 ou mais parcelas
    parcelas: List[ParcelaSchema] = Field(default_factory=list, description="Lista de parcelas identificadas")
    
    # Estrutura preparada para 1 ou mais classificações de despesa
    classificacoes_despesa: List[ClassificacaoDespesaSchema] = Field(
        default_factory=list,
        description="Lista de classificações de despesa atribuídas pelo Gemini"
    )
