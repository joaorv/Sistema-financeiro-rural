-- =====================================================================
-- Gestão-Contas-Rural - Esquema do banco PostgreSQL (Neon)
-- Baseado no diagrama do projeto. Execute no SQL Editor do Neon ou:
--   psql "$DATABASE_URL" -f db/schema.sql
-- Regras de negócio (não excluir, inativar/reativar) ficam na aplicação.
-- =====================================================================

CREATE TABLE IF NOT EXISTS pessoas (
  idpessoas    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tipo         VARCHAR(45)  NOT NULL,                  -- FORNECEDOR | CLIENTE | FATURADO
  razaosocial  VARCHAR(150) NOT NULL,
  fantasia     VARCHAR(150),
  documento    VARCHAR(45),                            -- CPF/CNPJ só com dígitos
  status       VARCHAR(45)  NOT NULL DEFAULT 'ATIVO'   -- ATIVO | INATIVO
);

CREATE TABLE IF NOT EXISTS classificacao (
  idclassificacao INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tipo            VARCHAR(45)  NOT NULL,               -- DESPESA | RECEITA
  descricao       VARCHAR(150) NOT NULL,               -- sempre em MAIÚSCULAS
  status          VARCHAR(45)  NOT NULL DEFAULT 'ATIVO'
);

CREATE TABLE IF NOT EXISTS movimentocontas (
  idmovimentocontas           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tipo                        VARCHAR(45)   NOT NULL,  -- APAGAR | ARECEBER
  numeronotafiscal            VARCHAR(45),
  dataemissao                 DATE,
  descricao                   VARCHAR(300),
  status                      VARCHAR(45)   NOT NULL DEFAULT 'ATIVO',
  valortotal                  NUMERIC(12,2) NOT NULL,
  pessoas_idfornecedorcliente INTEGER NOT NULL REFERENCES pessoas (idpessoas),
  pessoas_idfaturado          INTEGER          REFERENCES pessoas (idpessoas)
);

CREATE TABLE IF NOT EXISTS parcelascontas (
  idparcelascontas                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  identificacao                     VARCHAR(45)   NOT NULL,  -- ÚNICA | 1/3, 2/3...
  datavencimento                    DATE,
  valorparcela                      NUMERIC(12,2) NOT NULL,
  valorpago                         NUMERIC(12,2) NOT NULL DEFAULT 0,
  valorsaldo                        NUMERIC(12,2) NOT NULL,
  statusparcela                     VARCHAR(45)   NOT NULL DEFAULT 'ATIVO',
  movimentocontas_idmovimentocontas INTEGER NOT NULL REFERENCES movimentocontas (idmovimentocontas)
);

CREATE TABLE IF NOT EXISTS movimentocontas_has_classificacao (
  movimentocontas_idmovimentocontas INTEGER NOT NULL REFERENCES movimentocontas (idmovimentocontas),
  classificacao_idclassificacao     INTEGER NOT NULL REFERENCES classificacao (idclassificacao),
  PRIMARY KEY (movimentocontas_idmovimentocontas, classificacao_idclassificacao)
);
