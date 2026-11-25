-- Esquema do banco (SQLite). Pode ser executado várias vezes sem duplicar tabelas.
PRAGMA foreign_keys = ON;

-- Cadastro de colaboradores (simula a base do RH).
CREATE TABLE IF NOT EXISTS usuario (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula   TEXT NOT NULL UNIQUE,
    nome        TEXT NOT NULL,
    senha_hash  TEXT NOT NULL,
    perfil      TEXT NOT NULL CHECK (perfil IN ('colaborador', 'administrador')),
    setor       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS curso (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT NOT NULL UNIQUE,
    titulo        TEXT NOT NULL,
    carga_horaria INTEGER NOT NULL CHECK (carga_horaria > 0),
    nota_minima   INTEGER NOT NULL CHECK (nota_minima BETWEEN 70 AND 100),  -- RN-01
    obrigatorio   INTEGER NOT NULL DEFAULT 0 CHECK (obrigatorio IN (0, 1)),
    setor         TEXT,                       -- NULL = todos os setores
    status        TEXT NOT NULL CHECK (status IN ('ativo', 'suspenso', 'arquivado')),
    data_inicio   TEXT NOT NULL,              -- AAAA-MM-DD
    data_fim      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS atividade (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id  INTEGER NOT NULL REFERENCES curso(id),
    ordem     INTEGER NOT NULL,
    titulo    TEXT NOT NULL,
    UNIQUE (curso_id, ordem)
);

CREATE TABLE IF NOT EXISTS questao (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id   INTEGER NOT NULL REFERENCES curso(id),
    ordem      INTEGER NOT NULL,
    enunciado  TEXT NOT NULL,
    opcao_a    TEXT NOT NULL,
    opcao_b    TEXT NOT NULL,
    opcao_c    TEXT NOT NULL,
    opcao_d    TEXT NOT NULL,
    correta    TEXT NOT NULL CHECK (correta IN ('a', 'b', 'c', 'd')),
    UNIQUE (curso_id, ordem)
);

-- Registro de início do curso (A-08: quem iniciou pode concluir).
CREATE TABLE IF NOT EXISTS inscricao (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuario(id),
    curso_id    INTEGER NOT NULL REFERENCES curso(id),
    iniciado_em TEXT NOT NULL,
    UNIQUE (usuario_id, curso_id)
);

CREATE TABLE IF NOT EXISTS progresso (
    inscricao_id  INTEGER NOT NULL REFERENCES inscricao(id),
    atividade_id  INTEGER NOT NULL REFERENCES atividade(id),
    concluida_em  TEXT NOT NULL,
    PRIMARY KEY (inscricao_id, atividade_id)
);

CREATE TABLE IF NOT EXISTS tentativa (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    inscricao_id  INTEGER NOT NULL REFERENCES inscricao(id),
    acertos       INTEGER NOT NULL,
    total         INTEGER NOT NULL,
    nota          INTEGER NOT NULL CHECK (nota BETWEEN 0 AND 100),  -- percentual
    realizada_em  TEXT NOT NULL
);

-- Emissão única por colaborador e curso (A-07); código imprevisível e exclusivo (RN-03).
CREATE TABLE IF NOT EXISTS certificado (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuario(id),
    curso_id    INTEGER NOT NULL REFERENCES curso(id),
    codigo        TEXT NOT NULL UNIQUE,
    concluido_em  TEXT NOT NULL,              -- data da primeira tentativa aprovada
    emitido_em    TEXT NOT NULL,
    UNIQUE (usuario_id, curso_id)
);

-- Trilha de auditoria (CA-16). Nunca guarda senha nem dados pessoais.
CREATE TABLE IF NOT EXISTS log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER REFERENCES usuario(id),
    acao        TEXT NOT NULL,
    detalhe     TEXT,
    criado_em   TEXT NOT NULL
);

-- Arquivos anexados pelo administrador a um curso (material de estudo).
CREATE TABLE IF NOT EXISTS material (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id       INTEGER NOT NULL REFERENCES curso(id),
    nome_original  TEXT NOT NULL,
    arquivo        TEXT NOT NULL UNIQUE,      -- nome gerado no disco (nunca o nome enviado)
    tamanho        INTEGER NOT NULL,
    enviado_por    INTEGER REFERENCES usuario(id),
    enviado_em     TEXT NOT NULL
);
