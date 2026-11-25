# Avaliação dos critérios de aceitação e dos atributos de qualidade

Item da **entrega final (02/12/2026)**: "avaliação de critérios de aceitação e atributos".

**Como usar:** a coluna "Base técnica" diz o que já existe no código e nos testes (fatos).
As colunas **Situação** e **Evidência** são da equipe e só devem ser preenchidas depois de
executar o caso correspondente (`docs/execucao-testes.md`).

**Situação permitida:** Atendido · Atendido em parte · Não atendido · Não avaliado (com o motivo).

## 1. Critérios de aceitação (CA-01 a CA-17)

| CA | Critério (resumo) | Casos | Base técnica (o que existe) | Situação | Evidência |
|---|---|---|---|---|---|
| CA-01 | Login válido libera; inválido ou vazio nega, sem dizer qual campo errou | CT-01 | `auth.py`; `tests/system/test_login.py` | | |
| CA-02 | Colaborador não acessa a administração, nem pela URL | CT-02 | `perfil_required`; `tests/system/test_acesso.py` | | |
| CA-03 | Catálogo por setor, obrigatórios marcados; suspenso/fora do período não inicia | CT-03 | `routes/cursos.py`; `test_catalogo_e_progresso.py` | | |
| CA-04 | Progresso correto (2 de 4 = 50%) | CT-04 | `avaliacao.progresso_percentual`; testes de progresso | | |
| CA-05 | Curso A: 7 aprova, 6 reprova. Curso B: 7 reprova, 8 aprova | CT-05, CT-17 | `services/avaliacao.py`; `tests/unit/test_avaliacao.py` | | |
| CA-06 | Tentativa extra bloqueada; vale a maior nota | CT-06 | `registrar_tentativa_se_permitida`; `test_avaliacao_fluxo.py` | | |
| CA-07 | PDF com nome, matrícula, curso, carga horária, data e código | CT-07 | `certificado.gerar_pdf`; `test_certificado.py::test_ct07_*` | | |
| CA-08 | Certificado em até 5 s em 95% de 20 execuções | CT-08 | teste local de 20 emissões (A-04) | | |
| CA-09 | Reprovado ou com atividades incompletas não emite | CT-09 | `emitir_certificado` valida no servidor | | |
| CA-10 | 100 emissões sem código repetido | CT-10 | `secrets` + `UNIQUE`; `test_ct10_*` | | |
| CA-11 | Código válido: Autêntico; inexistente: não encontrado | CT-11 | `routes/certificados.py::verificar` | | |
| CA-12 | Consulta sem dados pessoais; entradas maliciosas como texto | CT-12 | `mascarar_nome`; `test_verificacao_publica.py` | | |
| CA-13 | Arquivar mantém o histórico | CT-13 | `listar_historico`; `test_ct13_*` | | |
| CA-14 | Páginas em até 3 s | CT-14 | **sem medição formal (Lighthouse)** | | |
| CA-15 | Só teclado, 360 px e três navegadores | CT-15 | 360 px e axe-core verificados no Chromium; **teclado completo e outros navegadores não** | | |
| CA-16 | Senhas em hash; logs de login, avaliação e emissão | CT-16 | `services/logs.py`; `test_ct16_*` | | |
| CA-17 | Gestor, relatório e aviso de vencimento | CT-18 | **não implementado** | Não avaliado: fora do escopo do protótipo (RF-11 e RF-12) | Plano, item de escopo |

## 2. Atributos de qualidade

| Atributo | O que o protótipo faz (fatos) | O que ainda não foi medido | Avaliação da equipe | Evidência |
|---|---|---|---|---|
| Funcionalidade | Nota, aprovação, certificado e verificação implementados e testados; cobertura de ramos de 100% em `services/avaliacao.py` | Execução independente pela equipe | | |
| Confiabilidade | Histórico preservado ao arquivar; emissão única (transação + `UNIQUE`); limite de tentativas atômico | Disponibilidade de 99,5% (SQLite local, sem medição) | | |
| Usabilidade | Interface responsiva (Bootstrap); 360 px sem rolagem lateral; 0 violações no axe-core em 10 páginas, botões de voltar nas telas (ambiente do autor) | Lighthouse; fluxo inteiro só com teclado; teste com usuários | | |
| Eficiência | Teste local de 20 emissões (CT-08); login carregou em cerca de 0,1 s no ambiente do autor | Lighthouse (CT-14); carga de 500 acessos (RNF-01, fora do escopo) | | |
| Manutenibilidade | Regras em `config.py`; `services/` sem Flask; ruff e bandit sem avisos; 260 testes | Métricas formais; os pontos de melhoria estão em `docs/revisao-de-codigo.md` | | |
| Portabilidade | Verificado no Chromium, Python 3.12, Linux | Firefox, Edge, Windows, Python 3.11, celular real | | |
| Segurança | Hash de senha, CSRF, sessão com HttpOnly/SameSite/expiração, perfil e dono verificados no servidor, SQL parametrizado, escape automático, logs sem senha, `pip-audit` sem vulnerabilidades | Bloqueio de força bruta, cabeçalhos de segurança e teste de invasão (ver revisão do código) | | |

## 3. Metas do projeto

| Meta | Leitura para o protótipo | Evidência |
|---|---|---|
| M-01: certificado em até 5 s, no lugar de 15 a 30 dias | Demonstrável pelo CT-08 (ambiente local) | |
| M-02: conformidade nos registros de treinamentos obrigatórios | O protótipo mostra o mecanismo (histórico + certificado verificável); a conformidade em si é organizacional e não é medida aqui | |

## 4. Conclusão (a equipe escreve)

Resumo: ___ de 16 critérios atendidos · ___ em parte · ___ não atendidos · CA-17 fora do escopo.
Principais riscos que permanecem: ____.
