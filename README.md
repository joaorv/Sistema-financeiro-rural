# 🌾 Sistema de Gestão Financeira Rural - Processador de Notas com IA

Aplicação web e API desenvolvida em **FastAPI** que utiliza o **Google Gemini** para processar notas fiscais em formato PDF (DANFE, NFS-e, cupons e recibos), extraindo automaticamente os dados de **Contas a Pagar** e classificando as despesas dentro da taxonomia contábil do **Agronegócio**.

---

## 🔒 Destaques de Arquitetura e Segurança

- 🛡️ **Autenticação Segura com Login e Senha**:
  - Acesso protegido por sessão com cookies `HttpOnly` e `SameSite=Lax`.
  - Comparação de senhas em tempo constante (`secrets.compare_digest`) para prevenir *Timing Attacks*.
  - Proteção contra ataques de força bruta (*Rate Limiting* por IP).
- 🔑 **Chave Gemini Volátil (Sem Persistência no Servidor)**:
  - O usuário informa a chave da API do Gemini diretamente no navegador após o login.
  - A chave é mantida apenas no `sessionStorage` da aba ativa do navegador (apagada automaticamente ao sair ou fechar o navegador).
  - A chave **nunca** é gravada em arquivos `.env`, disco ou banco de dados no servidor.
  - Sanitização de logs e mensagens de erro para evitar qualquer vazamento acidental de caracteres da chave.
- 📁 **Validação Rigorosa de Upload**:
  - Limite de segurança de 10 MB por arquivo.
  - Verificação de *Magic Bytes* (`%PDF-`) para impedir envio de scripts ou executáveis disfarçados.
