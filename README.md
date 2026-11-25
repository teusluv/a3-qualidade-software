# Portal de Treinamentos e Certificados — Protótipo A3

Protótipo da disciplina **Garantia da Qualidade de Software** (UNIFACS), projeto A3.
Cenário: **Hospital da Mulher**, em Feira de Santana. Todos os dados são **fictícios**.

**Equipe 2:** Alan Souza Sampaio · Felipe Augusto Mendes Evangelista · Guilherme da Silva Melo ·
José Mateus Santos Nunes · Marcos Messias Menezes de Almeida
**Orientadores:** Prof. Jairo Luciano Rêgo e Prof. Victor Moak

---

## 1. O que é este projeto (em 1 minuto)

Um site em que o colaborador do hospital faz um treinamento obrigatório, é avaliado e recebe,
**na hora**, um certificado em PDF com um código que qualquer pessoa pode conferir. Hoje esse
certificado leva de 15 a 30 dias; a meta do projeto (M-01) é emitir em até 5 segundos.

```
login → catálogo de cursos → inicia o curso → conclui as atividades
      → faz a avaliação (10 questões) → nota e resultado (aprovado ou reprovado)
      → se aprovado: certificado em PDF com código único
      → qualquer pessoa confere o código em "Verificar certificado" (sem login)
```

**Para a disciplina, o foco não é só o software:** é mostrar como o software foi **verificado e
validado** (testes, inspeção, análise estática, defeitos, regressão e CI). Por isso o projeto
traz o código, os testes automatizados e os documentos para a equipe registrar o que executar.

---

## 2. Começo rápido

