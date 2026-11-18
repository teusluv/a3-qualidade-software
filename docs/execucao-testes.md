# Registro de execução de testes

Preencha uma linha por execução. Os campos "obtido", "status" e "evidência" vêm da execução real.

Campos obrigatórios (CA-16 / rastreabilidade): ID do caso, resultado esperado,
resultado obtido, status e evidência.

**Status permitidos:** Aprovado · Reprovado · Bloqueado · Não executado (com o motivo).

**Ambiente (execução 1):** sistema operacional **Linux x86_64 (contêiner, glibc 2.39)** ·
Python **3.13.18** · navegador **nenhum (sem navegador gráfico no ambiente; o fluxo de tela foi
exercitado por requisições HTTP reais contra o servidor Flask em 127.0.0.1:5000)** ·
data **18/11/2026** · versão do código **pacote `A3-entrega-completa.zip`, antes do primeiro
commit (sem hash de commit)**.

> **Desvio de ambiente a registrar:** o README indica Python 3.12 como versão testada. Esta
> execução usou **Python 3.13.18** e os 174 testes passaram, o que é evidência adicional de
> portabilidade. Ainda falta confirmar Windows, Python 3.11, Firefox e Edge (CT-15 / Portabilidade).

**Repositório:** https://github.com/teusluv/a3-qualidade-software (público) ·
**CI:** primeira execução verde em 18/11/2026 (CI #1, commit 8d1dd3c, 49 s, Python 3.12).

**Comandos executados:** `python seed.py` · `pytest` · `pytest -v` ·
`pytest --cov=app --cov-branch` · `pytest --cov=app.services.avaliacao --cov-branch` ·
`ruff check .` · `bandit -r app` · scripts de fluxo HTTP (saídas em `docs/evidencias/`).

**Resumo:** 174/174 testes automatizados aprovados em 6,3 s · ruff e bandit sem avisos ·
cobertura de ramos de 96% no pacote `app` e **100%** em `services/avaliacao.py` ·
15 de 18 casos aprovados · 1 fora do escopo (CT-18) · 2 parciais (CT-14, CT-15).

**Depois da bateria de segurança e das correções D-02 e D-03 (mesma data):** a suíte passou a
**205 testes**, todos aprovados; cobertura de ramos de **97%** no pacote `app` e 100% em
`services/avaliacao.py`; ruff e bandit continuam sem avisos. Ver `relatorio-seguranca.md`.

## Execução 1 (primeira entrega, 25/11/2026)

| ID | Tipo | Resultado esperado | Resultado obtido | Status | Evidência |
|---|---|---|---|---|---|
| CT-01 | Sistema | Válidas: acesso liberado. Inválidas: negado, com mensagem genérica. | 1001/colab123 → HTTP 200 redirecionado a `/cursos`. 1001/senha errada → HTTP 401 com "Matrícula ou senha inválidas", sem indicar qual campo errou. SQL injection no login não autentica. 14 testes de `test_login.py` aprovados. | Aprovado | `evidencias/CT-01-03-04-05-fluxo-http.txt`; `evidencias/execucao-completa-verbose.txt` |
| CT-02 | Sistema | Colaborador na URL de administração: acesso negado. | Colaborador em `/admin/` → **HTTP 403**, com registro `acesso_negado` no log. Administrador 9001 → HTTP 200. O link de administração não aparece para o colaborador. | Aprovado | `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt`; `evidencias/CT-16-banco-logs-e-hash.txt` |
| CT-05 | Unidade e sistema | A: 7 = 70% Aprovado; 6 = 60% Reprovado. B: 7 Reprovado; 8 Aprovado. | Curso A: 6 acertos → 60% Reprovado; 7 → 70% Aprovado; 8 → 80% Aprovado. Curso B (mínimo 80%): 7 → Reprovado; 8 → Aprovado. Limites 69/70/71 e 79/80/81 cobertos nos testes de unidade (63 testes). Nota truncada: 69,9% não vira 70%. Gabarito não aparece no HTML da avaliação. | Aprovado | `evidencias/CT-01-03-04-05-fluxo-http.txt`; `evidencias/execucao-completa-verbose.txt` |
| CT-06 | Sistema | Tentativa extra bloqueada; nota final 80% (notas 60, 80, 70). | Três tentativas gravadas com notas **60, 80, 70**; a 4ª foi bloqueada (não gerou nota nova) e o histórico passou a exibir **80%** como nota final. Consulta ao banco: "1001 curso A: 3 tentativas (notas 60,80,70), maior = 80". | Aprovado | `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt`; `evidencias/CT-16-banco-logs-e-hash.txt` |
| CT-07 | Integração | PDF com todos os campos preenchidos. | PDF de 2.087 bytes entregue em HTTP 200. Texto extraído contém os 6 campos: nome (Carla Mendes Lima), matrícula (1001), curso (Segurança do Paciente), carga horária (4 horas), data (18/11/2026) e código de autenticidade. | Aprovado | `evidencias/CT-07-certificado.pdf`; `evidencias/CT-07-pdf-campos.txt` |
| CT-08 | Desempenho | Pelo menos 19 de 20 emissões em até 5 s. | **20 de 20** emissões (emitir + gerar PDF) dentro de 5 s. Mínimo 3,1 ms · mediana 3,3 ms · máximo 4,5 ms. Pela rota HTTP, a emissão completa levou 6 ms. Vale a ressalva A-04: medição em ambiente local. | Aprovado | `evidencias/CT-08-tempo-emissao.txt`; `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt` |
| CT-09 | Integração | Emissão negada para reprovado e para atividades incompletas; nenhum PDF. | Usuário 1002 sem atividades concluídas e com atividades incompletas: emissão negada com a mensagem "Conclua todas as atividades do curso para emitir o certificado."; nenhum link de PDF no histórico; evento `emissao_negada` gravado no log. Os 3 testes `test_ct09_*` (reprovado, atividades incompletas, curso não iniciado) aprovados. | Aprovado | `evidencias/CT-09-11-12-fluxo-http.txt`; `evidencias/CT-16-banco-logs-e-hash.txt` |
| CT-10 | Integração | 100 códigos distintos. | 100 certificados emitidos, 100 códigos distintos (`test_ct10_cem_certificados_com_codigos_distintos` aprovado); códigos gerados por `secrets`, não sequenciais, com restrição `UNIQUE`. Exemplo real: `CsiG9AlTmYpyfHhSI79BjA`. | Aprovado | `evidencias/execucao-completa-verbose.txt`; `evidencias/CT-16-banco-logs-e-hash.txt` |
| CT-11 | Sistema | Autêntico; Certificado não encontrado; validação do campo vazio. | Código válido → HTTP 200 "Autêntico", com curso, carga horária, data e titular. Código inexistente → **HTTP 404** "Certificado não encontrado". Campo vazio → **HTTP 400** "Informe o código do certificado". A página abre sem login. | Aprovado | `evidencias/CT-09-11-12-fluxo-http.txt` |
| CT-12 | Segurança | Sem matrícula, CPF, e-mail ou senha; nome mascarado; entradas tratadas como texto. | A resposta pública não traz matrícula (1001), nome completo, CPF, e-mail nem senha. Titular exibido como **"Carla M. L."**. Entradas `<script>alert(1)</script>`, `' OR 1=1 --`, `../../etc/passwd` e `%27%20OR%201=1` → HTTP 400 (formato inválido), sem execução, sem eco e sem "Autêntico". 7 testes `test_ct12_*` aprovados. | Aprovado | `evidencias/CT-09-11-12-fluxo-http.txt` |
| CT-16 | Caixa-branca | Senhas em hash; um log por evento. | Senhas armazenadas com **scrypt** (`scrypt:32768:8:1$...`, 162 caracteres); busca por "colab123"/"admin123" em todas as tabelas: nenhuma ocorrência. Log com usuário, ação e data/hora para `login_sucesso`, `login_falha`, `curso_iniciado`, `inicio_bloqueado`, `atividade_concluida`, `avaliacao_realizada`, `certificado_emitido`, `emissao_negada`, `acesso_negado` e `curso_status_alterado`. A coluna `detalhe` não guarda o que foi digitado no login. | Aprovado | `evidencias/CT-16-banco-logs-e-hash.txt` |
| CT-17 | Unidade | Cobertura de decisão ≥ 80% em `services/avaliacao.py`; testes passam. | Cobertura de ramos de **100%** em `app/services/avaliacao.py` (39 comandos, 14 ramos, 0 não cobertos). No pacote `app` inteiro: **96%**. 174 testes aprovados. `ruff check .` → "All checks passed!"; `bandit -r app` → "No issues identified" (960 linhas analisadas, 0 avisos). | Aprovado | `evidencias/CT-17-cobertura-avaliacao.txt`; `evidencias/CT-17-cobertura-geral.txt`; `evidencias/estatica-ruff.txt`; `evidencias/estatica-bandit.txt` |

## Execução 2 (entrega final, 02/12/2026), incluindo regressão

| ID | Tipo | Resultado esperado | Resultado obtido | Status | Evidência |
|---|---|---|---|---|---|
| CT-03 | Sistema | Só cursos aplicáveis; obrigatórios identificados; início do suspenso bloqueado. | Colaborador de Enfermagem (1001) vê A (marcado como obrigatório), B (do seu setor) e C; o curso D (arquivado) não aparece no catálogo. No curso C (suspenso) o botão "Iniciar curso" vem `disabled` e o POST de início é recusado, com evento `inicio_bloqueado` no log. Curso de outro setor não abre nem pela URL. | Aprovado | `evidencias/CT-01-03-04-05-fluxo-http.txt`; `evidencias/execucao-completa-verbose.txt` |
| CT-04 | Sistema | Progresso de 50% com 2 de 4 atividades. | Progresso medido a cada conclusão: 25% → **50%** → 75% → 100%. | Aprovado | `evidencias/CT-01-03-04-05-fluxo-http.txt` |
| CT-13 | Integração | Conclusões continuam visíveis após arquivar o curso. | Administrador alterou o curso A para "arquivado"; o histórico do colaborador continuou mostrando o curso, a nota e o link do certificado. Teste `test_ct13_arquivar_curso_mantem_historico_e_certificado` aprovado. Situação devolvida para "ativo" ao final. | Aprovado | `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt`; `evidencias/execucao-completa-verbose.txt` |
| CT-14 | Desempenho | Páginas principais em até 3 s (Lighthouse). | **Parcial.** Sem navegador no ambiente, não houve Lighthouse. Medição do tempo de resposta do servidor (5 requisições por página): `/login` 1,2 ms · `/verificar` 1,3 ms · `/cursos` 1,4 ms · `/cursos/1` 1,5 ms · `/historico` 1,4 ms · `/admin/` 1,5 ms (máximo 2,8 ms). Falta a medição de carregamento no navegador, que inclui o CSS vindo do CDN. | Não executado (falta Lighthouse; servidor medido, ver obtido) | `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt` |
| CT-15 | Acessibilidade | Fluxo só com teclado, em 360 px e em três navegadores. | **Parcial.** Sem navegador no ambiente. Checagem estática em 8 páginas (login, verificar, catálogo, curso, avaliação, histórico, administração e 404): **0 problemas** — todas com `lang`, `meta viewport`, `<title>`, `<h1>`, todo campo com rótulo (`label for` ou `legend` no grupo de rádio), nenhuma imagem sem `alt`, nenhum `tabindex` positivo, nenhum link ou botão sem texto. O CSS próprio usa só `max-width` (860 px e 420 px), sem largura fixa que force rolagem a 360 px. Faltam: navegação só por teclado, 360 px real e Firefox/Edge. | Não executado (falta teclado, 360 px real e 3 navegadores) | `evidencias/CT-15-acessibilidade-estatica.txt` |
| CT-18 | Sistema | **Não executado:** RF-11 e RF-12 estão fora do escopo do protótipo. | Não se aplica | Não executado | Plano, item de escopo |
| Regressão | Todos | Reexecutar os casos de prioridade alta e os afetados por correções. | Nenhum defeito funcional foi encontrado nos CT-01 a CT-17. Depois das correções de segurança **D-02** (força bruta no login) e **D-03** (cabeçalhos), a suíte completa foi reexecutada: **205/205 aprovados**, sem nenhuma quebra nos 174 testes anteriores. A bateria OWASP foi reexecutada e passou de 73/81 para **80/83**. O fluxo manual foi repetido em banco recém-semeado, com o mesmo resultado. | Aprovado | `evidencias/REG-regressao-apos-correcao.txt`; `evidencias/SEG-owasp-top10-apos-correcao.txt` |
| Segurança (extra) | OWASP Top 10 | Sem falha de autenticação, acesso, injeção ou adulteração. | 83 verificações, 80 aprovadas. Nenhuma falha de lógica. Os 3 alertas restantes dependem de HTTPS (cookie `Secure`, HSTS) ou do servidor de produção (cabeçalho `Server`). | Aprovado | `relatorio-seguranca.md`; `evidencias/SEG-owasp-top10-apos-correcao.txt` |

## Como gerar as evidências automatizadas

```bash
pytest -v                                    # lista cada teste e o resultado
pytest --cov=app --cov-branch --cov-report=term-missing
pytest --cov=app.services.avaliacao --cov-branch --cov-report=term-missing   # CT-17
ruff check .
bandit -r app
```

Salve a saída (print ou `> arquivo.txt`) em `docs/evidencias/`, com nome começando pelo ID do
caso (ex.: `CT-17-cobertura.txt`).

## O que ainda depende da equipe

1. **CT-14:** rodar o Lighthouse nas páginas principais e anexar o relatório.
2. **CT-15:** percorrer o fluxo só com Tab/Enter, abrir a 360 px e repetir em Chrome, Firefox e Edge.
3. **Portabilidade:** confirmar em Windows e Python 3.11/3.12 (aqui foi Linux e Python 3.13).
4. **CI:** subir no GitHub e registrar a primeira execução verde na aba Actions.
