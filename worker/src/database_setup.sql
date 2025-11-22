-- Tabela principal de Projetos
CREATE TABLE IF NOT EXISTS projetos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_externo INTEGER UNIQUE NOT NULL, -- ID da URL (ex: 56121)
    numero_processo TEXT, -- Ex: "05019/03"
    numero_projeto TEXT,  -- Ex: "314/25"
    tipo TEXT,            -- PLL, PLE, etc.
    ementa TEXT,
    data_abertura DATE,
    data_ultima_tramitacao DATETIME,
    situacao_tramitacao TEXT,
    situacao_plenaria TEXT,
    link_pdf_principal TEXT, -- URL do PDF baixado/analisado
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Autores (Nomes normalizados)
CREATE TABLE IF NOT EXISTS autores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    partido TEXT
);

-- Relacionamento Projeto <-> Autores (Muitos para Muitos)
CREATE TABLE IF NOT EXISTS projetos_autores (
    projeto_id INTEGER,
    autor_id INTEGER,
    PRIMARY KEY (projeto_id, autor_id),
    FOREIGN KEY(projeto_id) REFERENCES projetos(id),
    FOREIGN KEY(autor_id) REFERENCES autores(id)
);

-- Análise da IA (1 para 1 com Projeto)
CREATE TABLE IF NOT EXISTS analises_ia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id INTEGER UNIQUE NOT NULL,
    modelo_utilizado TEXT,
    titulo_simplificado TEXT,
    resumo_simples TEXT,
    data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(projeto_id) REFERENCES projetos(id)
);

-- Mudanças Práticas Identificadas (1 para N)
CREATE TABLE IF NOT EXISTS analise_mudancas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analise_id INTEGER NOT NULL,
    texto_simplificado TEXT NOT NULL,
    trechos_originais JSON NOT NULL, -- Lista de strings armazenada como JSON
    FOREIGN KEY(analise_id) REFERENCES analises_ia(id)
);

-- Justificativas do Autor (1 para N)
CREATE TABLE IF NOT EXISTS analise_justificativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analise_id INTEGER NOT NULL,
    texto_simplificado TEXT NOT NULL,
    trechos_originais JSON NOT NULL,
    FOREIGN KEY(analise_id) REFERENCES analises_ia(id)
);

-- Categorias/Tags (1 para N)
CREATE TABLE IF NOT EXISTS analise_categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analise_id INTEGER NOT NULL,
    nome_categoria TEXT NOT NULL, -- "Saúde", "Educação", etc.
    trechos_originais JSON NOT NULL,
    FOREIGN KEY(analise_id) REFERENCES analises_ia(id)
);