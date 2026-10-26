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
  const errorDetalhes = document.getElementById('error-detalhes');
  const errorDetalhesTexto = document.getElementById('error-detalhes-texto');
  const btnTentarNovamente = document.getElementById('btn-tentar-novamente');
  const loadingEtapa = document.getElementById('loading-etapa');
  const loadingSegundos = document.getElementById('loading-segundos');
  const loadingFeed = document.getElementById('loading-feed');
  const badgeTempo = document.getElementById('badge-tempo');
  const badgeTempoTexto = document.getElementById('badge-tempo-texto');

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

  // --- Análise no Banco de Dados e Lançamento (2ª Etapa) ---
  const analiseSection = document.getElementById('analise-section');
  const analiseCarregando = document.getElementById('analise-carregando');
  const analiseResultado = document.getElementById('analise-resultado');
  const analiseAviso = document.getElementById('analise-aviso');
  const btnReanalisar = document.getElementById('btn-reanalisar');
  const btnLancar = document.getElementById('btn-lancar');
  const lancamentoSucesso = document.getElementById('lancamento-sucesso');

  let arquivoSelecionado = null;
  let ultimoJsonExtraido = null;
  let notaLancada = false;  // impede lançar a mesma extração duas vezes
  let cardTentativaAtual = null;
  const cardTentativasPorModelo = new Map();

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

  // (O logout seguro, que também descarta a chave volátil, fica em comum.js)

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
    analiseSection.classList.add('hidden');
    ultimoJsonExtraido = null;
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
    analiseSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    btnProcessar.disabled = true;
    cardTentativaAtual = null;
    cardTentativasPorModelo.clear();
    if (loadingFeed) loadingFeed.innerHTML = '';
    if (loadingEtapa) loadingEtapa.textContent = 'Enviando PDF para análise com IA...';
    
    const inicio = iniciarCronometro();

    const formData = new FormData();
    formData.append('arquivo', arquivoSelecionado);

    let sucessoRecebido = false;

    try {
      const response = await fetch('/api/processar-nota', {
        method: 'POST',
        headers: {
          'X-Gemini-API-Key': chaveGemini
        },
        body: formData,
      });

      if (response.status === 401) {
        window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Erro ao comunicar com o servidor.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocos = buffer.split('\n\n');
        buffer = blocos.pop(); // Mantém pedaço incompleto no buffer

        for (const bloco of blocos) {
          const linhas = bloco.split('\n');
          for (const linha of linhas) {
            const trimmed = linha.trim();
            if (!trimmed.startsWith('data:')) continue;
            const payload = trimmed.replace(/^data:\s*/, '');
            try {
              const evento = JSON.parse(payload);
              await processarEventoStream(evento, inicio);
              if (evento.tipo === 'sucesso') {
                sucessoRecebido = true;
              }
            } catch (errJson) {
              console.warn('Erro ao ler evento SSE:', errJson, payload);
            }
          }
        }
      }

      if (!sucessoRecebido && !errorAlert.classList.contains('hidden')) {
        // Erro já tratado no evento tipo 'erro'
      } else if (!sucessoRecebido) {
        throw new Error('A conexão foi encerrada antes da finalização da resposta.');
      }

    } catch (err) {
      pararCronometro();
      if (cardTentativaAtual) {
        atualizarCardTentativa(cardTentativaAtual, {
          tipo: 'erro',
          mensagem: 'Falha no processamento',
          detalhes: err.message
        });
        cardTentativaAtual = null;
      } else {
        adicionarItemFeed('erro', 'Falha no processamento', err.message);
      }
      exibirErroExtracao(err.message);
    } finally {
      pararCronometro();
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
  // 8. Análise no Banco de Dados (FORNECEDOR / FATURADO / DESPESA)
  // ==============================================================

  function blocoAnalise(titulo, item, rotuloDocumento) {
    let situacao;
    if (!item.existe) {
      situacao = '<p class="font-extrabold text-red-600">NÃO EXISTE <span class="font-medium text-[11px] text-slate-500">(será criado ao lançar)</span></p>';
    } else if (item.status === 'INATIVO') {
      situacao = `<p class="font-extrabold text-blue-600">EXISTE – ID: ${item.id} <span class="font-semibold text-[11px] text-amber-700">(INATIVO – será reativado ao lançar)</span></p>`;
    } else {
      situacao = `<p class="font-extrabold text-blue-600">EXISTE – ID: ${item.id}</p>`;
    }
    const documento = rotuloDocumento
      ? `<p class="text-xs text-slate-600">${rotuloDocumento}: <span class="font-mono">${Comum.escapar(Comum.formatarDocumento(item.documento))}</span></p>`
      : '';
    return `
      <div>
        <p class="text-xs font-extrabold uppercase tracking-wider text-slate-900">${titulo}</p>
        <p class="font-medium text-slate-800">${Comum.escapar(item.descricao || 'Não informado')}</p>
        ${documento}
        ${situacao}
      </div>`;
  }

  async function analisarNota() {
    if (!ultimoJsonExtraido) return;
    analiseSection.classList.remove('hidden');
    analiseCarregando.classList.remove('hidden');
    analiseResultado.innerHTML = '';
    analiseAviso.classList.add('hidden');
    btnLancar.disabled = true;

    try {
      const analise = await Comum.api('/api/analisar', { method: 'POST', body: ultimoJsonExtraido });
      const faturadoDoc = (analise.faturado.documento || '').length === 14 ? 'CNPJ' : 'CPF';

      analiseResultado.innerHTML =
        blocoAnalise('Fornecedor', analise.fornecedor, 'CNPJ') +
        blocoAnalise('Faturado', analise.faturado, faturadoDoc) +
        analise.despesas.map(d => blocoAnalise('Despesa', d)).join('');

      if (analise.movimento_existente_id) {
        analiseAviso.innerHTML = `Esta nota já foi lançada (Movimento ID ${analise.movimento_existente_id}). ` +
          `<a href="/contas/${analise.movimento_existente_id}/editar" class="font-bold underline">Ver lançamento</a>`;
        analiseAviso.classList.remove('hidden');
      } else {
        btnLancar.disabled = notaLancada;
      }
    } catch (err) {
      analiseResultado.innerHTML = `<p class="text-xs text-red-700">${Comum.escapar(err.message)}</p>`;
    } finally {
      analiseCarregando.classList.add('hidden');
      if (window.lucide) lucide.createIcons();
    }
  }

  btnReanalisar.addEventListener('click', analisarNota);

  // Cria o que não existe + MOVIMENTO + PARCELA(S) e informa o sucesso ao usuário
  btnLancar.addEventListener('click', async () => {
    if (!ultimoJsonExtraido) return;
    btnLancar.disabled = true;
    lancamentoSucesso.classList.add('hidden');
    try {
      const r = await Comum.api('/api/lancar', { method: 'POST', body: ultimoJsonExtraido });
      const detalhes = [
        ...r.criados.map(c => `Criado: ${c}`),
        ...r.reativados.map(c => `Reativado: ${c}`),
      ];
      lancamentoSucesso.innerHTML = `
        <div class="flex items-start gap-3">
          <i data-lucide="check-circle" class="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0"></i>
          <div class="text-xs text-emerald-800 space-y-1">
            <p class="text-sm font-bold">${Comum.escapar(r.mensagem)}</p>
            ${detalhes.map(d => `<p>• ${Comum.escapar(d)}</p>`).join('')}
            <a href="/contas/${r.movimento_id}/editar" class="inline-block mt-1 font-bold underline">Ver registro lançado</a>
          </div>
        </div>`;
      lancamentoSucesso.classList.remove('hidden');
      notaLancada = true;
      await analisarNota();  // atualiza a análise: agora tudo EXISTE
      lancamentoSucesso.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      exibirErro(err.message);
      btnLancar.disabled = false;
    } finally {
      if (window.lucide) lucide.createIcons();
    }
  });

  // ==============================================================
  // 9. Funções Utilitárias
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

  function exibirErro(msg, detalhes = '', podeTentarNovamente = false) {
    errorMessageEl.textContent = msg;
    errorDetalhesTexto.textContent = detalhes;
    errorDetalhes.classList.toggle('hidden', !detalhes);
    errorDetalhes.open = false;
    btnTentarNovamente.classList.toggle('hidden', !podeTentarNovamente);
    errorAlert.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
  }

  // Traduz os erros técnicos da API do Gemini para mensagens amigáveis
  function exibirErroExtracao(msg) {
    const traducoes = [
      [/API key|API_KEY_INVALID|PERMISSION_DENIED|\b40[13]\b/i, 'Sua chave de API do Gemini parece inválida ou sem permissão. Verifique a chave e tente novamente.'],
      [/\b503\b|UNAVAILABLE|high demand/i, 'Os servidores do Gemini estão com alta demanda. Tente novamente em alguns instantes.'],
      [/\b429\b|RESOURCE_EXHAUSTED|quota/i, 'O limite de uso da sua chave do Gemini foi atingido. Aguarde alguns minutos e tente novamente.'],
      [/timeout|timed out|DEADLINE/i, 'A IA demorou demais para responder. Tente novamente.'],
      [/Failed to fetch|NetworkError/i, 'Não foi possível conectar ao servidor. Verifique sua conexão.'],
    ];
    const encontrada = traducoes.find(([padrao]) => padrao.test(msg));
    if (encontrada) {
      exibirErro(encontrada[1], msg, true);
    } else {
      exibirErro(msg, '', true);  // mensagens do servidor já em português
    }
  }

  btnTentarNovamente.addEventListener('click', () => btnProcessar.click());

  // ==============================================================
  // Feedback Visual em Tempo Real (SSE Streaming + Cronômetro)
  // ==============================================================

  let timerInterval = null;

  function iniciarCronometro() {
    const inicio = Date.now();
    if (loadingSegundos) loadingSegundos.textContent = '0,0s';
    badgeTempo.classList.add('hidden');
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const s = ((Date.now() - inicio) / 1000).toFixed(1).replace('.', ',');
      if (loadingSegundos) loadingSegundos.textContent = `${s}s`;
    }, 100);
    return inicio;
  }

  function pararCronometro() {
    clearInterval(timerInterval);
  }

  function adicionarItemFeed(tipo, mensagem, detalhes = '') {
    if (!loadingFeed) return null;
    const item = document.createElement('div');
    item.className = 'flex items-start gap-2.5 p-2.5 rounded-xl text-xs transition-all';

    let icone = 'clock';
    let corFundo = 'bg-slate-50 border border-slate-100 text-slate-700';

    if (tipo === 'info') {
      icone = 'info';
      corFundo = 'bg-slate-50 border border-slate-200 text-slate-700';
    } else if (tipo === 'tentativa') {
      icone = 'loader-2';
      corFundo = 'bg-blue-50/70 border border-blue-200 text-blue-900 font-medium';
    } else if (tipo === 'aviso') {
      icone = 'alert-triangle';
      corFundo = 'bg-amber-50/90 border border-amber-200 text-amber-900';
    } else if (tipo === 'sucesso') {
      icone = 'check-circle-2';
      corFundo = 'bg-emerald-50 border border-emerald-200 text-emerald-900 font-semibold';
    } else if (tipo === 'erro') {
      icone = 'x-circle';
      corFundo = 'bg-red-50/80 border border-red-200 text-red-900 font-semibold';
    }

    item.className += ' ' + corFundo;
    item.innerHTML = `
      <i data-lucide="${icone}" class="w-4 h-4 mt-0.5 flex-shrink-0 ${tipo === 'tentativa' ? 'animate-spin text-blue-600' : ''}"></i>
      <div class="flex-1">
        <div class="feed-item-titulo">${mensagem}</div>
        ${detalhes ? `<div class="feed-item-detalhes mt-0.5 text-[10px] opacity-75 font-mono break-words">${detalhes}</div>` : '<div class="feed-item-detalhes mt-0.5 text-[10px] opacity-75 font-mono break-words hidden"></div>'}
      </div>
    `;

    loadingFeed.appendChild(item);
    if (window.lucide) lucide.createIcons();
    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return item;
  }

  function atualizarCardTentativa(card, { tipo, mensagem, detalhes = '' }) {
    if (!card) return;

    let icone = 'x-circle';
    let classesCard = 'bg-red-50/80 border-red-200 text-red-900';
    let corIcone = 'text-red-600';

    if (tipo === 'sucesso') {
      icone = 'check-circle-2';
      classesCard = 'bg-emerald-50 border-emerald-200 text-emerald-900 font-semibold';
      corIcone = 'text-emerald-600';
    } else if (tipo === 'aviso' || tipo === 'erro') {
      icone = 'x-circle';
      classesCard = 'bg-red-50/80 border-red-200 text-red-900';
      corIcone = 'text-red-600';
    }

    // Remove classes de outros estados e aplica o novo tema
    card.classList.remove(
      'bg-blue-50/70', 'border-blue-200', 'text-blue-900', 'font-medium',
      'bg-amber-50/90', 'border-amber-200', 'text-amber-900',
      'bg-emerald-50', 'border-emerald-200', 'text-emerald-900', 'font-semibold',
      'bg-red-50/80', 'border-red-200', 'text-red-900'
    );
    card.className = `flex items-start gap-2.5 p-2.5 rounded-xl text-xs transition-all border ${classesCard}`;

    // Substitui o ícone com animate-spin pelo ícone de resultado estático
    const iconEl = card.querySelector('svg, i');
    if (iconEl) {
      iconEl.outerHTML = `<i data-lucide="${icone}" class="w-4 h-4 mt-0.5 flex-shrink-0 ${corIcone}"></i>`;
    }

    // Atualiza o texto do título
    const tituloEl = card.querySelector('.feed-item-titulo') || card.querySelector('.flex-1 > div');
    if (tituloEl && mensagem) {
      tituloEl.textContent = mensagem;
    }

    // Atualiza os detalhes
    let detalhesEl = card.querySelector('.feed-item-detalhes');
    if (!detalhesEl && detalhes) {
      detalhesEl = document.createElement('div');
      detalhesEl.className = 'feed-item-detalhes mt-0.5 text-[10px] opacity-75 font-mono break-words';
      const containerTexto = card.querySelector('.flex-1');
      if (containerTexto) containerTexto.appendChild(detalhesEl);
    }
    if (detalhesEl) {
      if (detalhes) {
        detalhesEl.textContent = detalhes;
        detalhesEl.classList.remove('hidden');
      } else {
        detalhesEl.textContent = '';
        detalhesEl.classList.add('hidden');
      }
    }

    if (window.lucide) lucide.createIcons();
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  async function processarEventoStream(evento, inicio) {
    if (evento.tipo === 'info') {
      if (loadingEtapa) loadingEtapa.textContent = evento.mensagem;
      adicionarItemFeed('info', evento.mensagem);

    } else if (evento.tipo === 'tentativa') {
      if (loadingEtapa) loadingEtapa.textContent = `Processando com ${evento.modelo}...`;
      const card = adicionarItemFeed('tentativa', evento.mensagem);
      cardTentativaAtual = card;
      if (evento.modelo) {
        cardTentativasPorModelo.set(evento.modelo, card);
      }

    } else if (evento.tipo === 'aviso') {
      // Falha na tentativa atual: atualiza o card giratório para x-circle vermelho
      if (loadingEtapa) loadingEtapa.textContent = `Aviso em ${evento.modelo}: alternando modelo...`;
      const card = (evento.modelo && cardTentativasPorModelo.get(evento.modelo)) || cardTentativaAtual;
      if (card) {
        atualizarCardTentativa(card, {
          tipo: 'aviso',
          mensagem: evento.mensagem,
          detalhes: evento.detalhes
        });
        if (cardTentativaAtual === card) {
          cardTentativaAtual = null;
        }
      } else {
        adicionarItemFeed('erro', evento.mensagem, evento.detalhes);
      }

    } else if (evento.tipo === 'sucesso') {
      // Sucesso na tentativa atual: atualiza o card para check-circle-2 verde
      const card = (evento.modelo && cardTentativasPorModelo.get(evento.modelo)) || cardTentativaAtual;
      if (card) {
        atualizarCardTentativa(card, {
          tipo: 'sucesso',
          mensagem: evento.mensagem
        });
      } else {
        adicionarItemFeed('sucesso', evento.mensagem);
      }

      if (loadingEtapa) loadingEtapa.textContent = 'Extração finalizada com sucesso!';

      // Pausa breve (~700ms) para exibir o feedback de sucesso no feed antes de mostrar os dados
      await new Promise(resolve => setTimeout(resolve, 700));

      pararCronometro();
      const tempoTotal = ((Date.now() - inicio) / 1000).toFixed(1).replace('.', ',');
      
      const dados = evento.dados;
      ultimoJsonExtraido = dados;
      renderizarResultados(dados);

      badgeTempoTexto.textContent = `Extraído em ${tempoTotal}s via ${evento.modelo}`;
      badgeTempo.classList.remove('hidden');

      ativarAba('json');
      loadingIndicator.classList.add('hidden');
      resultsSection.classList.remove('hidden');
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Análise automática no banco de dados
      lancamentoSucesso.classList.add('hidden');
      notaLancada = false;
      analisarNota();

    } else if (evento.tipo === 'erro') {
      pararCronometro();
      const card = (evento.modelo && cardTentativasPorModelo.get(evento.modelo)) || cardTentativaAtual;
      if (card) {
        atualizarCardTentativa(card, {
          tipo: 'erro',
          mensagem: evento.mensagem,
          detalhes: evento.detalhes
        });
        cardTentativaAtual = null;
      } else {
        adicionarItemFeed('erro', evento.mensagem, evento.detalhes);
      }
      exibirErroExtracao(evento.detalhes || evento.mensagem);
    }
  }

  function ocultarErro() {
    errorAlert.classList.add('hidden');
  }
});
