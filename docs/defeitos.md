# Registro de defeitos

Registre **somente defeitos reais**, encontrados na execução dos testes, na inspeção ou na
análise estática. Cada defeito precisa de evidência (print, saída de comando, trecho de código).

## Escalas

**Severidade** (impacto): Crítica (compromete segurança, dados ou o fluxo principal) · Alta
(funcionalidade importante falha) · Média (falha com alternativa) · Baixa (cosmético ou texto).

**Prioridade** (urgência de correção): P1 (corrigir antes da entrega) · P2 · P3.

**Situação:** Aberto · Corrigido · Verificado (reteste e regressão ok) · Rejeitado (não é defeito).

## Registro

| ID | Título | Onde | Origem (teste, inspeção, estática) | Passos para reproduzir | Esperado × Obtido | Severidade | Prioridade | Evidência | Situação | Correção (commit) | Regressão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D-01 | | | | | | | | | | | |

## Regras

- Um defeito por linha; IDs sequenciais (D-01, D-02...).
- Ao corrigir, anote o commit e reexecute o caso que o encontrou **e** os de prioridade alta.
- Defeito rejeitado continua na tabela, com o motivo.
