/**
 * Listagem genérica dos cadastros, conforme a recomendação de layout:
 *  - tabela começa vazia;
 *  - dados carregados pela Busca ou pelo botão TODOS (respeitando os filtros de tipo e situação);
 *  - ordenação ao clicar no cabeçalho de cada coluna;
 *  - busca por mais de um elemento (texto em vários campos + tipo + situação);
 *  - ações Editar / Excluir (lógico -> INATIVO) e Reativar para os inativos.
 *
 * Cada página define window.CRUD = { endpoint, rotaForm, nome, colunas: [{ campo, titulo, valor?, html? }] }
 */
document.addEventListener('DOMContentLoaded', () => {
  const cfg = window.CRUD;
  const inputBusca = document.getElementById('filtro-busca');
  const selectTipo = document.getElementById('filtro-tipo');
  const selectStatus = document.getElementById('filtro-status');
  const cabecalho = document.getElementById('tabela-cabecalho');
  const corpo = document.getElementById('tabela-corpo');
  const contador = document.getElementById('contador-registros');

  let registros = [];
  let ordenacao = { campo: null, asc: true };
  let ultimoFiltro = null;

  const valorDe = (col, r) => (col.valor ? col.valor(r) : r[col.campo]);
  const vazio = (msg) => `<tr><td colspan="${cfg.colunas.length + 1}" class="px-3 py-2.5 text-xs text-slate-600 bg-slate-100">${msg}</td></tr>`;

  // ---------- Cabeçalho com indexação (ordenação) por coluna ----------
  function renderizarCabecalho() {
    cabecalho.innerHTML = cfg.colunas.map(col => {
      const ativo = ordenacao.campo === col.campo;
      const seta = ativo ? (ordenacao.asc ? '▲' : '▼') : '';
      return `<th data-campo="${col.campo}" class="px-3 py-2 text-left text-xs font-semibold text-blue-600 underline underline-offset-2 cursor-pointer select-none hover:text-blue-800 whitespace-nowrap border-b-2 border-slate-200">
                ${Comum.escapar(col.titulo)} <span class="text-[9px] no-underline">${seta}</span>
              </th>`;
    }).join('') + '<th class="px-3 py-2 text-right text-xs font-bold text-slate-800 border-b-2 border-slate-200">Ações</th>';

    cabecalho.querySelectorAll('th[data-campo]').forEach(th => {
      th.addEventListener('click', () => {
        const campo = th.dataset.campo;
        ordenacao = { campo, asc: ordenacao.campo === campo ? !ordenacao.asc : true };
        renderizarCabecalho();
        renderizarLinhas();
      });
    });
  }

  function ordenar(lista) {
    if (!ordenacao.campo) return lista;
    const col = cfg.colunas.find(c => c.campo === ordenacao.campo);
    const chave = col.ordenar || ((r) => valorDe(col, r));
    return [...lista].sort((a, b) => {
      let va = chave(a), vb = chave(b);
      va = va ?? ''; vb = vb ?? '';
      const r = (typeof va === 'number' && typeof vb === 'number')
        ? va - vb
        : String(va).localeCompare(String(vb), 'pt-BR', { numeric: true, sensitivity: 'base' });
      return ordenacao.asc ? r : -r;
    });
  }

  // ---------- Linhas ----------
  function renderizarLinhas() {
    contador.textContent = ultimoFiltro ? `${registros.length} registro(s)` : '';
    if (!ultimoFiltro) {
      corpo.innerHTML = vazio('Nenhum registro carregado. Utilize a busca ou clique em "Todos".');
      return;
    }
    if (registros.length === 0) {
      corpo.innerHTML = vazio('Nenhum registro encontrado.');
      return;
    }
    corpo.innerHTML = ordenar(registros).map(r => {
      const celulas = cfg.colunas.map(col => {
        const v = valorDe(col, r);
        return `<td class="px-3 py-2 text-xs text-slate-700 align-top">${col.html ? v : Comum.escapar(v ?? '-')}</td>`;
      }).join('');
      const inativo = r.status === 'INATIVO';
      const acoes = inativo
        ? `<button data-acao="reativar" data-id="${r.id}" class="px-2.5 py-1 text-[11px] font-semibold rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100 inline-flex items-center gap-1"><i data-lucide="rotate-ccw" class="w-3 h-3"></i>Reativar</button>`
        : `<a href="${cfg.rotaForm}/${r.id}/editar" class="px-2.5 py-1 text-[11px] font-semibold rounded bg-blue-50 text-blue-700 hover:bg-blue-100 inline-flex items-center gap-1"><i data-lucide="pencil" class="w-3 h-3"></i>Editar</a>
           <button data-acao="excluir" data-id="${r.id}" class="px-2.5 py-1 text-[11px] font-semibold rounded bg-red-50 text-red-700 hover:bg-red-100 inline-flex items-center gap-1"><i data-lucide="trash-2" class="w-3 h-3"></i>Excluir</button>`;
      return `<tr class="border-t border-slate-100 hover:bg-slate-50/70 ${inativo ? 'opacity-60' : ''}">
                ${celulas}
                <td class="px-3 py-2 text-right whitespace-nowrap space-x-1">${acoes}</td>
              </tr>`;
    }).join('');
    if (window.lucide) lucide.createIcons();
  }

  // ---------- Carregamento ----------
  async function carregar(filtro) {
    Comum.limparAlerta();
    const params = new URLSearchParams();
    Object.entries(filtro).forEach(([k, v]) => { if (v) params.append(k, v); });
    corpo.innerHTML = vazio('Carregando...');
    try {
      registros = await Comum.api(`${cfg.endpoint}?${params}`);
      ultimoFiltro = filtro;
    } catch (err) {
      registros = [];
      ultimoFiltro = null;
      Comum.alerta(err.message, 'erro');
    }
    renderizarLinhas();
  }

  function filtroAtual() {
    return {
      busca: inputBusca.value.trim(),
      tipo: selectTipo ? selectTipo.value : '',
      status: selectStatus.value,
    };
  }

  document.getElementById('btn-buscar').addEventListener('click', () => carregar(filtroAtual()));
  inputBusca.addEventListener('keydown', (e) => { if (e.key === 'Enter') carregar(filtroAtual()); });

  // TODOS: limpa o texto de busca e carrega todos os registros com os filtros atuais
  document.getElementById('btn-todos').addEventListener('click', () => {
    inputBusca.value = '';
    carregar(filtroAtual());
  });

  // Excluir (lógico) / Reativar
  corpo.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-acao]');
    if (!btn) return;
    const id = btn.dataset.id;
    try {
      let mensagem;
      if (btn.dataset.acao === 'excluir') {
        if (!confirm(`Deseja excluir (inativar) este registro de ${cfg.nome}? Ele poderá ser reativado depois.`)) return;
        await Comum.api(`${cfg.endpoint}/${id}`, { method: 'DELETE' });
        mensagem = `Registro ${id} inativado com sucesso.`;
      } else {
        await Comum.api(`${cfg.endpoint}/${id}/reativar`, { method: 'POST' });
        mensagem = `Registro ${id} reativado com sucesso.`;
      }
      await carregar(ultimoFiltro || filtroAtual());
      Comum.alerta(mensagem, 'sucesso');
    } catch (err) {
      Comum.alerta(err.message, 'erro');
    }
  });

  renderizarCabecalho();
  renderizarLinhas();
});
