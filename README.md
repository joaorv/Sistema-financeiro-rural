# 🌾 Sistema de Gestão Financeira - Processador de Notas Fiscais com IA

Aplicação web e API desenvolvida em **FastAPI** que utiliza o **Google Gemini** para processar notas fiscais em formato PDF (DANFE, NFS-e, cupons e recibos), extraindo automaticamente os dados de **Contas a Pagar** e classificando as despesas dentro da taxonomia contábil do **Agronegócio**.

---

## 📋 Funcionalidades

- 📄 **Upload e Leitura de PDFs**: Processamento direto de arquivos de notas fiscais em PDF de até 25 MB.
- 🤖 **Extração Inteligente com Google Gemini**:
  - Dados do **Fornecedor** (Razão Social, Nome Fantasia, CNPJ).
  - Dados do **Faturado/Destinatário** (Nome Completo, CPF/CNPJ).
  - **Dados da Nota** (Número da NF, Data de Emissão, Descrição dos Produtos/Serviços, Valor Total).
  - **Cobrança e Vencimento** (Data de Vencimento, Quantidade de Parcelas e lista de Parcelas).
- 🏷️ **Classificação Automática de Despesas**: Categorização inteligente no contexto do agronegócio (ex.: *Insumos Agrícolas*, *Manutenção e Operação*, *Recursos Humanos*, *Serviços Operacionais*, etc.) com justificativa e subcategoria sugerida.
- 🖥️ **Interface Web Interativa**: Painel moderno em HTML/CSS/JS para envio rápido e visualização dos dados extraídos em tempo real.
- 📚 **Documentação Interativa (Swagger/OpenAPI)**: Testes rápidos de endpoints diretamente pelo navegador.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **FastAPI**: Framework web moderno e de alta performance.
- **Uvicorn**: Servidor ASGI leve e rápido.
- **Google GenAI SDK (`google-genai`)**: Integração de IA multimodal com modelos Gemini.
- **Pydantic v2**: Validação e serialização de dados estruturados.
- **Jinja2**: Renderização de templates HTML.

---

## 🚀 Passo a Passo de Execução (Do Zero)

Siga as etapas abaixo para configurar e rodar o projeto em sua máquina local.

### 1. Pré-requisitos

