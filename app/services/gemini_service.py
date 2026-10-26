import asyncio
import json
import logging
import re
import time
from typing import AsyncGenerator, Dict, List, Optional, Any

from google import genai
from google.genai import errors, types
from pydantic import Field

from app.config import settings
from app.schemas.invoice import (
    CategoriaDespesaEnum,
    ClassificacaoDespesaSchema,
    ExtracaoNotaFiscalResponse,
)

logger = logging.getLogger(__name__)

# Ordem de tentativa: em 503/429/timeout passa para o próximo modelo (flash antes de flash-lite)
MODELOS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]
TIMEOUT_MS = 60_000  # limite por tentativa
PAUSA_503_S = 1.5  # pausa curta antes do próximo modelo quando há pico de demanda (503)


# Schema enviado ao Gemini: igual ao da API, mas com a categoria restrita ao enum
class _ClassificacaoGemini(ClassificacaoDespesaSchema):
    categoria: CategoriaDespesaEnum


class _ExtracaoGemini(ExtracaoNotaFiscalResponse):
    classificacoes_despesa: List[_ClassificacaoGemini] = Field(default_factory=list)


SYSTEM_PROMPT = """
Você é um especialista contábil e tributário com profundo conhecimento no Agronegócio brasileiro.
Sua tarefa é analisar o documento de NOTA FISCAL (DANFE, NFS-e, Cupom Fiscal ou Recibo) em anexo no formato PDF e extrair os dados estruturados de CONTAS A PAGAR.

ATENÇÃO ÀS REGRAS DE EXTRAÇÃO:
1. FORNECEDOR (Emitente da nota):
   - razao_social: Razão Social completa do emitente.
   - nome_fantasia: Nome Fantasia se constar na nota (ou nulo se não houver).
   - cnpj: CNPJ do emitente (formatado com pontos e traços, ex: 00.000.000/0001-00).

2. FATURADO (Destinatário/Cliente da nota fiscal):
   - nome_completo: Nome completo ou Razão Social do destinatário.
   - cpf: CPF do destinatário (se pessoa física) ou CNPJ (se for pessoa jurídica destinatária).

3. DADOS DA NOTA:
   - numero_nota_fiscal: Número oficial da nota fiscal (campo "Nº" ou "Número da NF").
   - data_emissao: Data de emissão no formato AAAA-MM-DD.
   - descricao_produtos: Resumo detalhado de todos os produtos ou serviços contidos na nota.
   - valor_total: Valor total da nota fiscal (numérico float, ex: 1540.50).
   - quantidade_parcelas: Número de parcelas informadas no campo de cobrança/fatura (se não especificado, assuma 1).
   - data_vencimento: Data de vencimento principal ou da primeira parcela no formato AAAA-MM-DD (se não constar vencimento, use a data de emissão).
   - parcelas: Lista de parcelas contendo numero, data_vencimento (AAAA-MM-DD) e valor (float).

4. CLASSIFICAÇÃO DA DESPESA (Regra Crítica):
A despesa NÃO é um campo explícito da nota fiscal. Você DEVE interpretar a descrição dos produtos/serviços e classificá-la obrigatoriamente em UMA das seguintes Categorias Principais do Agronegócio:
- "INSUMOS AGRÍCOLAS": Sementes, Fertilizantes, Defensivos Agrícolas, Corretivos, Adubos, Mudas.
- "MANUTENÇÃO E OPERAÇÃO": Combustíveis (Diesel, Gasolina), Lubrificantes, Óleos, Peças, Parafusos, Componentes Mecânicos, Manutenção de Máquinas e Equipamentos, Pneus, Filtros, Correias, Ferramentas e Utensílios.
- "RECURSOS HUMANOS": Mão de Obra Temporária, Salários, Diárias de campo, Encargos.
- "SERVIÇOS OPERACIONAIS": Frete e Transporte, Colheita Terceirizada, Secagem e Armazenagem, Pulverização e Aplicação aérea/terrestre.
- "INFRAESTRUTURA E UTILIDADES": Energia Elétrica, Arrendamento de Terras, Construções, Reformas, Materiais Hidráulicos, Elétricos e de Construção.
- "ADMINISTRATIVAS": Honorários (Contábeis, Advocatícios, Agronômicos), Despesas Bancárias, Tarifas e Financeiras.
- "SEGUROS E PROTEÇÃO": Seguro Agrícola, Seguro de Ativos (Máquinas/Veículos), Seguro Prestamista.
- "IMPOSTOS E TAXAS": ITR, IPTU, IPVA, INCRA-CCIR, Taxas estaduais/municipais.
- "INVESTIMENTOS": Aquisição de Máquinas e Implementos, Aquisição de Veículos, Aquisição de Imóveis, Infraestrutura Rural.
- "OUTRAS DESPESAS": Apenas se não se enquadrar em nenhuma das anteriores.

Para cada classificação atribuída, forneça:
- "categoria": Nome exato de uma das categorias acima em maiúsculas.
- "subcategoria_sugerida": Ex: "Combustíveis e Lubrificantes", "Defensivos Agrícolas", etc.
- "justificativa": Explicação concisa relacionando o produto faturado com a categoria.

Campos ausentes no documento devem ser retornados como null.
"""

