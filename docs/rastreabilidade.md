# Rastreabilidade: requisito → critério → caso de teste → teste automatizado

Fonte: plano da primeira entrega (casos CT-01 a CT-18, critérios CA-01 a CA-17).
A coluna "Teste automatizado" aponta onde o caso está implementado no código. A coluna
"Execução" é preenchida pela equipe em `docs/execucao-testes.md`.

| CT | CA | Requisitos | Nível | Onde está (automatizado) | Complemento manual |
|---|---|---|---|---|---|
| CT-01 | CA-01 | RF-01, RNF-07 | Sistema | `tests/system/test_login.py` | Prints do login válido e inválido |
| CT-02 | CA-02 | RF-01, RNF-06 | Sistema | `tests/system/test_acesso.py` | Print do 403 pela URL `/admin/` |
| CT-03 | CA-03 | RF-02, RF-03, RN-04 | Sistema | `tests/system/test_catalogo_e_progresso.py`, `tests/unit/test_cursos.py` | Print do catálogo e do bloqueio |
| CT-04 | CA-04 | RF-03 | Sistema | `tests/system/test_catalogo_e_progresso.py::test_progresso_de_2_de_4_atividades_e_50_por_cento` | Print do progresso de 50% |
| CT-05 | CA-05 | RF-05, RN-01 | Unidade e sistema | `tests/unit/test_avaliacao.py`, `tests/system/test_avaliacao_fluxo.py` | Prints dos resultados (A e B) |
| CT-06 | CA-06 | RF-06 | Sistema | `tests/system/test_avaliacao_fluxo.py::test_ct06_*` | Print da mensagem de bloqueio |
| CT-07 | CA-07 | RF-07 | Integração | `tests/integration/test_certificado.py::test_ct07_*` | Abrir o PDF e conferir os campos |
| CT-08 | CA-08 | RNF-02 | Sistema (desempenho) | `tests/integration/test_certificado.py::test_ct08_*` | Registrar condições do ambiente (A-04) |
| CT-09 | CA-09 | RN-02 | Integração | `tests/integration/test_certificado.py::test_ct09_*` | Print da emissão negada |
| CT-10 | CA-10 | RF-07, RN-03 | Integração | `tests/integration/test_certificado.py::test_ct10_*`, `tests/unit/test_certificado.py` | Saída do teste |
| CT-11 | CA-11 | RF-08 | Sistema | `tests/system/test_verificacao_publica.py::test_ct11_*` | Prints dos 3 cenários |
| CT-12 | CA-12 | RF-08, RN-03, RNF-07 | Sistema (segurança) | `tests/system/test_verificacao_publica.py::test_ct12_*` | Inspecionar a resposta no navegador (F12) |
| CT-13 | CA-13 | RF-09, RF-10, RN-05 | Integração | `tests/integration/test_certificado.py::test_ct13_*` | Print do histórico após arquivar |
| CT-14 | CA-14 | RNF-01 | Sistema (desempenho) | — (manual) | Relatório do Lighthouse |
| CT-15 | CA-15 | RNF-04, RNF-05 | Sistema | — (manual) | Teclado, 360 px e três navegadores |
| CT-16 | CA-16 | RNF-07 | Caixa-branca, inspeção | `tests/integration/test_certificado.py::test_ct16_*`, `tests/system/test_login.py` | Inspeção do banco (`instance/portal.db`) e do painel de eventos em `/admin/` |
| CT-17 | CA-05 | RF-05 | Unidade, caixa-branca | `tests/unit/test_avaliacao.py` | Relatório `pytest --cov` (≥ 80%) |
| CT-18 | CA-17 | RF-11, RF-12, RN-06 | Sistema | — (fora do escopo do protótipo) | Registrar como não executado, com o motivo |

## Segurança e qualidade (RNF-06, RNF-07, RNF-08)

| Tema | Onde está |
|---|---|
| Hash de senha, sem texto puro | `tests/system/test_login.py`, `tests/integration/test_certificado.py::test_ct16_nenhuma_senha_*` |
| Proteção CSRF | `tests/system/test_sessao_e_csrf.py`, `tests/system/test_fluxo_com_csrf.py` |
| Sessão (cookie, expiração, logout) | `tests/system/test_sessao_e_csrf.py`, `tests/system/test_login.py` |
| SQL injection e XSS | `tests/system/test_login.py`, `tests/system/test_verificacao_publica.py` |
| Controle de acesso por perfil e por dono | `tests/system/test_acesso.py`, `tests/integration/test_certificado.py` |
| Isolamento do banco de teste | `tests/integration/test_banco_e_seed.py` |
| Bloqueio de força bruta no login (D-02) | `tests/system/test_seguranca.py::test_d02_*` |
| Cabeçalhos de segurança (D-03) | `tests/system/test_seguranca.py::test_d03_*` |
| Análise estática | `ruff check .` e `bandit -r app` |
