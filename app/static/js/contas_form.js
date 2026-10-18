/**
 * Formulário de Registrar Contas (A Pagar / A Receber).
 * Um registro pode ter uma ou mais classificações e uma ou mais parcelas com vencimentos distintos.
 * Usa o fluxo genérico do crud_form.js por meio dos ganchos aoIniciar / preencher / montar.
 */
(() => {
  const PESSOA_POR_TIPO = { APAGAR: 'FORNECEDOR', ARECEBER: 'CLIENTE' };
  const CLASSIFICACAO_POR_TIPO = { APAGAR: 'DESPESA', ARECEBER: 'RECEITA' };

  const $ = (id) => document.getElementById(id);
  const arred = (v) => Math.round((Number(v) || 0) * 100) / 100;

  // ---------- Selects e checkboxes dependentes do tipo ----------
  async function carregarOpcoes(tipo, selecionados = {}) {
    const [pessoas, faturados, classificacoes] = await Promise.all([
      Comum.api(`/api/pessoas?tipo=${PESSOA_POR_TIPO[tipo]}`),
      Comum.api('/api/pessoas?tipo=FATURADO'),
      Comum.api(`/api/classificacoes?tipo=${CLASSIFICACAO_POR_TIPO[tipo]}`),
    ]);

    $('rotulo-pessoa').textContent = tipo === 'APAGAR' ? 'Fornecedor' : 'Cliente';
    $('rotulo-classificacao').textContent = tipo === 'APAGAR' ? 'Tipos de Despesa' : 'Tipos de Receita';

    const opcao = (p) => `<option value="${p.id}">${Comum.escapar(p.razao_social)}${p.documento ? ' — ' + Comum.formatarDocumento(p.documento) : ''}</option>`;
    $('pessoa_id').innerHTML = '<option value="">Selecione...</option>' + pessoas.map(opcao).join('');
    $('faturado_id').innerHTML = '<option value="">(Nenhum)</option>' + faturados.map(opcao).join('');
    if (selecionados.pessoa_id) $('pessoa_id').value = selecionados.pessoa_id;
    if (selecionados.faturado_id) $('faturado_id').value = selecionados.faturado_id;

    const marcados = new Set(selecionados.classificacoes || []);
    $('lista-classificacoes').innerHTML = classificacoes.length
      ? classificacoes.map(c => `
          <label class="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
            <input type="checkbox" value="${c.id}" ${marcados.has(c.id) ? 'checked' : ''} class="accent-emerald-600">
            ${Comum.escapar(c.descricao)}
          </label>`).join('')
      : `<p class="text-xs text-slate-400">Nenhuma classificação ativa. <a href="/classificacoes/novo?tipo=${CLASSIFICACAO_POR_TIPO[tipo]}" class="text-blue-600 underline">Cadastrar</a></p>`;

    if (!pessoas.length) {
      Comum.alerta(`Nenhum ${PESSOA_POR_TIPO[tipo].toLowerCase()} ativo cadastrado. Cadastre-o em Pessoas antes de registrar a conta.`, 'erro');
    }
  }

  // ---------- Parcelas ----------
  function adicionarParcela(p = {}) {
    const tr = document.createElement('tr');
    tr.className = 'border-t border-slate-100';
    tr.dataset.id = p.id || '';
    tr.innerHTML = `
      <td class="px-3 py-1.5 font-semibold text-slate-600 identificacao"></td>
      <td class="px-3 py-1.5"><input type="date" class="venc px-2 py-1 border border-slate-200 rounded-lg bg-white" value="${p.data_vencimento || ''}"></td>
      <td class="px-3 py-1.5"><input type="number" step="0.01" min="0.01" class="valor w-32 px-2 py-1 border border-slate-200 rounded-lg bg-white" value="${p.valor_parcela ?? ''}"></td>
      <td class="px-3 py-1.5"><input type="number" step="0.01" min="0" class="pago w-32 px-2 py-1 border border-slate-200 rounded-lg bg-white" value="${p.valor_pago ?? 0}"></td>
      <td class="px-3 py-1.5 text-right"><button type="button" class="remover text-slate-400 hover:text-red-600" title="Remover parcela"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button></td>`;
    $('corpo-parcelas').appendChild(tr);
    atualizarResumo();
    if (window.lucide) lucide.createIcons();
  }

  function linhasParcelas() {
    return [...$('corpo-parcelas').querySelectorAll('tr')];
  }

  function atualizarResumo() {
    const linhas = linhasParcelas();
    linhas.forEach((tr, i) => {
      tr.querySelector('.identificacao').textContent = linhas.length === 1 ? 'ÚNICA' : `${i + 1}/${linhas.length}`;
    });
    const soma = arred(linhas.reduce((s, tr) => s + (Number(tr.querySelector('.valor').value) || 0), 0));
    const total = arred($('valor_total').value);
    const confere = Math.abs(soma - total) <= 0.01;
    const resumo = $('resumo-parcelas');
    resumo.textContent = `Soma das parcelas: ${Comum.formatarMoeda(soma)} · Valor total: ${Comum.formatarMoeda(total)}${confere ? ' ✓' : ' — os valores precisam ser iguais'}`;
    resumo.className = `text-[11px] mt-1.5 ${confere ? 'text-emerald-700' : 'text-amber-700'}`;
  }

  function dividirValorTotal() {
    const linhas = linhasParcelas();
    const total = arred($('valor_total').value);
    if (!linhas.length || total <= 0) return;
    const base = Math.floor((total / linhas.length) * 100) / 100;
    linhas.forEach((tr, i) => {
      // a última parcela absorve a diferença de centavos
      const valor = i === linhas.length - 1 ? arred(total - base * (linhas.length - 1)) : base;
      tr.querySelector('.valor').value = valor.toFixed(2);
    });
    atualizarResumo();
  }

  // ---------- Integração com crud_form.js ----------
  window.FORM = {
    endpoint: '/api/contas',
    rotaLista: '/contas',
    registroId: window.REGISTRO_ID,
    nome: 'Conta',

    aoIniciar: async () => {
      $('btn-add-parcela').addEventListener('click', () => adicionarParcela());
      $('btn-dividir').addEventListener('click', dividirValorTotal);
      $('valor_total').addEventListener('input', atualizarResumo);
      $('corpo-parcelas').addEventListener('input', atualizarResumo);
      $('corpo-parcelas').addEventListener('click', (e) => {
        if (e.target.closest('.remover')) {
          if (linhasParcelas().length === 1) return Comum.alerta('A conta precisa de pelo menos uma parcela.', 'erro');
          e.target.closest('tr').remove();
          atualizarResumo();
        }
      });
      $('tipo').addEventListener('change', () => carregarOpcoes($('tipo').value).catch(err => Comum.alerta(err.message, 'erro')));

      if (!window.REGISTRO_ID) {
        await carregarOpcoes($('tipo').value);
        adicionarParcela();
      }
    },

    preencher: async (d) => {
      $('tipo').value = d.tipo;
      await carregarOpcoes(d.tipo, {
        pessoa_id: d.pessoa.id,
        faturado_id: d.faturado ? d.faturado.id : null,
        classificacoes: d.classificacoes.map(c => c.id),
      });
      $('numero_nota_fiscal').value = d.numero_nota_fiscal || '';
      $('data_emissao').value = d.data_emissao || '';
      $('valor_total').value = d.valor_total;
      $('descricao').value = d.descricao || '';
      d.parcelas.filter(p => p.status === 'ATIVO').forEach(adicionarParcela);
      if (!linhasParcelas().length) adicionarParcela();
    },

    montar: () => {
      const classificacao_ids = [...$('lista-classificacoes').querySelectorAll('input:checked')].map(c => Number(c.value));
      if (!$('pessoa_id').value) throw new Error(`Selecione o ${$('rotulo-pessoa').textContent.toLowerCase()}.`);
      if (!classificacao_ids.length) throw new Error('Selecione ao menos uma classificação.');
      if (!(Number($('valor_total').value) > 0)) throw new Error('Informe o valor total.');

      const parcelas = linhasParcelas().map(tr => ({
        id: tr.dataset.id ? Number(tr.dataset.id) : null,
        data_vencimento: tr.querySelector('.venc').value || null,
        valor_parcela: Number(tr.querySelector('.valor').value) || 0,
        valor_pago: Number(tr.querySelector('.pago').value) || 0,
      }));
      if (parcelas.some(p => p.valor_parcela <= 0)) throw new Error('Informe o valor de todas as parcelas.');

      return {
        tipo: $('tipo').value,
        pessoa_id: Number($('pessoa_id').value),
        faturado_id: $('faturado_id').value ? Number($('faturado_id').value) : null,
        numero_nota_fiscal: $('numero_nota_fiscal').value.trim() || null,
        data_emissao: $('data_emissao').value || null,
        valor_total: Number($('valor_total').value),
        descricao: $('descricao').value.trim() || null,
        classificacao_ids,
        parcelas,
      };
    },
  };
})();
