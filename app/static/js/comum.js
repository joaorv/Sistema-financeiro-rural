/**
 * Utilitários compartilhados por todas as telas (chamadas à API, formatação, mensagens).
 */
const Comum = (() => {
  const FLASH_KEY = 'mensagem_flash';

  // Chamada à API com tratamento padrão de erros (401 -> login; detail do FastAPI -> mensagem)
  async function api(url, opcoes = {}) {
    const config = { ...opcoes, headers: { ...(opcoes.headers || {}) } };
    if (config.body && typeof config.body !== 'string' && !(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(config.body);
    }
    const resposta = await fetch(url, config);
    if (resposta.status === 401) {
      window.location.href = '/login';
      throw new Error('Sessão expirada.');
    }
    const dados = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(mensagemErro(dados));
    return dados;
  }

  function mensagemErro(dados) {
    const detalhe = dados && dados.detail;
    if (Array.isArray(detalhe)) {
      // Erros de validação do Pydantic (422)
      return detalhe.map(e => (e.msg || '').replace(/^Value error, /, '')).join(' ');
    }
    return detalhe || 'Ocorreu um erro inesperado.';
  }

  function escapar(texto) {
    return String(texto ?? '').replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  function formatarDocumento(doc) {
    const d = String(doc || '').replace(/\D/g, '');
    if (d.length === 11) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    if (d.length === 14) return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    return doc || '-';
  }

  // Máscara de CPF/CNPJ enquanto o usuário digita
  function mascaraDocumento(input) {
    input.addEventListener('input', () => {
      const d = input.value.replace(/\D/g, '').slice(0, 14);
      if (d.length <= 11) {
        input.value = d.replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2');
      } else {
        input.value = d.replace(/(\d{2})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1/$2').replace(/(\d{4})(\d{1,2})$/, '$1-$2');
      }
    });
  }

  function formatarMoeda(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) return 'R$ 0,00';
    return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  function formatarData(iso) {
    if (!iso) return '-';
    const p = String(iso).split('-');
    return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : iso;
  }

  // Mensagem de sucesso/erro no topo do conteúdo
  function alerta(mensagem, tipo = 'sucesso') {
    const area = document.getElementById('area-alerta');
    if (!area) return alert(mensagem);
    const cores = tipo === 'sucesso'
      ? 'bg-emerald-50 border-emerald-500 text-emerald-800'
      : 'bg-red-50 border-red-500 text-red-800';
    const icone = tipo === 'sucesso' ? 'check-circle' : 'alert-circle';
    area.innerHTML = `
      <div class="border-l-4 ${cores} p-3.5 rounded-r-xl shadow-sm flex items-start gap-2.5 text-xs font-medium">
        <i data-lucide="${icone}" class="w-4 h-4 mt-0.5 flex-shrink-0"></i>
        <span>${escapar(mensagem)}</span>
      </div>`;
    area.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
    area.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function limparAlerta() {
    const area = document.getElementById('area-alerta');
    if (area) { area.innerHTML = ''; area.classList.add('hidden'); }
  }

  // Mensagem que sobrevive a um redirecionamento (ex.: salvar -> voltar à lista)
  function definirFlash(mensagem) {
    sessionStorage.setItem(FLASH_KEY, mensagem);
  }

  function exibirFlash() {
    const msg = sessionStorage.getItem(FLASH_KEY);
    if (msg) {
      sessionStorage.removeItem(FLASH_KEY);
      alerta(msg, 'sucesso');
    }
  }

  // Logout comum a todas as páginas (também descarta a chave volátil do Gemini)
  document.addEventListener('DOMContentLoaded', () => {
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
      btnLogout.addEventListener('click', async () => {
        sessionStorage.removeItem('gemini_api_key');
        try {
          await fetch('/api/logout', { method: 'POST' });
        } finally {
          window.location.href = '/login';
        }
      });
    }
    exibirFlash();
    if (window.lucide) lucide.createIcons();
  });

  return {
    api, escapar, formatarDocumento, mascaraDocumento, formatarMoeda, formatarData,
    alerta, limparAlerta, definirFlash,
  };
})();
