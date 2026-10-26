-- =====================================================================
-- Gestão-Contas-Rural - Classificações padrão (executar após schema.sql)
-- DESPESA: mesmas categorias usadas pelo prompt do Gemini.
-- Seguro para rodar mais de uma vez (não duplica).
-- =====================================================================

INSERT INTO classificacao (tipo, descricao)
SELECT v.tipo, v.descricao
FROM (VALUES
  ('DESPESA', 'INSUMOS AGRÍCOLAS'),
  ('DESPESA', 'MANUTENÇÃO E OPERAÇÃO'),
  ('DESPESA', 'RECURSOS HUMANOS'),
  ('DESPESA', 'SERVIÇOS OPERACIONAIS'),
  ('DESPESA', 'INFRAESTRUTURA E UTILIDADES'),
  ('DESPESA', 'ADMINISTRATIVAS'),
  ('DESPESA', 'SEGUROS E PROTEÇÃO'),
  ('DESPESA', 'IMPOSTOS E TAXAS'),
  ('DESPESA', 'INVESTIMENTOS'),
  ('DESPESA', 'OUTRAS DESPESAS'),
  ('RECEITA', 'VENDA DE GRÃOS'),
  ('RECEITA', 'VENDA DE GADO'),
  ('RECEITA', 'PRESTAÇÃO DE SERVIÇOS'),
  ('RECEITA', 'ARRENDAMENTO RECEBIDO'),
  ('RECEITA', 'OUTRAS RECEITAS')
) AS v (tipo, descricao)
WHERE NOT EXISTS (
  SELECT 1 FROM classificacao c WHERE c.tipo = v.tipo AND c.descricao = v.descricao
);