Você precisa do **Python 3.12** (versão em que foi testado) e do **Git** (opcional, para o GitHub).

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python seed.py                   # cria o banco com dados fictícios (pode repetir)
pytest                           # roda os 260 testes (leva alguns segundos)
flask --app app run --debug      # abre em http://127.0.0.1:5000
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
pytest
flask --app app run --debug
```

Para sair do ambiente virtual: `deactivate`.

### Usuários de demonstração

| Perfil | Matrícula | Senha | Setor |
|---|---|---|---|
| Colaborador | 1001 | colab123 | Enfermagem |
| Colaborador | 1002 | colab123 | Farmácia |
| Administrador | 9001 | admin123 | TI |

### Cursos de demonstração

| Curso | Nota mínima | Situação | Quem vê |
|---|---|---|---|
| A: Segurança do Paciente | 70% | Ativo, **obrigatório** | Todos |
| B: Higienização das Mãos e Controle de Infecção | 80% | Ativo | Só Enfermagem |
| C: Biossegurança em Laboratório | 70% | **Suspenso** (não aceita novos inícios) | Todos |
| D: Protocolo Antigo de Triagem | 70% | **Arquivado** (só aparece no histórico) | Quem já fez |

### Roteiro de demonstração (5 minutos)

1. Entre como **1001 / colab123**. O catálogo mostra A (obrigatório), B e C (suspenso).
2. Abra o curso **C**: o botão "Iniciar curso" está desabilitado (critério CA-03).
3. Abra o curso **A**, inicie e conclua as 4 atividades (o progresso sobe: 25%, 50%...).
4. Faça a avaliação. Com 7 acertos: 70%, **Aprovado**. Com 6: 60%, **Reprovado**.
5. Aprovado? Clique em **Emitir / baixar certificado**: o PDF traz nome, matrícula, curso,
   carga horária, data e código.
6. Abra **Verificar certificado** (menu), cole o código: "Autêntico", com o nome mascarado.
7. Entre como **9001 / admin123** e abra **Administração**: cadastre um curso novo, **anexe um
   material** (PDF, Word, PowerPoint, texto ou imagem, até 20 MB), altere a situação de um curso e
   veja os eventos registrados. Depois entre como colaborador, inicie o curso novo e baixe o material.
   Como colaborador, abrir `/admin/` dá "Acesso negado" (CA-02).

---

## 3. O que o sistema faz

### Telas (T-01 a T-05 do plano)

| Tela | Endereço | Quem acessa |
|---|---|---|
| T-01 Login | `/login` | Todos |
| T-02 Catálogo | `/cursos` (a raiz `/` leva para ele) | Logado |
| T-03 Curso e atividades | `/cursos/<id>` | Logado |
| T-04 Avaliação e resultado | `/cursos/<id>/avaliacao` e `/cursos/<id>/resultado/<id>` | Logado |
| T-05 Verificação pública | `/verificar` | **Qualquer pessoa, sem login** |
| Histórico | `/historico` | Logado |
| Administração (cadastro de curso, anexo de material, situação dos cursos, eventos) | `/admin/` | Só administrador |

Outros endereços: `POST /cursos/<id>/iniciar`, `POST /cursos/<id>/atividades/<id>/concluir`,
`POST /cursos/<id>/certificado`, `GET /certificados/<id>/pdf`, `GET /cursos/<id>/materiais/<id>`
(download do material), `POST /logout`, `POST /admin/cursos` (cadastrar curso),
`POST /admin/cursos/<id>/status`, `POST /admin/cursos/<id>/materiais` (anexar) e
`POST /admin/materiais/<id>/remover`.

### Regras de negócio adotadas

| Regra | O que significa |
|---|---|
| RN-01 | Aprovação exige no mínimo 70%; o curso pode exigir mais (o B exige 80%), nunca menos. A nota "igual ao mínimo" aprova. A nota é **truncada**: 69,9% não vira 70% |
| RN-02 | O certificado só sai com atividades concluídas **e** nota suficiente, validado no servidor |
| RN-03 | Código único, gerado com `secrets` e protegido por restrição `UNIQUE`. A consulta pública mostra só o mínimo, com o nome parcialmente mascarado ("Carla M. L.") |
| RN-04 | Curso obrigatório vale para todos; os demais, por setor |
| RN-05 | Arquivar um curso não apaga o histórico de quem o concluiu |

### Hipóteses de trabalho (ambiguidades do plano, A-01 a A-08)

Estão em `app/config.py` ou no código, e podem mudar sem refazer a lógica.

| ID | Hipótese |
|---|---|
| A-01 | Aviso de vencimento **não** é implementado (RF-12 fora do escopo) |
| A-02 | Até **3 tentativas** por colaborador e curso; prevalece a **maior nota** |
| A-03 | Assinatura em imagem fictícia no PDF (o QR code é opcional e não foi feito) |
| A-04 | Os 5 s do certificado são medidos no **ambiente local**, em uso normal |
| A-05 | A consulta pública mostra curso, carga horária, data e nome mascarado |
| A-06 | A avaliação só abre com 100% das atividades concluídas |
| A-07 | O limite de 3 tentativas vale no total, **mesmo após aprovação**; o certificado é emitido **uma única vez** por colaborador e curso |
| A-08 | Se o período do curso (ou a suspensão) vem depois que a pessoa iniciou, ela **pode concluir**; só **novos inícios** são bloqueados |

### Fora do escopo do protótipo

Gestor, relatórios e aviso de vencimento (RF-11, RF-12, caso CT-18); edição das questões pela
interface (todo curso novo recebe 4 atividades e 10 questões-modelo); integração real com RH/PEP; teste de carga com 500
acessos (RNF-01) e medição de disponibilidade (RNF-03).

---

## 4. Como funciona por dentro

### Tecnologias

| Uso | Ferramenta |
|---|---|
| Linguagem | Python 3.12 |
| Web | Flask, Flask-WTF (proteção CSRF) |
| Interface | HTML, CSS, Bootstrap 5 (via CDN, com hash de integridade) e Jinja2 |
| Banco | SQLite (módulo `sqlite3` da biblioteca padrão) |
| PDF | reportlab (e pypdf, só nos testes, para ler o PDF gerado) |
| Testes | pytest, pytest-cov |
| Qualidade | ruff (estilo e erros), bandit (segurança) |
| CI | GitHub Actions |

### Estrutura de pastas

```
portal/
├── app/
│   ├── __init__.py          # create_app(): monta a aplicação (application factory)
│   ├── config.py            # constantes de negócio (nota mínima, tentativas...) e de sessão
│   ├── db.py                # conexão com o banco e criação das tabelas
│   ├── schema.sql           # as tabelas
│   ├── seed_data.py         # dados fictícios (usado pelo seed.py e pelos testes)
│   ├── auth.py              # login, logout e controle de acesso por perfil
│   ├── routes/              # o que cada endereço faz (recebe o pedido e responde)
│   │   ├── cursos.py        #   catálogo, curso, atividades, avaliação, resultado, histórico
│   │   ├── certificados.py  #   emissão, PDF e verificação pública
│   │   └── admin.py         #   cadastro de curso, anexo de material, situação dos cursos, eventos
│   ├── services/            # regras de negócio (sem Flask: fáceis de testar)
│   │   ├── avaliacao.py     #   nota, aprovação, tentativas (funções puras)
│   │   ├── cursos.py        #   consultas de catálogo, inscrição, progresso, tentativas
│   │   ├── certificado.py   #   emissão única, código, PDF, consulta pública
│   │   ├── cadastro.py      #   validação e criação de curso novo
│   │   ├── materiais.py     #   upload seguro do material (extensão, assinatura, nome gerado)
│   │   └── logs.py          #   registro de eventos
│   ├── templates/           # as páginas HTML
│   └── static/              # CSS (e pastas para js/ e img/)
├── tests/
│   ├── conftest.py          # preparação compartilhada (banco temporário por teste)
│   ├── unit/                # testes de unidade (caixa-branca)
│   ├── integration/         # componentes juntos (serviço + banco + PDF)
│   └── system/              # fluxo completo pelas rotas (caixa-preta)
├── docs/                    # documentos (veja a seção 6)
├── .github/workflows/ci.yml # pipeline de integração contínua
├── seed.py                  # cria o banco e carrega os dados fictícios
├── requirements.txt         # dependências com versão fixada
├── pytest.ini               # configuração dos testes
├── ruff.toml                # configuração da análise estática
└── README.md
```

### O caminho de um pedido (exemplo: emitir o certificado)

1. O navegador envia `POST /cursos/1/certificado`.
2. `auth.py` identifica o usuário pela sessão; `routes/certificados.py` recebe o pedido.
3. `services/certificado.py` abre **uma transação**, confere (no servidor) se as atividades estão
   completas e se a nota é suficiente, gera um código com `secrets` e grava o certificado e o log.
4. A rota devolve o PDF (`gerar_pdf`). Um pedido repetido devolve o **mesmo** certificado.

### Princípios usados

- **Regra de negócio fora das rotas:** `services/` não conhece o Flask, então se testa direto.
- **Application factory:** `create_app()` cria uma aplicação limpa a cada teste.
- **Configuração em um só lugar:** nenhum "70" ou "3" espalhado pelo código.
- **SQL sempre parametrizado** e **escape automático** do Jinja (contra SQL injection e XSS).
- **Segurança no servidor:** perfil verificado em toda rota restrita; senhas com hash;
  CSRF nos formulários; cookie de sessão `HttpOnly` e `SameSite`, com expiração de 30 minutos.
- **Gravações críticas atômicas:** emitir certificado e registrar tentativa usam transação
  (`BEGIN IMMEDIATE`), então pedidos simultâneos não geram duplicidade nem passam do limite.
- **Logs sem dados pessoais:** só usuário, ação e data/hora; nunca senha.

---

## 5. Testes e qualidade

```powershell
pytest                                                    # todos os testes
pytest -v                                                 # lista cada teste e o resultado
pytest --cov=app --cov-branch --cov-report=term-missing   # cobertura de ramos
pytest --cov=app.services.avaliacao --cov-branch --cov-report=term-missing   # meta do CT-17
ruff check .                                              # análise estática (estilo e erros)
bandit -r app                                             # análise estática (segurança)
```

| Pasta de testes | O que verifica | Casos do plano |
|---|---|---|
| `tests/unit/` | Nota, aprovação, tentativas, máscara do nome, regra de novo início | CT-05, CT-10, CT-17 |
| `tests/integration/` | Certificado (PDF, único, simultâneo), 100 códigos, logs, histórico, banco | CT-07 a CT-10, CT-13, CT-16 |
| `tests/system/` | Login, acesso, catálogo, avaliação, verificação pública, admin (cadastro e anexo), navegação, CSRF | CT-01 a CT-06, CT-11, CT-12 |

**Meta de cobertura:** 80% de cobertura de ramos em `app/services/avaliacao.py`. Hoje está em
100%. `--cov-branch` mede ramos, que usamos como indicador da cobertura de decisão do plano; ele
não prova, sozinho, que todas as combinações de condições foram exercitadas, por isso os valores
limite (69/70/71 e 79/80/81) têm testes escritos à mão.

**Isolamento:** nenhum teste usa o banco do protótipo (`instance/portal.db`). Cada teste recebe uma
**cópia nova** de um banco temporário.

**Casos que dependem de vocês (manuais):** CT-14 (Lighthouse) e CT-15 (teclado, 360 px e três
navegadores). O CT-18 está fora do escopo.

### Integração contínua

O arquivo `.github/workflows/ci.yml` roda a cada push na `main` e a cada pull request: instala
as dependências, roda `ruff`, `bandit`, `pytest` com cobertura e confere a meta de 80%. Só
funciona depois de o projeto estar no GitHub; confirmem a primeira execução na aba **Actions**.

---

## 6. Mapa da documentação (pasta `docs/`)

Cada documento existe em Markdown (`.md`), em Word (`docs/word/`) e em PDF (`docs/pdf/`). Para editar, use o Word; o `.md` serve para ler no GitHub.

| Documento | Para que serve | Quem preenche |
|---|---|---|
| `rastreabilidade.md` | Liga requisito → critério → caso de teste → teste automatizado | Pronto |
| `execucao-testes.md` | **Registro** de cada execução: esperado, obtido, status, evidência | **Equipe** |
| `defeitos.md` | **Registro** de defeitos reais, com evidência e classificação | **Equipe** |
| `inspecao.md` | Checklist da inspeção, tabela de achados, análise estática, limitações conhecidas | **Equipe** |
| `revisao-de-codigo.md` | 21 pontos de melhoria apontados numa revisão técnica (abertos, para a equipe avaliar) | Pronto; a equipe decide o que vira defeito |
| `avaliacao-criterios.md` | Avaliação de CA-01 a CA-17 e dos 7 atributos de qualidade (entrega final) | **Equipe** |
| `divisao-de-tarefas.md` | Quem faz o quê e o cronograma até 25/11 e 02/12 | Pronto; ajustem os nomes |
| `ci-cd.md` | Proposta de CI/CD para o relatório | Pronto; a equipe revisa |
| `verificacao-do-autor.md` | O que foi (e o que **não** foi) verificado antes da entrega | Pronto |
| `referencia-interface/` | Capturas de como as telas ficaram, para comparar | Pronto |
| `apresentacao/A3-apresentacao.pptx` | Slides (7) para a apresentação; os slides 5, 6 e 7 têm campos em laranja para a equipe preencher | **Equipe** |
| `evidencias/` | Pasta para prints e saídas de comandos da equipe | **Equipe** |

**Importante:** nada nos documentos de registro foi pré-preenchido com resultado. Eles só têm
valor se contarem o que **vocês** executaram de verdade.

---

## 7. Plano de trabalho

Entrega 1 (25/11/2026): primeira versão funcional, revisão e inspeção, defeitos com evidências,
análise estática, primeira execução de testes de caixa-preta e caixa-branca.
Entrega final (02/12/2026): execução documentada, resultados, defeitos classificados, correções e
regressão, avaliação de critérios e atributos, proposta de CI/CD.

Resumo do caminho (detalhes e responsáveis em `docs/divisao-de-tarefas.md`):

1. **17 e 18/11:** cada um roda o projeto; subir no GitHub e ver o CI verde.
2. **19 a 24/11:** executar os testes, inspecionar, registrar defeitos com evidência.
3. **25/11:** entrega 1.
4. **26/11 a 1/12:** corrigir, rodar a regressão, avaliar critérios e atributos, preparar a apresentação.
5. **2/12:** entrega final.

---

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Activate.ps1` não pode ser carregado (PowerShell) | A política de execução bloqueia scripts | Rode `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e tente de novo |
| `python` não é reconhecido | Python fora do PATH | Use `py -3.12 -m venv .venv`, ou reinstale marcando "Add to PATH" |
| Aviso "Banco sem usuários. Rode: python seed.py" | O seed não foi executado | Rode `python seed.py` |
| Erro "Banco de dados desatualizado" | Banco criado por uma versão antiga | Apague a pasta `instance` e rode `python seed.py` |
| Login diz "Matrícula ou senha inválidas" | Seed não rodou ou senha errada | Confira a tabela de usuários e rode `python seed.py` |
| Página sem estilo (tudo "cru") | Sem internet: o Bootstrap vem de CDN | Conecte à internet (ou baixe o Bootstrap para `app/static/`) |
| `Address already in use` | A porta 5000 está ocupada | `flask --app app run --port 5001` |
| `pytest` não encontrado | Ambiente virtual desativado | Ative o `.venv` e rode `pip install -r requirements.txt` |
| Anexo recusado: "Tipo de arquivo não permitido" ou "conteúdo não corresponde" | Só entram pdf, docx, pptx, txt, png, jpg e jpeg, e o conteúdo precisa ser do tipo da extensão | Use um arquivo real desses tipos, com até 20 MB |
| Quer recomeçar do zero | Dados bagunçados na demonstração | Apague `instance/` e rode `python seed.py` |

---

## 9. Limitações conhecidas

- Sem bloqueio de tentativas de login e sem cabeçalhos de segurança (ver `docs/revisao-de-codigo.md`).
- As "atividades" apenas são marcadas como concluídas; o material de estudo pode ser anexado, mas o
  sistema não confere se foi lido.
- Os arquivos anexados ficam na pasta local `instance/uploads`; o upload confere extensão e assinatura
  do arquivo, mas não faz varredura de vírus.
- O PDF não tem QR code; a assinatura é ilustrativa.
- O cookie `Secure` fica desligado no uso local em HTTP (ligue com `SESSION_COOKIE_SECURE=1` em HTTPS).
- O SQLite serve ao protótipo, mas não valida 500 acessos simultâneos nem a disponibilidade de 99,5%.
- Verificado apenas no Chromium, em Python 3.12 e Linux; Windows, Firefox, Edge e Python 3.11
  ficam para a equipe confirmar.

---

## 10. Glossário

| Sigla | Significa |
|---|---|
| RF | Requisito funcional (o que o sistema faz) |
| RNF | Requisito não funcional (desempenho, segurança, acessibilidade...) |
| RN | Regra de negócio |
| CA | Critério de aceitação (condição para dar o requisito como atendido) |
| CT | Caso de teste |
| A-0x | Hipótese de trabalho para uma ambiguidade do plano |
| M-0x | Meta do projeto (M-01: certificado em até 5 s; M-02: conformidade nos registros) |
| Caixa-preta | Testa pela interface, sem olhar o código |
| Caixa-branca | Testa olhando o código (cobertura de ramos) |
| Regressão | Repetir testes depois de uma correção, para ver se nada quebrou |
| CI/CD | Integração e entrega contínuas: verificações automáticas a cada alteração |

## 11. Convenções

- **Código:** PEP 8, verificado pelo `ruff`; nomes em português para o domínio (`nota`,
  `tentativa`) e em inglês para termos técnicos.
- **Commits:** mensagens curtas no imperativo (`Adiciona cálculo de nota`).
- **Branches:** `nome/tarefa`; integração por pull request, com revisão de outro integrante.
- **Defeitos:** em `docs/defeitos.md`, com ID, passos, esperado × obtido, evidência e severidade.
- **Testes não executados:** registrar como "Não executado", com o motivo; nunca omitir.
- **Desempenho:** a medição dos 5 s vale para o ambiente local e não comprova desempenho em
  produção; o relatório final repete essa ressalva.
