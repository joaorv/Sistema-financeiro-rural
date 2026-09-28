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
│   ├── schemas/
│   │   └── invoice.py         # Schemas e validação Pydantic dos dados da NF
│   ├── services/
│   │   └── gemini_service.py  # Extração com Gemini e chave dinâmica em memória RAM
│   ├── static/
│   │   ├── css/custom.css     # Estilos complementares
│   │   └── js/app.js          # Lógica frontend (sessionStorage, upload, tabs)
│   ├── templates/
│   │   ├── login.html         # Página de autenticação segura
│   │   └── index.html         # Painel principal com modal da chave e visualizador
│   ├── auth.py                # Assinatura de sessão HMAC-SHA256 e Rate Limiting
│   ├── config.py              # Configurações do servidor e segurança
│   └── main.py                # Aplicação FastAPI, rotas protegidas e middleware
├── Procfile                   # Comando de inicialização para Render / PaaS
├── render.yaml                # Arquivo Blueprint para deploy em nuvem
├── requirements.txt           # Dependências do projeto
├── .env.example               # Exemplo de variáveis de ambiente
└── README.md                  # Documentação completa
```
