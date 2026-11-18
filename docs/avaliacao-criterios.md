# Avaliação dos critérios de aceitação e dos atributos de qualidade

Item da **entrega final (02/12/2026)**: "avaliação de critérios de aceitação e atributos".

**Como usar:** a coluna "Base técnica" diz o que já existe no código e nos testes (fatos).
As colunas **Situação** e **Evidência** são da equipe e só devem ser preenchidas depois de
executar o caso correspondente (`docs/execucao-testes.md`).

**Situação permitida:** Atendido · Atendido em parte · Não atendido · Não avaliado (com o motivo).

## 1. Critérios de aceitação (CA-01 a CA-17)

| CA | Critério (resumo) | Casos | Base técnica (o que existe) | Situação | Evidência |
|---|---|---|---|---|---|
| CA-01 | Login válido libera; inválido ou vazio nega, sem dizer qual campo errou | CT-01 | `auth.py`; `tests/system/test_login.py` | Atendido | CT-01 aprovado: 401 com mensagem genérica, 14 testes de login · `evidencias/CT-01-03-04-05-fluxo-http.txt` |
| CA-02 | Colaborador não acessa a administração, nem pela URL | CT-02 | `perfil_required`; `tests/system/test_acesso.py` | Atendido | CT-02 aprovado: HTTP 403 pela URL, com `acesso_negado` no log · `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt` |
| CA-03 | Catálogo por setor, obrigatórios marcados; suspenso/fora do período não inicia | CT-03 | `routes/cursos.py`; `test_catalogo_e_progresso.py` | Atendido | CT-03 aprovado: botão `disabled` e POST recusado no curso suspenso · `evidencias/CT-01-03-04-05-fluxo-http.txt` |
| CA-04 | Progresso correto (2 de 4 = 50%) | CT-04 | `avaliacao.progresso_percentual`; testes de progresso | Atendido | CT-04 aprovado: 25% → 50% → 75% → 100% · `evidencias/CT-01-03-04-05-fluxo-http.txt` |
| CA-05 | Curso A: 7 aprova, 6 reprova. Curso B: 7 reprova, 8 aprova | CT-05, CT-17 | `services/avaliacao.py`; `tests/unit/test_avaliacao.py` | Atendido | CT-05 e CT-17 aprovados: comportamento confirmado nos 4 cenários e 100% de cobertura de ramos · `evidencias/CT-17-cobertura-avaliacao.txt` |
| CA-06 | Tentativa extra bloqueada; vale a maior nota | CT-06 | `registrar_tentativa_se_permitida`; `test_avaliacao_fluxo.py` | Atendido | CT-06 aprovado: 3 tentativas (60, 80, 70), 4ª bloqueada, nota final 80% · `evidencias/CT-16-banco-logs-e-hash.txt` |
| CA-07 | PDF com nome, matrícula, curso, carga horária, data e código | CT-07 | `certificado.gerar_pdf`; `test_certificado.py::test_ct07_*` | Atendido | CT-07 aprovado: os 6 campos conferidos no texto extraído do PDF · `evidencias/CT-07-pdf-campos.txt`, `evidencias/CT-07-certificado.pdf` |
| CA-08 | Certificado em até 5 s em 95% de 20 execuções | CT-08 | teste local de 20 emissões (A-04) | Atendido | CT-08 aprovado: 20/20 dentro de 5 s, mediana de 3,3 ms (ressalva A-04: ambiente local) · `evidencias/CT-08-tempo-emissao.txt` |
| CA-09 | Reprovado ou com atividades incompletas não emite | CT-09 | `emitir_certificado` valida no servidor | Atendido | CT-09 aprovado: emissão negada com mensagem, nenhum PDF, `emissao_negada` no log · `evidencias/CT-09-11-12-fluxo-http.txt` |
| CA-10 | 100 emissões sem código repetido | CT-10 | `secrets` + `UNIQUE`; `test_ct10_*` | Atendido | CT-10 aprovado: 100 códigos distintos, sem sequência · `evidencias/execucao-completa-verbose.txt` |
| CA-11 | Código válido: Autêntico; inexistente: não encontrado | CT-11 | `routes/certificados.py::verificar` | Atendido | CT-11 aprovado: 200 Autêntico, 404 não encontrado, 400 campo vazio · `evidencias/CT-09-11-12-fluxo-http.txt` |
| CA-12 | Consulta sem dados pessoais; entradas maliciosas como texto | CT-12 | `mascarar_nome`; `test_verificacao_publica.py` | Atendido | CT-12 aprovado: titular como "Carla M. L.", sem matrícula/CPF/e-mail; 4 entradas maliciosas recusadas com 400 · `evidencias/CT-09-11-12-fluxo-http.txt`. Observação D-01 (código na URL) em `defeitos.md` |
| CA-13 | Arquivar mantém o histórico | CT-13 | `listar_historico`; `test_ct13_*` | Atendido | CT-13 aprovado: curso, nota e certificado seguem no histórico após arquivar · `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt` |
| CA-14 | Páginas em até 3 s | CT-14 | **sem medição formal (Lighthouse)** | Não avaliado: falta Lighthouse (sem navegador no ambiente da execução) | Resposta do servidor entre 1,2 e 2,8 ms nas 6 páginas principais · `evidencias/CT-05-06-07-08-13-02-14-fluxo-http.txt` |
| CA-15 | Só teclado, 360 px e três navegadores | CT-15 | 360 px e axe-core verificados no Chromium; **teclado completo e outros navegadores não** | Atendido em parte | Checagem estática em 8 páginas sem nenhum problema (lang, viewport, título, h1, rótulos, alt, sem tabindex positivo) e CSS só com `max-width`; faltam teclado, 360 px real e Firefox/Edge · `evidencias/CT-15-acessibilidade-estatica.txt` |
| CA-16 | Senhas em hash; logs de login, avaliação e emissão | CT-16 | `services/logs.py`; `test_ct16_*` | Atendido | CT-16 aprovado: scrypt (162 caracteres), nenhuma senha em texto puro no banco, 10 tipos de evento com usuário e data/hora · `evidencias/CT-16-banco-logs-e-hash.txt` |
| CA-17 | Gestor, relatório e aviso de vencimento | CT-18 | **não implementado** | Não avaliado: fora do escopo do protótipo (RF-11 e RF-12) | Plano, item de escopo |

