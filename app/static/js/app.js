/**
 * Frontend - Processamento de Notas Fiscais com Gemini e Chave Volátil em Memória
 */

document.addEventListener('DOMContentLoaded', () => {
  const STORAGE_KEY_GEMINI = 'gemini_api_key';

  // --- Elementos de Chave e Sessão ---
  const modalChave = document.getElementById('modal-chave');
  const btnStatusChave = document.getElementById('btn-status-chave');
  const dotStatusChave = document.getElementById('dot-status-chave');
  const labelStatusChave = document.getElementById('label-status-chave');
  const btnFecharModal = document.getElementById('btn-fechar-modal');
  const btnCancelarModal = document.getElementById('btn-cancelar-modal');
  const btnLimparChave = document.getElementById('btn-limpar-chave');
  const formChaveGemini = document.getElementById('form-chave-gemini');
  const inputApiKey = document.getElementById('input-api-key');
  const toggleModalKey = document.getElementById('toggle-modal-key');
  const iconEyeModal = document.getElementById('icon-eye-modal');
  const btnLogout = document.getElementById('btn-logout');

  // --- Elementos de Upload ---
  const filePickerBox = document.getElementById('file-picker-box');
  const fileInput = document.getElementById('file-input');
  const filePickerName = document.getElementById('file-picker-name');
  const fileInfoContainer = document.getElementById('file-info-container');
  const fileNameEl = document.getElementById('file-name');
  const fileSizeEl = document.getElementById('file-size');
  const btnRemover = document.getElementById('btn-remover');
  const btnProcessar = document.getElementById('btn-processar');

  // --- Indicadores de status e erro ---
  const loadingIndicator = document.getElementById('loading-indicator');
  const errorAlert = document.getElementById('error-alert');
  const errorMessageEl = document.getElementById('error-message');

  // --- Seção de Resultados ---
  const resultsSection = document.getElementById('results-section');
  const tabBtnFormatada = document.getElementById('tab-btn-formatada');
  const tabBtnJson = document.getElementById('tab-btn-json');
  const viewFormatada = document.getElementById('view-formatada');
  const viewJson = document.getElementById('view-json');

  // --- JSON e Cópia ---
  const jsonViewer = document.getElementById('json-viewer');
  const btnCopiarJson = document.getElementById('btn-copiar-json');
  const copiarText = document.getElementById('copiar-text');

  // --- Campos da Visualização Formatada ---
  const badgeCategoria = document.getElementById('badge-categoria');
  const cardSubcategoria = document.getElementById('card-subcategoria');
  const cardJustificativa = document.getElementById('card-justificativa');
  const cardNumeroNf = document.getElementById('card-numero-nf');
  const cardDataEmissao = document.getElementById('card-data-emissao');
  const cardDataVencimento = document.getElementById('card-data-vencimento');
  const cardValorTotal = document.getElementById('card-valor-total');
  const cardFornecedorRazao = document.getElementById('card-fornecedor-razao');
  const cardFornecedorFantasia = document.getElementById('card-fornecedor-fantasia');
  const cardFornecedorCnpj = document.getElementById('card-fornecedor-cnpj');
  const cardFaturadoNome = document.getElementById('card-faturado-nome');
  const cardFaturadoCpf = document.getElementById('card-faturado-cpf');
  const cardDescricaoProdutos = document.getElementById('card-descricao-produtos');
  const cardQtdParcelas = document.getElementById('card-qtd-parcelas');
  const listaParcelas = document.getElementById('lista-parcelas');

  let arquivoSelecionado = null;
  let ultimoJsonExtraido = null;

  // ==============================================================
  // 1. Gerenciamento da Chave Volátil do Gemini (sessionStorage)
  // ==============================================================

  function obterChaveArmazenada() {
    return (sessionStorage.getItem(STORAGE_KEY_GEMINI) || '').trim();
  }

  function atualizarStatusChave() {
    const chave = obterChaveArmazenada();
    if (chave) {
      // Chave ativa
      btnStatusChave.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition border bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100';
      dotStatusChave.className = 'w-2 h-2 rounded-full bg-emerald-500';
      labelStatusChave.textContent = 'Chave Gemini Ativa';
      btnLimparChave.classList.remove('hidden');
    } else {
      // Chave pendente
      btnStatusChave.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition border bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100';
      dotStatusChave.className = 'w-2 h-2 rounded-full bg-amber-500 animate-pulse';
      labelStatusChave.textContent = 'Configurar Chave Gemini';
      btnLimparChave.classList.add('hidden');
    }
    if (window.lucide) lucide.createIcons();
  }

  function abrirModalChave() {
    inputApiKey.value = obterChaveArmazenada();
    modalChave.classList.remove('hidden');
    inputApiKey.focus();
    if (window.lucide) lucide.createIcons();
  }

  function fecharModalChave() {
    modalChave.classList.add('hidden');
  }

  btnStatusChave.addEventListener('click', abrirModalChave);
  btnFecharModal.addEventListener('click', fecharModalChave);
  btnCancelarModal.addEventListener('click', fecharModalChave);

  // Fechar ao clicar fora do card do modal
  modalChave.addEventListener('click', (e) => {
    if (e.target === modalChave) {
      fecharModalChave();
    }
  });

  // Alternar visibilidade da senha no modal
  toggleModalKey.addEventListener('click', () => {
    const tipo = inputApiKey.type === 'password' ? 'text' : 'password';
    inputApiKey.type = tipo;
    iconEyeModal.setAttribute('data-lucide', tipo === 'password' ? 'eye' : 'eye-off');
    if (window.lucide) lucide.createIcons();
  });

  // Salvar chave no sessionStorage (volátil, nunca salva em disco ou servidor)
  formChaveGemini.addEventListener('submit', (e) => {
    e.preventDefault();
    const chave = inputApiKey.value.trim();
    if (!chave) return;

    sessionStorage.setItem(STORAGE_KEY_GEMINI, chave);
    atualizarStatusChave();
    fecharModalChave();
    ocultarErro();
  });

  // Botão para remover a chave da memória
  btnLimparChave.addEventListener('click', () => {
    sessionStorage.removeItem(STORAGE_KEY_GEMINI);
    inputApiKey.value = '';
    atualizarStatusChave();
    fecharModalChave();
  });

  // Se não houver chave na sessão ao carregar a tela, abre o modal automaticamente após 300ms
  atualizarStatusChave();
  if (!obterChaveArmazenada()) {
    setTimeout(abrirModalChave, 300);
  }

  // ==============================================================
  // 2. Logout Seguro
  // ==============================================================

  btnLogout.addEventListener('click', async () => {
    // 1. Limpa a chave volátil da memória do navegador
    sessionStorage.removeItem(STORAGE_KEY_GEMINI);
    try {
      // 2. Encerra a sessão no backend (limpa o cookie)
      await fetch('/api/logout', { method: 'POST' });
    } finally {
      // 3. Redireciona para o login
      window.location.href = '/login';
    }
  });

  // ==============================================================
  // 3. Handlers de Seleção de Arquivo e Drag & Drop
  // ==============================================================

  filePickerBox.addEventListener('click', () => fileInput.click());

  filePickerBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    filePickerBox.classList.add('border-slate-400', 'bg-slate-200/50');
  });

  filePickerBox.addEventListener('dragleave', () => {
    filePickerBox.classList.remove('border-slate-400', 'bg-slate-200/50');
  });

  filePickerBox.addEventListener('drop', (e) => {
    e.preventDefault();
    filePickerBox.classList.remove('border-slate-400', 'bg-slate-200/50');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      tratarArquivo(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      tratarArquivo(e.target.files[0]);
    }
  });

  btnRemover.addEventListener('click', (e) => {
    e.stopPropagation();
    limparArquivo();
  });

  function tratarArquivo(file) {
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      exibirErro('Por favor, selecione um arquivo válido no formato PDF.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      exibirErro('O arquivo selecionado excede o limite máximo permitido de 10 MB.');
      return;
    }

    ocultarErro();
    arquivoSelecionado = file;

    filePickerName.textContent = file.name;
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatarTamanhoMB(file.size);
    fileInfoContainer.classList.remove('hidden');

    if (window.lucide) lucide.createIcons();
  }

  function limparArquivo() {
    arquivoSelecionado = null;
    fileInput.value = '';
    filePickerName.textContent = 'Nenhum arquivo selecionado';
    fileInfoContainer.classList.add('hidden');
    resultsSection.classList.add('hidden');
    ocultarErro();
  }

  function formatarTamanhoMB(bytes) {
    if (!bytes) return '0.00 MB';
    const mb = bytes / (1024 * 1024);
    if (mb < 0.01) return '0.01 MB';
    return mb.toFixed(2) + ' MB';
  }

  // ==============================================================
  // 4. Alternador de Abas (Visualização Formatada vs JSON)
  // ==============================================================

  tabBtnFormatada.addEventListener('click', () => ativarAba('formatada'));
  tabBtnJson.addEventListener('click', () => ativarAba('json'));

  function ativarAba(aba) {
    if (aba === 'formatada') {
      tabBtnFormatada.classList.add('bg-white', 'text-slate-900', 'shadow-xs');
      tabBtnFormatada.classList.remove('text-slate-600');
      tabBtnJson.classList.remove('bg-white', 'text-slate-900', 'shadow-xs');
      tabBtnJson.classList.add('text-slate-600');

      viewFormatada.classList.remove('hidden');
      viewJson.classList.add('hidden');
    } else {
      tabBtnJson.classList.add('bg-white', 'text-slate-900', 'shadow-xs');
      tabBtnJson.classList.remove('text-slate-600');
      tabBtnFormatada.classList.remove('bg-white', 'text-slate-900', 'shadow-xs');
      tabBtnFormatada.classList.add('text-slate-600');

      viewJson.classList.remove('hidden');
      viewFormatada.classList.add('hidden');
    }
  }

  // ==============================================================
  // 5. Processamento com a IA (Envio da Chave via Header Seguro)
  // ==============================================================

  btnProcessar.addEventListener('click', async () => {
    if (!arquivoSelecionado) {
      exibirErro('Selecione um arquivo PDF de nota fiscal primeiro.');
      return;
    }

    const chaveGemini = obterChaveArmazenada();
    if (!chaveGemini) {
      abrirModalChave();
      exibirErro('Por favor, informe sua Chave de API do Gemini para continuar.');
      return;
    }

    ocultarErro();
    resultsSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    btnProcessar.disabled = true;

    const formData = new FormData();
    formData.append('arquivo', arquivoSelecionado);

    try {
      const response = await fetch('/api/processar-nota', {
        method: 'POST',
        headers: {
          'X-Gemini-API-Key': chaveGemini
        },
        body: formData,
      });

      const data = await response.json();

      // Sessão expirada
      if (response.status === 401) {
        window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        throw new Error(data.detail || 'Erro ao processar a nota fiscal.');
      }

      ultimoJsonExtraido = data;
      renderizarResultados(data);

      // Garante que a aba JSON está ativa por padrão como no modelo
      ativarAba('json');

      resultsSection.classList.remove('hidden');
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
      exibirErro(err.message);
    } finally {
      loadingIndicator.classList.add('hidden');
      btnProcessar.disabled = false;
      if (window.lucide) lucide.createIcons();
    }
  });

  // ==============================================================
  // 6. Renderização dos Resultados Extraídos
  // ==============================================================

  function renderizarResultados(dados) {
    // 1. Classificação da Despesa
    const classificacao = dados.classificacoes_despesa && dados.classificacoes_despesa.length > 0
      ? dados.classificacoes_despesa[0]
      : { categoria: 'MANUTENÇÃO E OPERAÇÃO', subcategoria_sugerida: 'Geral', justificativa: 'Classificação automática' };

    badgeCategoria.textContent = classificacao.categoria || 'MANUTENÇÃO E OPERAÇÃO';
    cardSubcategoria.textContent = classificacao.subcategoria_sugerida || '-';
    cardJustificativa.textContent = classificacao.justificativa || '-';

    // 2. Dados Gerais da Nota
    cardNumeroNf.textContent = dados.numero_nota_fiscal || 'N/A';
    cardDataEmissao.textContent = formatarDataBR(dados.data_emissao);
    cardDataVencimento.textContent = formatarDataBR(dados.data_vencimento);
    cardValorTotal.textContent = formatarMoedaBR(dados.valor_total);

    // 3. Fornecedor
    const fornecedor = dados.fornecedor || {};
    cardFornecedorRazao.textContent = fornecedor.razao_social || 'Não informado';
    cardFornecedorFantasia.textContent = fornecedor.nome_fantasia || 'Não informado';
    cardFornecedorCnpj.textContent = fornecedor.cnpj || 'Não informado';

    // 4. Faturado
    const faturado = dados.faturado || {};
    cardFaturadoNome.textContent = faturado.nome_completo || 'Não informado';
    cardFaturadoCpf.textContent = faturado.cpf || 'Não informado';

    // 5. Descrição de Produtos
    cardDescricaoProdutos.textContent = dados.descricao_produtos || 'Nenhuma descrição encontrada na nota.';

    // 6. Parcelas
    cardQtdParcelas.textContent = dados.quantidade_parcelas || 1;
    listaParcelas.innerHTML = '';
    const parcelas = dados.parcelas && dados.parcelas.length > 0
      ? dados.parcelas
      : [{ numero: 1, data_vencimento: dados.data_vencimento, valor: dados.valor_total }];

    parcelas.forEach(p => {
      const row = document.createElement('div');
      row.className = 'flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs';
      row.innerHTML = `
        <span class="font-semibold text-slate-700">Parcela ${p.numero || 1}</span>
        <span class="text-slate-500">Vencimento: <strong class="text-slate-800">${formatarDataBR(p.data_vencimento)}</strong></span>
        <span class="font-bold text-emerald-700">${formatarMoedaBR(p.valor)}</span>
      `;
      listaParcelas.appendChild(row);
    });

    // 7. Visualizador de JSON com destaque de sintaxe escuro
    const jsonString = JSON.stringify(dados, null, 2);
    jsonViewer.innerHTML = destacarSintaxeJson(jsonString);

    if (window.lucide) lucide.createIcons();
  }

  // ==============================================================
  // 7. Botão Copiar JSON
  // ==============================================================

  btnCopiarJson.addEventListener('click', async () => {
    if (!ultimoJsonExtraido) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(ultimoJsonExtraido, null, 2));
      copiarText.textContent = 'Copiado!';
      btnCopiarJson.classList.add('bg-emerald-50', 'text-emerald-700', 'border-emerald-300');
      setTimeout(() => {
        copiarText.textContent = 'Copiar JSON';
        btnCopiarJson.classList.remove('bg-emerald-50', 'text-emerald-700', 'border-emerald-300');
      }, 2000);
    } catch (err) {
      console.error('Falha ao copiar JSON:', err);
    }
  });

  // ==============================================================
  // 8. Funções Utilitárias
  // ==============================================================

  function formatarMoedaBR(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) return 'R$ 0,00';
    return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  function formatarDataBR(dataIso) {
    if (!dataIso) return '-';
    const partes = dataIso.split('-');
    if (partes.length === 3) {
      return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }
    return dataIso;
  }

  function destacarSintaxeJson(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      function (match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'json-key';
            const colonIndex = match.lastIndexOf(':');
            const keyPart = match.substring(0, colonIndex);
            return '<span class="json-key">' + keyPart + '</span><span class="json-colon">:</span>';
          } else {
            cls = 'json-string';
          }
        } else if (/true|false/.test(match)) {
          cls = 'json-boolean';
        } else if (/null/.test(match)) {
          cls = 'json-null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
      }
    );
  }

  function exibirErro(msg) {
    errorMessageEl.textContent = msg;
    errorAlert.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
  }

  function ocultarErro() {
    errorAlert.classList.add('hidden');
  }
});
