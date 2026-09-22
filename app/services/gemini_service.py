import json
import logging
import re
from typing import Optional

from app.config import settings
from app.schemas.invoice import ExtracaoNotaFiscalResponse

logger = logging.getLogger(__name__)

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
   - parcelas: Lista de parcelas contendo {"numero": 1, "data_vencimento": "AAAA-MM-DD", "valor": float}.

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

ESTRUTURA DO JSON DE RESPOSTA OBRIGATÓRIA:
Retorne APENAS um objeto JSON válido correspondente à estrutura abaixo, sem markdown, sem tags ```json ou texto extra:
{
  "fornecedor": {
    "razao_social": "string ou null",
    "nome_fantasia": "string ou null",
    "cnpj": "string ou null"
  },
  "faturado": {
    "nome_completo": "string ou null",
    "cpf": "string ou null"
  },
  "numero_nota_fiscal": "string ou null",
  "data_emissao": "AAAA-MM-DD ou null",
  "descricao_produtos": "string",
  "quantidade_parcelas": 1,
  "data_vencimento": "AAAA-MM-DD ou null",
  "valor_total": 0.0,
  "parcelas": [
    {
      "numero": 1,
      "data_vencimento": "AAAA-MM-DD ou null",
      "valor": 0.0
    }
  ],
  "classificacoes_despesa": [
    {
      "categoria": "NOME DA CATEGORIA",
      "subcategoria_sugerida": "string",
      "justificativa": "string"
    }
  ]
}
"""


def _limpar_resposta_json(texto: str) -> str:
    """Remove eventuais marcações de bloco de código markdown ```json ... ```"""
    texto = texto.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", texto)
    if match:
        return match.group(1).strip()
    return texto


def _chamar_gemini_novo_sdk(pdf_bytes: bytes) -> str:
    """Tenta chamar a API do Gemini utilizando o SDK moderno 'google-genai'."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Modelos disponíveis e ativos no Google GenAI
    modelos_candidatos = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash",
    ]
    erros = []

    for modelo in modelos_candidatos:
        # Tentativa 1: com response_mime_type="application/json" e system_instruction
        try:
            print(f"[Gemini] Tentando processar com {modelo} (JSON mode)...")
            response = client.models.generate_content(
                model=modelo,
                contents=[
                    types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type="application/pdf"
                    ),
                    "Extraia todos os campos da nota fiscal em anexo e retorne o JSON estruturado conforme as instruções."
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            if response and response.text:
                print(f"[Gemini] Sucesso com o modelo {modelo}!")
                return response.text
        except Exception as e1:
            print(f"[Gemini] Falha no modo JSON estruturado com {modelo}: {e1}")
            erros.append(f"{modelo} (JSON): {e1}")

            # Tentativa 2: fallback simples sem response_mime_type
            try:
                print(f"[Gemini] Tentando fallback para {modelo}...")
                response = client.models.generate_content(
                    model=modelo,
                    contents=[
                        types.Part.from_bytes(
                            data=pdf_bytes,
                            mime_type="application/pdf"
                        ),
                        f"{SYSTEM_PROMPT}\n\nAnalise o arquivo PDF acima e retorne o JSON solicitado."
                    ]
                )
                if response and response.text:
                    print(f"[Gemini] Sucesso no fallback com o modelo {modelo}!")
                    return response.text
            except Exception as e2:
                print(f"[Gemini] Falha no fallback com {modelo}: {e2}")
                erros.append(f"{modelo} (fallback): {e2}")

    raise RuntimeError(f"Erro ao processar PDF via google-genai: {' ; '.join(erros)}")


def _chamar_gemini_sdk_legado(pdf_bytes: bytes) -> str:
    """Fallback utilizando o SDK 'google-generativeai' se instalado."""
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    modelos_candidatos = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
    ultimo_erro = None

    for modelo in modelos_candidatos:
        try:
            logger.info(f"Tentando extração com o modelo {modelo} via google-generativeai...")
            model = genai.GenerativeModel(
                model_name=modelo,
                generation_config={"response_mime_type": "application/json", "temperature": 0.1}
            )
            response = model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_bytes},
                SYSTEM_PROMPT
            ])
            if response and response.text:
                return response.text
        except Exception as e:
            logger.warning(f"Falha com modelo legado {modelo}: {e}")
            ultimo_erro = e

    raise RuntimeError(f"Erro ao processar PDF via google-generativeai: {ultimo_erro}")


def extrair_dados_nota_fiscal(pdf_bytes: bytes, filename: str = "nota_fiscal.pdf") -> ExtracaoNotaFiscalResponse:
    """
    Envia o arquivo PDF da nota fiscal para a API do Google Gemini,
    obtém os campos obrigatórios e a classificação inteligente da despesa,
    e retorna o schema validado ExtracaoNotaFiscalResponse.
    """
    if not settings.is_gemini_configured:
        raise ValueError(
            "Chave de API do Gemini não configurada. Defina a variável GEMINI_API_KEY no arquivo .env."
        )

    if not pdf_bytes or len(pdf_bytes) == 0:
        raise ValueError("O arquivo PDF enviado está vazio.")

    raw_response_text: Optional[str] = None
    erros = []

    # 1. Tenta utilizar google-genai (SDK oficial moderno)
    try:
        raw_response_text = _chamar_gemini_novo_sdk(pdf_bytes)
    except ImportError:
        logger.info("google-genai não encontrado. Tentando google-generativeai...")
    except Exception as e:
        erros.append(f"google-genai: {str(e)}")

    # 2. Se não conseguiu e google-generativeai estiver disponível, tenta com ele
    if not raw_response_text:
        try:
            raw_response_text = _chamar_gemini_sdk_legado(pdf_bytes)
        except ImportError:
            pass  # SDK novo já está instalado e foi testado acima
        except Exception as e:
            erros.append(f"google-generativeai: {str(e)}")

    if not raw_response_text:
        msg_erro = " | ".join(erros) if erros else "Falha desconhecida na comunicação com a API do Gemini."
        raise RuntimeError(f"Não foi possível processar a nota fiscal com o Gemini: {msg_erro}")

    # Parse e validação do JSON retornado
    cleaned_json = _limpar_resposta_json(raw_response_text)
    try:
        dados_dict = json.loads(cleaned_json)
    except json.JSONDecodeError as err:
        logger.error(f"Erro ao decodificar JSON do Gemini: {cleaned_json}")
        raise ValueError(f"O Gemini retornou um conteúdo que não é um JSON válido: {err}")

    # Garante consistência de campos
    # Se parcelas estiver vazio mas tiver vencimento e valor_total, monta a 1ª parcela
    if not dados_dict.get("parcelas") and dados_dict.get("data_vencimento"):
        dados_dict["parcelas"] = [
            {
                "numero": 1,
                "data_vencimento": dados_dict.get("data_vencimento"),
                "valor": dados_dict.get("valor_total")
            }
        ]

    # Valida através do Pydantic
    return ExtracaoNotaFiscalResponse(**dados_dict)