- 🌐 **Pronto para Hospedagem Gratuita**:
  - Arquivos `Procfile` e `render.yaml` inclusos para deploy em menos de 5 minutos no [Render.com](https://render.com).

---

## 📋 Credenciais Padrão de Demonstração

Para acessar o serviço localmente ou em ambiente de testes:

| Campo | Valor Padrão |
| :--- | :--- |
| **Usuário** | `admin` |
| **Senha** | `rural2026!` |

*(As credenciais podem ser personalizadas via variáveis de ambiente `AUTH_USERNAME` e `AUTH_PASSWORD`).*

---

## ☁️ Como Hospedar Gratuitamente no Render.com (Passo a Passo)

O **Render.com** é uma plataforma em nuvem que oferece um plano gratuito perfeito para rodar aplicações FastAPI diretamente conectadas ao seu repositório GitHub.

```bash
cd "c:\Users\caminho_da_pasta_do_projeto"
```

### Passo 2: Criar um Novo Web Service
1. No painel do Render, clique no botão **New +** e selecione **Web Service**.
2. Conecte seu repositório GitHub: `Gestão-Contas-Rural` (ou o nome do seu repositório).
3. Preencha os campos de configuração:
   - **Name:** `gestao-contas-rural` (ou outro nome de sua preferência)
   - **Language:** `Python 3`
   - **Branch:** `main` (ou a branch que desejar)
   - **Region:** `Ohio (US East)` ou `Frankfurt (EU)`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free` (0.1 CPU, 512 MB RAM)

### Passo 3: Configurar Variáveis de Ambiente (Opcional)
Na seção **Environment Variables**, você pode definir as credenciais que desejar:
- `AUTH_USERNAME`: `admin`
- `AUTH_PASSWORD`: `sua_senha_segura`
- `PYTHON_VERSION`: `3.11.9`

*(Nota: **Não é necessário** adicionar `GEMINI_API_KEY` no Render, pois cada usuário informa sua chave de forma segura no painel web).*

### Passo 4: Fazer o Deploy
1. Clique no botão **Create Web Service** no rodapé da página.
2. O Render fará o build e em cerca de 2 a 3 minutos exibirá a mensagem `Your service is live 🎉`.
3. Você receberá uma URL pública gratuita (ex: `https://gestao-contas-rural.onrender.com`).

> [!NOTE]
> No plano gratuito do Render, se o serviço ficar 15 minutos sem acessos, ele entra em modo de suspensão (*spin down*). Ao ser acessado novamente, ele pode levar de 40 a 50 segundos para "acordar", funcionando normalmente e com rapidez logo em seguida.

---

## 💻 Como Rodar Localmente na sua Máquina

### 1. Pré-requisitos
- Python 3.10+ instalado.
- Chave de API do Gemini gerada gratuitamente no [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Ativar Ambiente Virtual e Instalar Dependências
```bash
# Criar venv (caso ainda não tenha criado)
python -m venv venv

# Ativar venv no Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### 3. Iniciar o Servidor
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acessar no Navegador
- Acesse `http://localhost:8000`
- Insira as credenciais (`admin` / `rural2026!`)
- No modal que será exibido, cole sua **Gemini API Key**
- Carregue uma nota fiscal em PDF e clique em **EXTRAIR DADOS**!

---

## 🗄️ 2ª Etapa: Análise no Banco e Lançamento de Contas

Após a extração, o sistema consulta automaticamente o banco de dados e mostra, para cada item da nota:

```
FORNECEDOR   IGUAÇU MAQUINAS LTDA · CNPJ 11.111.111/0001-00   NÃO EXISTE
FATURADO     BELTRANO DA SILVA · CPF 999.999.999-99            EXISTE – ID: 19
DESPESA      MANUTENÇÃO E OPERAÇÃO                             EXISTE – ID: 22
```

Ao clicar em **LANÇAR CONTA A PAGAR**, em uma única transação, o sistema:

1. Cria o novo FORNECEDOR (se for o caso)
2. Cria o novo FATURADO (se for o caso)
3. Cria a nova DESPESA (se for o caso)
4. Cria o registro do MOVIMENTO (`APAGAR`) e suas PARCELAS (`ÚNICA` ou `1/N`, `2/N`...)
5. Informa ao usuário que o registro foi lançado com sucesso

Registros que existem, mas estão INATIVOS, são reativados. Uma nota já lançada (mesmo nº e fornecedor) não é lançada novamente.

### Cadastros (CRUD)

| Tela | Funcionalidades |
| :--- | :--- |
| **Pessoas** | Manter Fornecedor, Cliente e Faturado |
| **Classificações** | Manter Tipo de Despesa e Tipo de Receita |
| **Contas** | Registrar Contas a Pagar e a Receber (uma ou mais classificações e parcelas) |

Todas seguem a recomendação de layout: tabela inicialmente vazia; carga pela **Busca** ou **Todos** (somente ATIVOS); ordenação por coluna; busca por mais de um elemento; ações **Editar / Excluir** (exclusão lógica: STATUS = INATIVO) e **Reativar**. O STATUS nunca aparece nos formulários (CREATE grava ATIVO).

### Rotas da API

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `POST` | `/api/analisar` | Consulta Fornecedor / Faturado / Despesa da nota extraída |
| `POST` | `/api/lancar` | Cria o que faltar + movimento + parcelas |
| `GET` | `/api/{pessoas,classificacoes,contas}?busca=&tipo=&status=ATIVO\|INATIVO\|TODOS` | Lista / busca |
| `GET` | `/api/{entidade}/{id}` | Detalhe |
| `POST` | `/api/{entidade}` | Inclui (STATUS = ATIVO) |
| `PUT` | `/api/{entidade}/{id}` | Altera |
| `DELETE` | `/api/{entidade}/{id}` | Exclusão lógica (STATUS = INATIVO) |
| `POST` | `/api/{entidade}/{id}/reativar` | STATUS = ATIVO |

A documentação interativa fica em `/docs`.

### 🔌 Banco de dados PostgreSQL no Neon

Sem `DATABASE_URL`, o sistema usa um **SQLite local** (`rural.db`) para desenvolvimento, criado automaticamente. O banco definitivo é um **PostgreSQL no [Neon](https://neon.tech)**, criado pelos scripts da pasta `db/` (seguindo o diagrama do projeto):

1. No painel do Neon, abra o **SQL Editor** e execute `db/schema.sql` (cria as tabelas) e depois `db/seed.sql` (classificações padrão de DESPESA/RECEITA). Pela linha de comando: `psql "<connection string>" -f db/schema.sql`.
2. Copie a *connection string* do Neon (`postgresql://usuario:senha@ep-xxxx.neon.tech/neondb?sslmode=require`) para a variável `DATABASE_URL` no `.env` (local) e nas *Environment Variables* do Render.
3. O driver `psycopg[binary]` (psycopg 3) já está no `requirements.txt`; a URL é convertida automaticamente para `postgresql+psycopg://`.
4. No PostgreSQL a aplicação **não** cria nem altera tabelas: qualquer mudança de estrutura deve ser feita em `db/schema.sql` e refletida em `app/db/models.py` (`__tablename__` e o primeiro argumento de `mapped_column("nome_real", ...)`).

Tabelas: `pessoas`, `classificacao`, `movimentocontas`, `parcelascontas` e `movimentocontas_has_classificacao` (N:N entre movimento e classificação).

> [!WARNING]
> No plano gratuito do Render o disco é apagado a cada deploy/reinício, então o SQLite **não** é persistente lá. Para a entrega, configure o `DATABASE_URL` do banco definitivo.

---

## 🌾 Categorias de Despesas do Agronegócio (LLM)

A inteligência artificial analisa os produtos contidos na nota fiscal e realiza a classificação automática em uma das seguintes categorias contábeis:

1. **INSUMOS AGRÍCOLAS**: Sementes, fertilizantes, defensivos, adubos, mudas.
2. **MANUTENÇÃO E OPERAÇÃO**: Combustíveis (Diesel), lubrificantes, peças de máquinas, filtros, ferramentas.
3. **RECURSOS HUMANOS**: Mão de obra temporária, diárias de campo, salários e encargos.
4. **SERVIÇOS OPERACIONAIS**: Fretes, transporte, colheita terceirizada, secagem, armazenagem, pulverização.
5. **INFRAESTRUTURA E UTILIDADES**: Energia elétrica, irrigação, materiais de construção e reformas.
6. **ADMINISTRATIVAS**: Honorários agronômicos/contábeis, taxas e tarifas bancárias.
7. **SEGUROS E PROTEÇÃO**: Seguro agrícola, seguro de máquinas e implementos.
8. **IMPOSTOS E TAXAS**: ITR, CCIR, taxas estaduais/municipais.
9. **INVESTIMENTOS**: Aquisição de tratores, maquinários, veículos e imóveis rurais.
10. **OUTRAS DESPESAS**: Despesas atípicas fora das categorias principais.

---

## 📂 Estrutura do Projeto

```plaintext
Sistema-financeiro-rural/
├── app/
│   ├── db/
│   │   ├── database.py        # Conexão (DATABASE_URL), sessão e criação das tabelas
│   │   └── models.py          # Tabelas: Pessoas, Classificacao, MovimentoContas, ParcelaContas
│   ├── repositories/          # Único ponto de acesso ao banco (consultas e gravações)
│   ├── routers/
│   │   ├── cadastros.py       # API REST dos CRUDs (Pessoas, Classificações, Contas)
│   │   ├── lancamento.py      # /api/analisar e /api/lancar (2ª etapa)
│   │   └── paginas.py         # Páginas HTML dos cadastros
│   ├── schemas/
│   │   ├── invoice.py         # Schemas e validação Pydantic dos dados da NF
│   │   ├── cadastros.py       # Schemas dos cadastros
│   │   └── analise.py         # Schemas da análise e do lançamento
│   ├── services/
│   │   ├── gemini_service.py  # Extração com Gemini e chave dinâmica em memória RAM
│   │   ├── conta_service.py   # Regras de contas e parcelas
│   │   └── lancamento_service.py # Análise da nota e lançamento (tudo ou nada)
│   ├── static/
│   │   ├── css/custom.css     # Estilos complementares
│   │   └── js/                # app.js (extração/análise), comum.js, crud_lista.js, crud_form.js, contas_form.js
│   ├── templates/
│   │   ├── base.html          # Layout com menu
│   │   ├── login.html         # Página de autenticação segura
│   │   ├── index.html         # Extração, análise no banco e lançamento
│   │   ├── cadastro_lista.html / cadastro_form.html  # Layouts genéricos do CRUD
│   │   └── pessoas/ classificacoes/ contas/          # Telas de cada cadastro
│   ├── auth.py                # Assinatura de sessão HMAC-SHA256 e Rate Limiting
│   ├── config.py              # Configurações do servidor, segurança e banco
│   ├── dependencies.py        # Verificação de sessão para rotas e páginas
│   └── main.py                # Aplicação FastAPI, rotas protegidas e middleware
├── Procfile                   # Comando de inicialização para Render / PaaS
├── render.yaml                # Arquivo Blueprint para deploy em nuvem
├── requirements.txt           # Dependências do projeto
├── .env.example               # Exemplo de variáveis de ambiente
└── README.md                  # Documentação completa
```