## 2. Atributos de qualidade

| Atributo | O que o protótipo faz (fatos) | O que ainda não foi medido | Avaliação da equipe | Evidência |
|---|---|---|---|---|
| Funcionalidade | Nota, aprovação, certificado e verificação implementados e testados; cobertura de ramos de 100% em `services/avaliacao.py` | Execução independente pela equipe | Atende: 15 de 15 casos executáveis aprovados; 174/174 testes | `evidencias/execucao-pytest-resumo.txt` |
| Confiabilidade | Histórico preservado ao arquivar; emissão única (transação + `UNIQUE`); limite de tentativas atômico | Disponibilidade de 99,5% (SQLite local, sem medição) | Atende no escopo do protótipo: emissões simultâneas geraram 1 certificado e 8 envios simultâneos não passaram do limite de 3 | `evidencias/execucao-completa-verbose.txt` |
| Usabilidade | Interface responsiva (Bootstrap); 360 px sem rolagem lateral; 0 violações no axe-core em 9 páginas (ambiente do autor) | Lighthouse; fluxo inteiro só com teclado; teste com usuários | Atende em parte: 0 problemas na checagem estática de 8 páginas; falta a verificação no navegador | `evidencias/CT-15-acessibilidade-estatica.txt` |
| Eficiência | Teste local de 20 emissões (CT-08); login carregou em cerca de 0,1 s no ambiente do autor | Lighthouse (CT-14); carga de 500 acessos (RNF-01, fora do escopo) | Atende com folga no ambiente local: certificado em 3,3 ms (meta de 5 s) e páginas em até 2,8 ms | `evidencias/CT-08-tempo-emissao.txt` |
| Manutenibilidade | Regras em `config.py`; `services/` sem Flask; ruff e bandit sem avisos; **205 testes** | Métricas formais; os pontos de melhoria estão em `docs/revisao-de-codigo.md` | Atende: ruff "All checks passed", bandit "No issues identified" (1.038 linhas), cobertura de 97% no pacote `app` | `evidencias/estatica-ruff.txt`, `evidencias/estatica-bandit.txt`, `evidencias/CT-17-cobertura-geral.txt` |
| Portabilidade | Verificado no Chromium, Python 3.12, Linux | Firefox, Edge, Windows, Python 3.11, celular real | Atende em parte, com um ganho: a suíte também passou em **Python 3.13.18** (Linux); faltam Windows, Firefox, Edge e celular | `evidencias/ambiente.txt` |
| Segurança | Hash de senha, CSRF, sessão com HttpOnly/SameSite/expiração, perfil e dono verificados no servidor, SQL parametrizado, escape automático, logs sem senha, **bloqueio de força bruta no login (D-02)** e **cabeçalhos de segurança em toda resposta (D-03)** | Teste de invasão por terceiros; HSTS e cookie `Secure` dependem de HTTPS | Atende: bateria OWASP Top 10 com **80 de 83** verificações passando e nenhuma falha de lógica (injeção, IDOR, CSRF, adulteração de nota e SSTI recusados). Os 3 alertas restantes dependem de HTTPS ou do servidor de produção (D-04) | `relatorio-seguranca.md`, `evidencias/SEG-owasp-top10-apos-correcao.txt`, `evidencias/D-03-cabecalhos.txt` |