Certifique-se de ter instalado em seu computador:
- [Python 3.10](https://www.python.org/downloads/) ou superior (marque a opção *"Add Python to PATH"* durante a instalação no Windows).
- Uma chave de API do Google Gemini. Se você ainda não possui, crie gratuitamente no [Google AI Studio](https://aistudio.google.com/app/apikey).

---

### 2. Abrir o Terminal no Diretório do Projeto

Navegue até a pasta do projeto no seu terminal (PowerShell, CMD, Git Bash ou terminal do VS Code):

```bash
cd "c:\Users\caminho_da_pasta_do_projeto"
```

---

### 3. Criar o Ambiente Virtual (venv)

É uma boa prática criar um ambiente virtual isolado para as bibliotecas do projeto:

- **Windows (PowerShell ou Prompt de Comando):**
  ```powershell
  python -m venv venv
  ```

- **Linux / macOS:**
  ```bash
  python3 -m venv venv
  ```

---

### 4. Ativar o Ambiente Virtual

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Se você receber um aviso sobre execução de scripts bloqueada no PowerShell, execute primeiro: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e tente novamente).*

- **Windows (CMD / Prompt de Comando):**
  ```cmd
  venv\Scripts\activate.bat
  ```

- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

*(Quando ativado com sucesso, o prefixo `(venv)` aparecerá no início da linha de comando).*

---

### 5. Instalar as Dependências

Com o ambiente virtual ativado, instale todas as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

---

### 6. Configurar as Variáveis de Ambiente (`.env`)

O projeto necessita da sua chave do Google Gemini para processar as notas fiscais.

1. Crie uma cópia do arquivo `.env.example` nomeando-a como `.env`:
   - **Windows (PowerShell):**
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS / Git Bash:**
     ```bash
     cp .env.example .env
     ```

2. Abra o arquivo `.env` em seu editor de texto e insira sua chave da API do Gemini:
   ```env
   HOST=0.0.0.0
   PORT=8000
   GEMINI_API_KEY=AIzaSy...sua_chave_real_aqui
   ```

---

### 7. Iniciar a Aplicação

Você pode rodar o servidor utilizando qualquer um dos comandos abaixo:

- **Opção 1 (Recomendada com live-reload):**
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

- **Opção 2 (Executando o módulo Python):**
  ```bash
  python -m app.main
  ```

O terminal exibirá uma mensagem informando que a aplicação está pronta:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

### 8. Acessar no Navegador

Abra o seu navegador web favorito e acesse:

| Recurso | URL | Descrição |
| :--- | :--- | :--- |
| **Painel Web (Frontend)** | [http://localhost:8000](http://localhost:8000) | Interface gráfica para upload e extração de PDFs |
| **Swagger UI (Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentação interativa da API |
| **Redoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Documentação técnica alternativa da API |
| **Verificação de Status** | [http://localhost:8000/api/status](http://localhost:8000/api/status) | Endpoint que confirma status e validade da chave |

---

## 📂 Estrutura do Projeto

```plaintext
Projeto Paraib/
├── app/
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── invoice.py         # Schemas e validação Pydantic dos dados da NF
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini_service.py  # Lógica de integração e extração via Google Gemini
│   ├── static/                # Arquivos estáticos (CSS, JavaScript, ícones)
│   ├── templates/
│   │   └── index.html         # Página principal da interface web (Jinja2)
│   ├── config.py              # Leitura de variáveis de ambiente e configurações
│   └── main.py                # Ponto de entrada FastAPI e definição de rotas
├── .env.example               # Modelo de variáveis de ambiente
├── .env                       # Variáveis de ambiente locais (não versionado)
├── .gitignore                 # Arquivos e pastas ignorados pelo Git
├── requirements.txt           # Dependências do projeto Python
└── README.md                  # Este guia de execução
```

---

## 📡 Endpoints da API

### `GET /api/status`
Verifica se o servidor está online e se a `GEMINI_API_KEY` foi configurada.

**Exemplo de Resposta:**
```json
{
  "status": "online",
  "gemini_configurado": true,
  "mensagem": "Servidor pronto para processar notas fiscais."
}
```

---

### `POST /api/processar-nota`
Recebe o arquivo PDF da nota fiscal através de um campo multipart chamado `arquivo` e retorna o JSON estruturado com os dados extraídos e a classificação contábil.

- **Content-Type**: `multipart/form-data`
- **Parâmetro**: `arquivo` (arquivo PDF, máx. 25 MB)

**Exemplo de uso via `cURL`:**
```bash
curl -X POST "http://localhost:8000/api/processar-nota" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "arquivo=@/caminho/para/sua_nota_fiscal.pdf"
```

---

## 🌾 Categorias de Despesas do Agronegócio

A inteligência artificial analisa o conteúdo da nota e classifica automaticamente a despesa em uma das categorias:

1. **INSUMOS AGRÍCOLAS**: Sementes, fertilizantes, defensivos, adubos, mudas.
2. **MANUTENÇÃO E OPERAÇÃO**: Combustíveis, peças de máquinas, óleos, filtros, ferramentas.
3. **RECURSOS HUMANOS**: Mão de obra temporária, diárias de campo, serviços rurais.
4. **SERVIÇOS OPERACIONAIS**: Fretes, transporte, secagem, armazenagem, pulverização.
5. **INFRAESTRUTURA E UTILIDADES**: Energia elétrica, irrigação, reformas, materiais hidráulicos.
6. **ADMINISTRATIVAS**: Honorários agronômicos/contábeis, taxas bancárias.
7. **SEGUROS E PROTEÇÃO**: Seguro rural, seguro de máquinas e implementos.
8. **IMPOSTOS E TAXAS**: ITR, CCIR, taxas estaduais/municipais.
9. **INVESTIMENTOS**: Aquisição de tratores, implementos, veículos, terras.
10. **OUTRAS DESPESAS**: Despesas atípicas fora das categorias anteriores.

---

## ❓ Resolução de Problemas Comuns (Troubleshooting)

### 1. "O script Activate.ps1 não pode ser carregado porque a execução de scripts foi desabilitada..."
No PowerShell do Windows, essa é uma política de segurança padrão. Para liberar no processo atual, execute:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Em seguida, execute `.\venv\Scripts\Activate.ps1` novamente.

### 2. "Atenção: GEMINI_API_KEY não configurada no arquivo .env"
- Verifique se você criou o arquivo com o nome exato `.env` (sem extensão `.txt` no final).
- Abra o arquivo `.env` e confirme se a linha possui a sua chave real: `GEMINI_API_KEY=AIzaSy...`
- Caso tenha alterado o arquivo, não é necessário reiniciar o servidor; a aplicação recarrega a chave automaticamente.

### 3. Erro "Port 8000 is already in use" (Porta em uso)
Se outra aplicação estiver usando a porta `8000`, basta iniciar o servidor especificando outra porta:
```bash
uvicorn app.main:app --reload --port 8080
```
E acesse `http://localhost:8080`.
