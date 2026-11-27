# Registro de execução de testes

Preencha uma linha por execução. **Nada aqui foi pré-preenchido com resultado:** os campos
"obtido", "status" e "evidência" devem vir da execução real da equipe.

Campos obrigatórios (CA-16 / rastreabilidade): ID do caso, resultado esperado,
resultado obtido, status e evidência.

**Status permitidos:** Aprovado · Reprovado · Bloqueado · Não executado (com o motivo).

**Ambiente (preencher uma vez):** sistema operacional ____ · Python ____ · navegador ____ ·
data ____ · versão do código (commit) ____.

## Execução 1 (primeira entrega, 25/11/2026)

| ID | Tipo | Resultado esperado | Resultado obtido | Status | Evidência |
|---|---|---|---|---|---|
| CT-01 | Sistema | Válidas: acesso liberado. Inválidas: negado, com mensagem genérica. | | | |
| CT-02 | Sistema | Colaborador na URL de administração: acesso negado. | | | |
| CT-05 | Unidade e sistema | A: 7 = 70% Aprovado; 6 = 60% Reprovado. B: 7 Reprovado; 8 Aprovado. | | | |
| CT-06 | Sistema | Tentativa extra bloqueada; nota final 80% (notas 60, 80, 70). | | | |
| CT-07 | Integração | PDF com todos os campos preenchidos. | | | |
| CT-08 | Desempenho | Pelo menos 19 de 20 emissões em até 5 s. | | | |
| CT-09 | Integração | Emissão negada para reprovado e para atividades incompletas; nenhum PDF. | | | |
| CT-10 | Integração | 100 códigos distintos. | | | |
| CT-11 | Sistema | Autêntico; Certificado não encontrado; validação do campo vazio. | | | |
| CT-12 | Segurança | Sem matrícula, CPF, e-mail ou senha; nome mascarado; entradas tratadas como texto. | | | |
| CT-16 | Caixa-branca | Senhas em hash; um log por evento. | | | |
| CT-17 | Unidade | Cobertura de decisão ≥ 80% em `services/avaliacao.py`; testes passam. | | | |

## Execução 2 (entrega final, 02/12/2026), incluindo regressão

| ID | Tipo | Resultado esperado | Resultado obtido | Status | Evidência |
|---|---|---|---|---|---|
| CT-03 | Sistema | Só cursos aplicáveis; obrigatórios identificados; início do suspenso bloqueado. | | | |
| CT-04 | Sistema | Progresso de 50% com 2 de 4 atividades. | | | |
| CT-13 | Integração | Conclusões continuam visíveis após arquivar o curso. | | | |
| CT-14 | Desempenho | Páginas principais em até 3 s (Lighthouse). | | | |
| CT-15 | Acessibilidade | Fluxo só com teclado, em 360 px e em três navegadores. | | | |
| CT-18 | Sistema | **Não executado:** RF-11 e RF-12 estão fora do escopo do protótipo. | Não se aplica | Não executado | Plano, item de escopo |
| Regressão | Todos | Reexecutar os casos de prioridade alta e os afetados por correções. | | | |

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
