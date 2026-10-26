/**
 * Formulário genérico de inclusão/edição.
 *  - Inclusão: POST (o backend grava STATUS = ATIVO; o campo não aparece na tela).
 *  - Edição: PUT (o STATUS fica oculto e não é alterado).
 *
 * Cada página define window.FORM = {
 *   endpoint, rotaLista, registroId, nome,
 *   preencher?(dados, form)  -> preenche campos especiais na edição
 *   montar?(form)            -> retorna o JSON a enviar (padrão: campos com name)
 *   aoIniciar?(form)         -> ganchos extras (máscaras, carregar selects...)
 * }
 */
document.addEventListener('DOMContentLoaded', async () => {
  const cfg = window.FORM;
  const form = document.getElementById('form-cadastro');
  const btnSalvar = document.getElementById('btn-salvar');

  function montarPadrao() {
    const dados = {};
    form.querySelectorAll('[name]').forEach(el => {
      const v = el.value.trim();
      dados[el.name] = v === '' ? null : v;
    });
    return dados;
  }

  function preencherPadrao(dados) {
    form.querySelectorAll('[name]').forEach(el => {
      if (dados[el.name] !== undefined && dados[el.name] !== null) el.value = dados[el.name];
    });
  }

  try {
    if (cfg.aoIniciar) await cfg.aoIniciar(form);
    if (cfg.registroId) {
      const dados = await Comum.api(`${cfg.endpoint}/${cfg.registroId}`);
      if (dados.status === 'INATIVO') {
        Comum.alerta('Este registro está INATIVO. Reative-o na listagem para poder editá-lo.', 'erro');
        btnSalvar.disabled = true;
      }
      await (cfg.preencher || preencherPadrao)(dados, form);
    }
  } catch (err) {
    Comum.alerta(err.message, 'erro');
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    Comum.limparAlerta();
    btnSalvar.disabled = true;
    try {
      const corpo = cfg.montar ? cfg.montar(form) : montarPadrao();
      const salvo = await Comum.api(
        cfg.registroId ? `${cfg.endpoint}/${cfg.registroId}` : cfg.endpoint,
        { method: cfg.registroId ? 'PUT' : 'POST', body: corpo }
      );
      Comum.definirFlash(cfg.registroId
        ? `${cfg.nome} ID ${salvo.id} atualizado(a) com sucesso.`
        : `${cfg.nome} cadastrado(a) com sucesso! ID ${salvo.id}.`);
      window.location.href = cfg.rotaLista;
    } catch (err) {
      Comum.alerta(err.message, 'erro');
      btnSalvar.disabled = false;
    }
  });
});