## 3. Metas do projeto

| Meta | Leitura para o protótipo | Evidência |
|---|---|---|
| M-01: certificado em até 5 s, no lugar de 15 a 30 dias | **Demonstrada** no CT-08: 20/20 emissões dentro de 5 s, mediana de 3,3 ms (ambiente local, ressalva A-04) | `evidencias/CT-08-tempo-emissao.txt` |
| M-02: conformidade nos registros de treinamentos obrigatórios | Mecanismo demonstrado: histórico preservado após arquivar (CT-13), certificado verificável publicamente (CT-11) e 10 tipos de evento registrados (CT-16). A conformidade em si é organizacional e não é medida aqui | `evidencias/CT-16-banco-logs-e-hash.txt` |

## 4. Conclusão (a equipe escreve)

**Execução de 18/11/2026 (Linux, Python 3.13.18, sem navegador gráfico):**

Resumo: **14** de 16 critérios atendidos · **1** em parte (CA-15) · **0** não atendidos ·
**1** não avaliado (CA-14, falta o Lighthouse) · CA-17 fora do escopo.

Principais riscos que permanecem:

1. **CA-14 e CA-15 dependem de navegador:** Lighthouse, navegação só por teclado, 360 px real e
   Firefox/Edge ainda não foram verificados. São os dois itens que faltam para fechar a avaliação.
2. **Portabilidade:** só Linux foi exercitado (Python 3.13 e, segundo o autor, 3.12). Windows e
   Python 3.11 seguem sem confirmação.
3. **Segurança:** o bloqueio de tentativas de login e os cabeçalhos de segurança foram
   implementados e verificados (D-02 e D-03). Permanecem: HSTS e cookie `Secure`, que dependem
   de HTTPS; o cabeçalho `Server`, que depende do servidor de produção (D-04); e o código do
   certificado trafegando na URL (D-01, mitigado por `Referrer-Policy: no-referrer`).
4. **Desempenho em produção:** os números de CT-08 e de resposta das páginas valem para o
   ambiente local com SQLite; os 500 acessos simultâneos (RNF-01) e a disponibilidade de 99,5%
   (RNF-03) continuam fora do escopo.
5. **CI ainda não executado:** o `ci.yml` só roda depois de o projeto estar no GitHub.
