# Proposta de CI/CD

Objetivo: a cada alteração, verificar automaticamente qualidade, segurança e testes, e preparar
a entrega com pouco esforço manual e baixo risco.

## O que já existe (CI)

O arquivo `.github/workflows/ci.yml` roda a cada `push` na `main` e a cada pull request:

| Etapa | Ferramenta | Bloqueia se... |
|---|---|---|
| Análise estática | `ruff check .` | houver erro de estilo ou de código |
| Análise de segurança | `bandit -r app` | houver achado |
| Testes | `pytest --cov=app --cov-branch` | algum teste falhar |
| Meta de cobertura | `coverage report --fail-under=80` (módulo de avaliação) | a cobertura de ramos ficar abaixo de 80% |
| Relatório | `coverage.xml` como artefato | (não bloqueia) |

> O pipeline foi escrito para o GitHub Actions, mas só roda de verdade depois que o repositório
> estiver no GitHub; a equipe deve confirmar a primeira execução.

## Proposta para o restante do ciclo (não implementada)

```
commit → pull request → CI (lint, segurança, testes, cobertura)
       → revisão por outro integrante → merge na main
       → build do pacote → deploy em homologação → testes de aceitação → produção
```

| Prática | Proposta |
|---|---|
| Branch protection | A `main` só aceita merge com CI verde e uma revisão aprovada |
| Revisão | Pull request com checklist de `docs/inspecao.md` |
| Segredos | `SECRET_KEY` e demais valores em *secrets* do repositório, nunca no código |
| Build | Imagem Docker ou pacote com `requirements.txt` fixado |
| Homologação | Implantação automática da `main`, com banco recriado pelo `seed.py` |
| Testes pós-deploy | Teste rápido do fluxo (login, avaliação, certificado) contra a homologação |
| Produção | Implantação manual aprovada, com plano de reversão para a versão anterior |
| Banco | Trocar o SQLite por um banco servidor (ex.: PostgreSQL) com migrações versionadas |
| Desempenho | Teste de carga agendado (ex.: 500 acessos, RNF-01) em ambiente próprio |
| Acessibilidade | Lighthouse no pipeline com nota mínima definida (CA-14, CA-15) |
| Dependências | Verificação periódica de vulnerabilidades (`pip-audit` ou Dependabot) |

## Métricas para acompanhar

Tempo de execução do pipeline · taxa de falha por alteração · cobertura de ramos · número de
defeitos abertos por severidade · tempo entre merge e implantação.

## Riscos e limites

- O SQLite não suporta bem escrita concorrente; adequado ao protótipo, não à produção.
- Hoje o deploy é manual (`flask run` local); a automação acima depende de definir onde o
  sistema será hospedado.
