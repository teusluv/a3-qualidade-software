# Relatório de execução de testes — 18/11/2026

Execução completa dos casos CT-01 a CT-18 do plano, no pacote `A3-entrega-completa`.
Detalhe caso a caso em `execucao-testes.md`; saídas de comando em `evidencias/`.

## 1. Ambiente

| Item | Valor |
|---|---|
| Sistema | Linux x86_64, glibc 2.39 (contêiner) |
| Python | 3.13.18 (o README indica 3.12; os 174 testes passaram também no 3.13) |
| Dependências | conforme `requirements.txt`, sem alteração (`evidencias/ambiente.txt`) |
| Servidor | Flask em `127.0.0.1:5000`, banco recém-semeado por `python seed.py` |
| Navegador | nenhum (sem navegador gráfico): o fluxo de tela foi exercitado por requisições HTTP reais, com CSRF, cookies e sessão |
| Versão do código | pacote entregue, antes do primeiro commit |

## 2. Resultado em uma linha

**205/205 testes automatizados aprovados · ruff e bandit sem avisos · 15 de 15 casos
executáveis aprovados · 2 casos parciais por falta de navegador (CT-14, CT-15) · 1 fora do
escopo (CT-18) · nenhum defeito funcional encontrado · bateria OWASP Top 10 com 80 de 83
verificações aprovadas.**

(A suíte tinha 174 testes na primeira execução; os 31 restantes nasceram das correções de
segurança D-02 e D-03, feitas no mesmo dia.)

## 3. Testes automatizados

| Conjunto | Testes | Resultado |
|---|---|---|
| `tests/unit/` (avaliação, cursos, certificado) | 91 | 91 aprovados |
| `tests/integration/` (banco, certificado, concorrência) | 21 | 21 aprovados |
| `tests/system/` (login, acesso, catálogo, avaliação, admin, verificação, CSRF) | 62 | 62 aprovados |
| `tests/system/test_seguranca.py` (cabeçalhos, força bruta) | 31 | 31 aprovados |
| **Total** | **205** | **205 aprovados** |

Cobertura de ramos: **100%** em `app/services/avaliacao.py` (meta do CT-17: 80%) e **97%** no
pacote `app` (613 comandos, 142 ramos, 14 comandos não cobertos).

Análise estática: `ruff check .` → "All checks passed!"; `bandit -r app` → "No issues
identified", 1.038 linhas, 0 avisos em qualquer severidade.

## 4. Casos de teste

| CT | Resultado | Observação principal |
|---|---|---|
| CT-01 Login | Aprovado | 401 com mensagem genérica; SQL injection não autentica |
| CT-02 Acesso admin | Aprovado | 403 pela URL, com `acesso_negado` no log |
| CT-03 Catálogo | Aprovado | Por setor, obrigatório marcado, suspenso bloqueado |
| CT-04 Progresso | Aprovado | 25% → 50% → 75% → 100% |
| CT-05 Nota | Aprovado | A: 6→60% reprovado, 7→70% aprovado; B: 7 reprova, 8 aprova |
| CT-06 Tentativas | Aprovado | 60, 80, 70 gravadas; 4ª bloqueada; nota final 80% |
| CT-07 PDF | Aprovado | Os 6 campos conferidos no texto extraído do PDF |
| CT-08 Desempenho da emissão | Aprovado | 20/20 em até 5 s; mediana **3,3 ms** (meta: 5 s) |
| CT-09 Emissão negada | Aprovado | Mensagem clara, nenhum PDF, evento no log |
| CT-10 Códigos | Aprovado | 100 códigos distintos, não sequenciais |
| CT-11 Verificação | Aprovado | 200 Autêntico · 404 inexistente · 400 vazio |
| CT-12 Dados pessoais | Aprovado | "Carla M. L."; 4 entradas maliciosas recusadas com 400 |
| CT-13 Arquivamento | Aprovado | Histórico e certificado preservados |
| CT-14 Lighthouse | **Parcial** | Sem navegador. Servidor responde em 1,2 a 2,8 ms |
| CT-15 Acessibilidade | **Parcial** | 0 problemas na checagem estática de 8 páginas; faltam teclado, 360 px real e Firefox/Edge |
| CT-16 Senhas e logs | Aprovado | scrypt; nenhuma senha em texto puro; 10 tipos de evento |
| CT-17 Cobertura | Aprovado | 100% de ramos em `services/avaliacao.py` |
| CT-18 Gestor e vencimento | Não executado | Fora do escopo (RF-11, RF-12) |

## 5. Defeitos

Nenhum defeito funcional nos CT-01 a CT-17. A bateria de segurança (OWASP Top 10, em
`relatorio-seguranca.md`) levantou três itens de configuração, dois já corrigidos e verificados:

| ID | Item | Situação |
|---|---|---|
| D-02 | Login sem proteção contra força bruta | **Verificado**: bloqueia na 6ª tentativa |
| D-03 | Respostas sem cabeçalhos de segurança | **Verificado**: 5 cabeçalhos em toda resposta |
| D-04 | Servidor anuncia a versão | Aberto: é de implantação, não de código |

E uma observação:

- **D-01** — o código do certificado trafega na URL (o formulário da verificação usa GET), então
  fica no histórico do navegador e no log de acesso do servidor. Severidade Baixa, P3; a
  correção seria enviar o formulário por POST. Não afeta nenhum fluxo e não expõe dados
  pessoais: o CT-12 continua aprovado.

## 6. Dois achados que valem para o relatório final

1. **Portabilidade acima do declarado:** a suíte passou inteira em Python 3.13.18, e o README
   só declarava Python 3.12.
2. **A meta M-01 tem folga grande:** a meta é 5 s e a emissão leva 3,3 ms na mediana — cerca de
   1.500 vezes mais rápido que o limite, no ambiente local (ressalva A-04).

## 7. O que falta e quem faz

| # | Pendência | Por que não foi feito aqui |
|---|---|---|
| 1 | Lighthouse nas páginas principais (CT-14) | Exige navegador |
| 2 | Fluxo só com teclado, 360 px real e Chrome/Firefox/Edge (CT-15) | Exige navegador |
| 3 | Confirmar Windows e Python 3.11/3.12 | Ambiente da execução é Linux |
| 4 | Primeira execução verde do CI na aba Actions | Exige o projeto no GitHub |
| 5 | Checklist de inspeção e os 19 pontos de `revisao-de-codigo.md` | Dependem de leitura do código pelos inspetores |
| 6 | Preencher nomes, data e commit nos cabeçalhos dos documentos | Dados da equipe |
