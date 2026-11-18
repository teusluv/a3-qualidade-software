# Relatório de revisão e inspeção

Inspeção do código por pessoas diferentes de quem o escreveu. Marque cada item após conferir
**no código**, anote o local e registre os achados na tabela e em `docs/defeitos.md`.

**Inspetores:** ____ · **Data:** ____ · **Versão (commit):** ____

## 1. Checklist

### Regras de negócio
- [ ] Aprovação usa `>=` e o mínimo do curso nunca fica abaixo de 70% (`services/avaliacao.py`)
- [ ] A nota é truncada, não arredondada para cima
- [ ] O limite de tentativas é verificado no servidor, também no envio (`routes/cursos.py`)
- [ ] O certificado só é emitido com atividades concluídas e nota suficiente (`services/certificado.py`)
- [ ] A emissão é única por colaborador e curso (`UNIQUE` e transação)
- [ ] Curso suspenso, arquivado ou fora do período bloqueia só novos inícios (A-08)

### Segurança
- [ ] Todas as consultas SQL usam parâmetros, sem concatenar entrada do usuário
- [ ] Senhas só aparecem como hash (`seed_data.py`, `auth.py`)
- [ ] Toda rota restrita usa `login_required` ou `perfil_required`
- [ ] O colaborador só baixa o próprio certificado
- [ ] A consulta pública devolve só o mínimo e valida o formato do código
- [ ] Os formulários que alteram dados têm token CSRF
- [ ] Nenhum segredo fixo no código; `SECRET_KEY` vem do ambiente
- [ ] Os logs não guardam senha nem o que foi digitado no login

### Qualidade do código
- [ ] Funções pequenas, com uma responsabilidade e nomes claros
- [ ] Regras de negócio fora das rotas (`services/`)
- [ ] Sem código duplicado ou morto
- [ ] Constantes de negócio em `config.py`
- [ ] Mensagens de erro claras e sem detalhes internos

### Testes
- [ ] Cada regra de negócio tem teste nos valores limite
- [ ] Os testes não usam o banco real (`conftest.py`)
- [ ] Os casos CT-01 a CT-17 têm teste ou execução manual prevista

## 2. Achados da inspeção

Preencha com o que for encontrado de fato. Um achado vira defeito em `docs/defeitos.md`
quando confirmado.

| # | Local (arquivo:linha) | Evidência | Severidade | Recomendação | Defeito? |
|---|---|---|---|---|---|
| 1 | | | | | |

## 3. Análise estática

Cole aqui a saída real de `ruff check .` e `bandit -r app` e classifique cada aviso.

**Saída real da execução de 18/11/2026 (Linux, Python 3.13.18):**

```
$ ruff check .
All checks passed!                                  (código de saída 0)

$ bandit -r app
Test results:
        No issues identified.
Code scanned:
        Total lines of code: 960
Total issues (by severity):
        Undefined: 0   Low: 0   Medium: 0   High: 0
```

| Ferramenta | Aviso | Local | Classificação (defeito, falso positivo, aceito) | Justificativa |
|---|---|---|---|---|
| ruff 0.17.5 | nenhum aviso | — | — | Nada a classificar: 0 ocorrências nas verificações configuradas em `ruff.toml` |
| bandit 1.9.4 | nenhum aviso | — | — | Nada a classificar: 0 ocorrências de severidade baixa, média ou alta em 960 linhas de `app/` |

Evidências: `evidencias/estatica-ruff.txt` e `evidencias/estatica-bandit.txt`.

> A ausência de avisos **não** encerra a inspeção: ruff e bandit não avaliam regra de negócio.
> Os 19 pontos de `revisao-de-codigo.md` e o checklist da seção 1 continuam a cargo dos
> inspetores, que precisam ler o código.

## 4. Limitações conhecidas (declaradas pelo autor do código)

São pontos que a equipe já sabe que existem. Servem de roteiro para a inspeção e **não** são
defeitos descobertos por ela; a equipe decide o que classificar como defeito.

- Sem limite de tentativas de login nem bloqueio de conta (risco de força bruta).
- Sem limitação de requisições na consulta pública; a proteção contra adivinhação do código
  vem da sua entropia (`secrets.token_urlsafe(16)`).
- Sem recuperação ou troca de senha; os usuários vêm do `seed.py` (RH simulado).
- O cookie `Secure` fica desligado no protótipo local em HTTP (ligar com `SESSION_COOKIE_SECURE=1`
  em HTTPS).
- A tabela `log` cresce sem limite e sem rotação.
- As "atividades" apenas são marcadas como concluídas; não há conteúdo real (vídeo, PDF).
- O PDF não tem QR code (opcional na hipótese A-03) e a assinatura é ilustrativa.
- O Bootstrap vem de CDN; sem internet a página perde o estilo (o hash de integridade protege
  contra alteração do arquivo).
- A medição dos 5 s do certificado vale para o ambiente local (A-04); o SQLite não valida os
  500 acessos simultâneos (RNF-01 está fora do escopo).
- "Hoje" usa o relógio do servidor, sem tratamento de fuso horário.
- Os testes automatizados desligam o CSRF; ele é verificado por dois testes dedicados.