# Configuração fixa da chamada (o formato do JSON é garantido pelo response_schema)
_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    response_mime_type="application/json",
    response_schema=_ExtracaoGemini,
    temperature=0.1,
    # Sem tools: desativa o AFC (remove o aviso do SDK no terminal)
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def _redigir_chave(texto: str, chave: Optional[str] = None) -> str:
    """Higieniza o texto de log ou erro para evitar que caracteres da chave da API vazem."""
    if not texto:
        return texto
    if chave and len(chave) > 6:
        texto = texto.replace(chave, "[CHAVE_PROTEGIDA]")
    # Remove qualquer padrão provável de chave Gemini (AIzaSy...)
    texto = re.sub(r"AIza[0-9A-Za-z\-_]{20,}", "[CHAVE_PROTEGIDA]", texto)
    return texto


async def extrair_dados_nota_fiscal_stream(
    pdf_bytes: bytes,
    api_key: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executa a extração da nota fiscal enviando eventos em tempo real para cada tentativa,
    aviso de 503/alta demanda, e resultado final estruturado.
    """
    chave_efetiva = (api_key or "").strip() or settings.GEMINI_API_KEY
    if not chave_efetiva:
        yield {
            "tipo": "erro",
            "mensagem": "Chave de API do Gemini não informada. Insira sua chave para continuar."
        }
        return

    if not pdf_bytes or len(pdf_bytes) == 0:
        yield {
            "tipo": "erro",
            "mensagem": "O arquivo PDF enviado está vazio."
        }
        return

    client = genai.Client(api_key=chave_efetiva, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
    conteudo = [
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        "Extraia todos os campos da nota fiscal em anexo.",
    ]
    erros = []

    yield {
        "tipo": "info",
        "mensagem": "Arquivo PDF preparado. Iniciando conexão com a IA..."
    }

    for modelo in MODELOS:
        config = _CONFIG
        if modelo.startswith("gemini-3"):
            config = _CONFIG.model_copy(update={
                "thinking_config": types.ThinkingConfig(thinking_level=types.ThinkingLevel.MEDIUM)
            })

        yield {
            "tipo": "tentativa",
            "modelo": modelo,
            "mensagem": f"Consultando modelo {modelo}..."
        }

        try:
            # Executa a chamada em thread separada para não travar o loop assíncrono
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=modelo,
                contents=conteudo,
                config=config
            )

            if response and response.text:
                try:
                    dados_dict = json.loads(response.text)
                    if not dados_dict.get("parcelas") and dados_dict.get("data_vencimento"):
                        dados_dict["parcelas"] = [
                            {
                                "numero": 1,
                                "data_vencimento": dados_dict.get("data_vencimento"),
                                "valor": dados_dict.get("valor_total")
                            }
                        ]
                    resultado = ExtracaoNotaFiscalResponse(**dados_dict)
                    yield {
                        "tipo": "sucesso",
                        "modelo": modelo,
                        "mensagem": f"Extração concluída com sucesso via {modelo}!",
                        "dados": resultado.model_dump()
                    }
                    return
                except Exception as e_parse:
                    logger.error(f"Erro ao processar JSON retornado por {modelo}: {e_parse}")
                    erros.append(f"{modelo}: JSON inválido retornado")
            else:
                erros.append(f"{modelo}: resposta vazia")

        except errors.ClientError as e:
            msg_e = _redigir_chave(str(e), chave_efetiva)
            # Chave inválida / sem permissão: aborta imediatamente
            if e.code in (401, 403) or (e.code == 400 and "API key" in msg_e):
                yield {
                    "tipo": "erro",
                    "modelo": modelo,
                    "mensagem": "Chave de API do Gemini inválida ou sem permissão. Verifique sua chave.",
                    "detalhes": msg_e
                }
                return
            erros.append(f"{modelo}: {msg_e}")
            yield {
                "tipo": "aviso",
                "modelo": modelo,
                "mensagem": f"{modelo}: Não disponível ({e.code}). Alternando modelo...",
                "detalhes": msg_e
            }

        except Exception as e:
            msg_e = _redigir_chave(str(e), chave_efetiva)
            erros.append(f"{modelo}: {msg_e}")
            if "503" in msg_e or "UNAVAILABLE" in msg_e:
                yield {
                    "tipo": "aviso",
                    "modelo": modelo,
                    "mensagem": f"{modelo}: Servidores com alta demanda (503). Aguardando {PAUSA_503_S}s e tentando próximo modelo...",
                    "detalhes": msg_e
                }
                await asyncio.sleep(PAUSA_503_S)
            else:
                yield {
                    "tipo": "aviso",
                    "modelo": modelo,
                    "mensagem": f"{modelo}: Falha temporária ({msg_e[:60]}...). Alternando...",
                    "detalhes": msg_e
                }

    yield {
        "tipo": "erro",
        "mensagem": "Não foi possível processar a nota fiscal com nenhum dos modelos disponíveis no momento.",
        "detalhes": " ; ".join(erros)
    }

